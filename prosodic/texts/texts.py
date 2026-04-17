from ..imports import *
from ..words import WordTokenList, WordToken
from .syll_df import build_syll_df
from .phrasal_stress import add_phrasal_stress

NUMBUILT = 0
PARSED_CACHE_DIR = os.path.join(PATH_HOME_DATA, "parsed")


def _meter_to_dict(meter):
    """Serialize a Meter's configuration (constraints, weights, zones) to JSON-safe dict."""
    if meter is None:
        return None
    d = {
        "constraints": {k: float(v) for k, v in dict(meter.constraints).items()},
        "max_s": int(meter.max_s),
        "max_w": int(meter.max_w),
        "resolve_optionality": bool(meter.resolve_optionality),
        "parse_unit": meter.parse_unit,
    }
    zones = getattr(meter, 'zones', None)
    if zones is not None:
        d["zones"] = zones if isinstance(zones, (str, int)) else str(zones)
    zone_weights = getattr(meter, 'zone_weights', None)
    if zone_weights is not None:
        d["zone_weights"] = {k: float(v) for k, v in dict(zone_weights).items()}
    return d


class TextModel(Entity):
    """
    A class that represents a text structure, comprised of WordTokens.
    """

    is_text = True
    prefix = "text"

    def __init__(
        self,
        children: Optional[list] = [],
        txt: str = None,
        fn: str = None,
        lang: Optional[str] = DEFAULT_LANG,
        parent: Optional[Entity] = None,
        tokens_df: Optional[pd.DataFrame] = None,
        syntax: Optional[bool] = None,
        syntax_model: Optional[str] = None,
        **kwargs,
    ):
        if isinstance(children, str):
            txt = children
            children = []

        if not txt and not fn and not children and tokens_df is None:
            raise ValueError(
                "must provide either txt string or filename or token dataframe"
            )
        txt = clean_text(get_txt(txt, fn)).strip()
        lang = lang if lang else detect_lang(txt)

        # syntax options
        self._syntax = syntax if syntax is not None else DEFAULT_SYNTAX
        self._syntax_model = syntax_model or DEFAULT_SYNTAX_MODEL

        # store for lazy construction
        self._token_dicts = None
        self._syll_df = None
        self._children_built = bool(children)

        # init entity (sets self.children via property setter below)
        super().__init__(
            children=children,
            txt=txt,
            lang=lang,
            **kwargs,
        )
        self._parse_results = {}
        self._line_parse_results = {}

        if not self._children_built:
            if tokens_df is None:
                token_dicts = list(tokenize_sentwords_iter(txt))
            else:
                token_dicts = [row.to_dict() for _, row in tokens_df.iterrows()]

            self._token_dicts = token_dicts

            # build syllable DataFrame from raw get_word() output (fast)
            self._syll_df = build_syll_df(token_dicts, lang=lang)

            # optionally add phrasal stress from dependency parse
            if self._syntax:
                add_phrasal_stress(self._syll_df, model=self._syntax_model)

            # DON'T build Entity children yet — defer to first access

    def _build_children(self):
        """Lazily construct WordToken Entity objects from stored token dicts."""
        if self._children_built:
            return
        if self._token_dicts is None and self._syll_df is not None:
            # loaded from parquet — reconstruct token dicts from syll_df
            self._token_dicts = self._token_dicts_from_syll_df()
        if self._token_dicts is None:
            return
        self._children_built = True
        for d in progress_bar(
            self._token_dicts,
            progress=len(self._token_dicts) >= 1000,
            desc="Building long text",
        ):
            self._children_data.append(WordToken(lang=self.lang, **d))

    def _token_dicts_from_syll_df(self):
        """Reconstruct token dicts from _syll_df (for loaded texts)."""
        df = self._syll_df
        # one dict per unique word_num, using form_idx=0
        seen = set()
        dicts = []
        for _, row in df[df['form_idx'].isin([0, -1])].drop_duplicates('word_num').iterrows():
            dicts.append({
                'txt': row['word_txt'],
                'num': int(row['word_num']),
                'line_num': int(row['line_num']),
                'para_num': int(row['para_num']),
                'sent_num': int(row['sent_num']),
                'sentpart_num': int(row['sentpart_num']),
                'linepart_num': int(row['linepart_num']),
                'is_punc': int(row['is_punc']),
            })
        return dicts

    # property to intercept children access for lazy building
    @property
    def children(self):
        if not self._children_built and (self._token_dicts is not None or self._syll_df is not None):
            self._build_children()
        return self._children_data

    @children.setter
    def children(self, value):
        self._children_data = value
        if value and len(value) > 0:
            self._children_built = True

    @cached_property
    def stanzas(self):
        from ..texts.stanzas import StanzaList

        return StanzaList.from_wordtokens(self.children, text=self)

    @cached_property
    def lines(self):
        from ..texts.lines import LineList

        lines = LineList.from_wordtokens(self.children, text=self)

        # attach any DF-based parse results to the line entities
        if self._line_parse_results:
            for meter_key, line_results in self._line_parse_results.items():
                for line in lines:
                    line_num = line.num
                    if line_num in line_results:
                        pl = line_results[line_num]
                        # set parent to the line's WordTokenList
                        wt_list = line.children
                        if hasattr(wt_list, '_parses'):
                            pl.parent = wt_list
                            wt_list._parses = pl
                        line._parses = pl

        return lines

    @cached_property
    def lineparts(self):
        from ..texts.lines import LinePartList

        return LinePartList.from_wordtokens(self.children, text=self)

    @cached_property
    def sents(self):
        from ..sents.sents import SentenceList

        return SentenceList.from_wordtokens(self.children, text=self)

    @cached_property
    def sentparts(self):
        from ..sents.sents import SentPartList

        return SentPartList.from_wordtokens(self.children, text=self)

    @property
    def wordtokens(self):
        return self.children

    def to_hash(self) -> str:
        return hashstr(self._txt)

    @property
    def hash(self):
        pkg={"txt": self._txt, "lang": self.lang}
        return encode_hash(serialize(pkg))

    @property
    def key(self):
        if self._key is None:
            self._key = f"{self.nice_type_name}({self.hash})"
        return self._key

    def cleanup(self):
        self._parse_results.clear()
        self._parses = None
        for obj in self.iter_all():
            obj.clear_cached_properties()

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.children[item]
        return super().__getitem__(item)


    @cache
    def parse(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
        lim=None,
        force=False,
        meter=None,
        num_proc=None,  # deprecated, ignored
        **meter_kwargs,
    ):
        from ..parsing.parselists import ParseListList

        if combine_by != self.prefix:
            self._parses = ParseListList(parent=self)
        for i,pl in enumerate(self.parse_iter(
            combine_by=combine_by,
            force=force,
            meter=meter,
            lim=lim,
            **meter_kwargs,
        )):
            if combine_by == self.prefix:
                return pl
            else:
                pl._num = i+1
                self._parses.append(pl)
        return self._parses

    def parse_iter(
        self,
        combine_by: Literal["line", "sent"] = DEFAULT_COMBINE_BY,
        lim=None,
        force=False,
        meter=None,
        **meter_kwargs,
    ):
        from ..parsing.parselists import ParseList

        meter = self.get_meter(meter=meter, **meter_kwargs)
        if combine_by and meter.parse_unit == combine_by:
            combine_by = None

        parse_key = (meter.key, combine_by)
        if parse_key in self._parse_results:
            yield from self._parse_results[parse_key]
        else:
            self._parse_results[parse_key] = []
            last_unit = None
            units = []
            for parse_list in meter.parse_text_iter(
                self, force=force, lim=lim
            ):
                # DF-only path: parse_list.parent may be None
                if parse_list.parent is not None:
                    parsed_ent = parse_list.parent
                    parsed_ent._parses = parse_list
                else:
                    # DF path: results stored in _line_parse_results,
                    # will be attached to entities when lines are accessed
                    parsed_ent = None

                if not combine_by:
                    self._parse_results[parse_key].append(parse_list)
                    yield parse_list
                elif parsed_ent is not None:
                    this_unit = getattr(parsed_ent, combine_by)
                    if units and last_unit is not this_unit:
                        new_parselist = ParseList.from_combinations(units, parent=last_unit)
                        last_unit._parses = new_parselist
                        self._parse_results[parse_key].append(new_parselist)
                        yield new_parselist
                        units = []
                    units.append(parse_list)
                    last_unit = this_unit
                else:
                    # DF path without combine: just collect
                    self._parse_results[parse_key].append(parse_list)
                    yield parse_list

            if units:
                new_parselist = ParseList.from_combinations(units, parent=last_unit)
                last_unit._parses = new_parselist
                self._parse_results[parse_key].append(new_parselist)
                yield new_parselist

    @property
    def parses(self) -> Any:
        if not self._parses:
            self.parse()
        return self._parses

    @property
    def df(self):
        """The syllable DataFrame — no entity construction needed."""
        return self._syll_df

    @cached_property
    def parsed_df(self):
        """Parse with default meter and return results as a DataFrame.

        One row per (line, unbounded parse, syllable). Joins to _syll_df on
        (line_num, word_num, form_idx, syll_idx). No entity construction.
        """
        if getattr(self, '_cached_parsed_df', None) is not None:
            return self._cached_parsed_df
        return self.get_parses_df()

    def get_parsed_df(self, mode='unbounded', **meter_kwargs):
        """Alias for get_parses_df(mode=..., **meter_kwargs)."""
        return self.get_parses_df(mode=mode, **meter_kwargs)

    def get_parses_df(self, mode='unbounded', **meter_kwargs):
        """Parse and return results as a DataFrame. No entity construction.

        Args:
            mode: 'best', 'unbounded' (default), or 'all'.
            **meter_kwargs: custom meter config (max_s, max_w, etc.)

        Returns a DataFrame with one row per (line, parse, syllable). Columns:
            line_num, word_num, form_idx, syll_idx (within-word, joins to _syll_df),
            line_syll_idx (position within line), parse_idx, parse_rank (1-indexed
            among unbounded, NA for bounded), parse_score, is_best, is_bounded,
            pos_idx, pos_size, meter_val, syll_txt, syll_ipa, is_stressed,
            plus one `*<constraint>` column per violation (int8).

        Implementation is vectorized: per-line chunks are built directly
        from the numpy (S, N, C) violation arrays without row-by-row Python loops.
        """
        if mode not in ('best', 'unbounded', 'all'):
            raise ValueError(f"mode must be 'best', 'unbounded', or 'all'; got {mode!r}")

        self.parse(**meter_kwargs)
        if not self._line_parse_results:
            return pd.DataFrame()

        sdf = self._syll_df
        all_word_nums = sdf['word_num'].values
        all_form_idxs = sdf['form_idx'].values
        all_syll_idxs = sdf['syll_idx'].values

        chunks = []
        constraint_names = None

        # use only the most recent meter's results — mixing constraint sets
        # across meters would break the shared violation columns
        latest_key = next(reversed(self._line_parse_results))
        line_results = self._line_parse_results[latest_key]
        for line_num in sorted(line_results.keys()):
            pl = line_results[line_num]
            sylls = getattr(pl, '_sylls', None)
            viols = getattr(pl, '_all_viols', None)
            if not sylls or viols is None:
                continue
            N = len(sylls)
            if N == 0:
                continue

            unbounded_mask = pl._unbounded_mask
            all_scores = pl._all_scores
            unb_idx = pl._unbounded_indices

            if len(unb_idx) == 0 and mode != 'all':
                continue

            # rank among unbounded (1-indexed, -1 sentinel for bounded)
            S_total = len(unbounded_mask)
            rank_of = np.full(S_total, -1, dtype=np.int32)
            if len(unb_idx) > 0:
                ub_sorted = unb_idx[np.argsort(pl._scores)]
                rank_of[ub_sorted] = np.arange(1, len(ub_sorted) + 1, dtype=np.int32)
                best_idx = int(ub_sorted[0])
            else:
                best_idx = -1

            if mode == 'best':
                parse_indices = np.array([best_idx], dtype=np.int64) if best_idx >= 0 else np.empty(0, dtype=np.int64)
            elif mode == 'unbounded':
                parse_indices = unb_idx[np.argsort(pl._scores)]
            else:
                parse_indices = np.argsort(all_scores)

            P = len(parse_indices)
            if P == 0:
                continue

            if constraint_names is None:
                constraint_names = list(pl._constraint_names)

            # Scansion-derived features: (S, N) arrays.
            # meter_val is 's'/'w' from meter_vals bool; fall back to scansion list.
            mv_arr = getattr(pl, '_meter_vals', None)
            pi_arr = getattr(pl, '_position_ids', None)
            ps_arr = getattr(pl, '_position_sizes', None)
            if mv_arr is None or pi_arr is None or ps_arr is None:
                from ..parsing.vectorized import encode_scansions
                mv_arr, pi_arr, ps_arr = encode_scansions(pl._all_scansions, N)

            sel_mv = mv_arr[parse_indices]       # (P, N) bool
            sel_pi = pi_arr[parse_indices]       # (P, N) int
            sel_ps = ps_arr[parse_indices]       # (P, N) int

            PN = P * N

            # Parse-level columns broadcast over N syllables
            parse_idx_col = np.repeat(parse_indices.astype(np.int32), N)
            parse_score_col = np.repeat(all_scores[parse_indices].astype(np.float64), N)
            is_bounded_col = np.repeat(~unbounded_mask[parse_indices], N)
            is_best_col = np.repeat(parse_indices == best_idx, N)
            parse_rank_col = np.repeat(rank_of[parse_indices], N)
            line_num_col = np.full(PN, int(line_num), dtype=np.int32)

            # Syll-level columns tiled across P parses
            line_syll_idx_col = np.tile(np.arange(N, dtype=np.int32), P)
            row_idx = getattr(pl, '_syll_row_idx', None)
            if row_idx is not None:
                r_arr = np.asarray(row_idx)
                word_num_col = np.tile(all_word_nums[r_arr].astype(np.int32), P)
                form_idx_col = np.tile(all_form_idxs[r_arr].astype(np.int32), P)
                syll_idx_col = np.tile(all_syll_idxs[r_arr].astype(np.int32), P)
            else:
                word_num_col = np.full(PN, -1, dtype=np.int32)
                form_idx_col = np.zeros(PN, dtype=np.int32)
                syll_idx_col = np.tile(np.arange(N, dtype=np.int32), P)

            syll_txt_arr = np.array(
                [getattr(s, 'txt', '') or '' for s in sylls], dtype=object,
            )
            syll_ipa_arr = np.array(
                [getattr(s, 'ipa', '') or '' for s in sylls], dtype=object,
            )
            is_stressed_arr = np.array(
                [bool(s.is_stressed) for s in sylls], dtype=bool,
            )
            syll_txt_col = np.tile(syll_txt_arr, P)
            syll_ipa_col = np.tile(syll_ipa_arr, P)
            is_stressed_col = np.tile(is_stressed_arr, P)

            # Flatten (P, N) -> (P*N,)
            meter_val_col = np.where(sel_mv.ravel(), 's', 'w')
            pos_idx_col = sel_pi.ravel().astype(np.int32)
            pos_size_col = sel_ps.ravel().astype(np.int32)

            # Violations: viols[parse_indices] -> (P, N, C) -> (P*N, C)
            sel_viols = viols[parse_indices].reshape(PN, -1).astype(np.int8)

            chunks.append({
                'line_num': line_num_col,
                'word_num': word_num_col,
                'form_idx': form_idx_col,
                'syll_idx': syll_idx_col,
                'line_syll_idx': line_syll_idx_col,
                'parse_idx': parse_idx_col,
                'parse_rank': parse_rank_col,
                'parse_score': parse_score_col,
                'is_best': is_best_col,
                'is_bounded': is_bounded_col,
                'pos_idx': pos_idx_col,
                'pos_size': pos_size_col,
                'meter_val': meter_val_col,
                'syll_txt': syll_txt_col,
                'syll_ipa': syll_ipa_col,
                'is_stressed': is_stressed_col,
                '_viols': sel_viols,
                '_c_names': pl._constraint_names,
            })

        if not chunks:
            return pd.DataFrame()

        # Concatenate all chunks into DataFrame
        base_cols = [
            'line_num', 'word_num', 'form_idx', 'syll_idx', 'line_syll_idx',
            'parse_idx', 'parse_rank', 'parse_score', 'is_best', 'is_bounded',
            'pos_idx', 'pos_size', 'meter_val', 'syll_txt', 'syll_ipa', 'is_stressed',
        ]
        data = {k: np.concatenate([c[k] for c in chunks]) for k in base_cols}
        df = pd.DataFrame(data)
        df['parse_rank'] = pd.array(df['parse_rank'].values, dtype='Int32')
        df.loc[df['parse_rank'] < 0, 'parse_rank'] = pd.NA

        # Violation columns (only emit those with any non-zero value)
        viols_all = np.concatenate([c['_viols'] for c in chunks], axis=0)
        c_names = chunks[0]['_c_names']
        for ci, cname in enumerate(c_names):
            col = viols_all[:, ci]
            if col.any():
                df[f'*{cname}'] = col

        return df

    def save(self, path=None, save_parses='unbounded', compression='gzip',
             **meter_kwargs):
        """Save text + syllable DF + parse results to parquet files.

        Writes syll.parquet (full _syll_df), parsed.parquet (parse results
        per mode), meta.json. parsed.parquet joins to syll.parquet on
        (line_num, word_num, form_idx, syll_idx).

        Args:
            path: directory to save into. Defaults to
                ~/prosodic_data/data/parsed/<hash>/.
            save_parses: 'best', 'unbounded' (default), or 'all'.
            compression: parquet codec (default 'gzip'). Pass None for uncompressed.
            **meter_kwargs: passed to parse() if not already parsed.

        Returns:
            str: path to the saved directory.
        """
        if path is None:
            path = os.path.join(PARSED_CACHE_DIR, self.hash)
        os.makedirs(path, exist_ok=True)

        self._syll_df.to_parquet(
            os.path.join(path, "syll.parquet"), compression=compression,
        )

        pdf = self.get_parses_df(mode=save_parses, **meter_kwargs)
        if len(pdf) > 0:
            pdf.to_parquet(
                os.path.join(path, "parsed.parquet"), compression=compression,
            )

        # Write source text to its own file (gzipped if compression is 'gzip')
        gzip_text = compression == 'gzip'
        txt_bytes = self._txt.encode('utf-8')
        if gzip_text:
            import gzip
            with gzip.open(os.path.join(path, "text.txt.gz"), "wb") as f:
                f.write(txt_bytes)
            text_file = "text.txt.gz"
        else:
            with open(os.path.join(path, "text.txt"), "wb") as f:
                f.write(txt_bytes)
            text_file = "text.txt"

        import json
        from datetime import datetime, timezone
        _prosodic_version = None
        try:
            _vpath = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', '_version.py')
            _vpath = os.path.normpath(_vpath)
            if os.path.exists(_vpath):
                _ns = {}
                with open(_vpath) as _vf:
                    exec(_vf.read(), _ns)
                _prosodic_version = _ns.get('__version__')
            if _prosodic_version is None:
                import importlib.metadata as _im
                _prosodic_version = _im.version('prosodic')
        except Exception:
            pass

        meta = {
            "prosodic_version": _prosodic_version,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "text_file": text_file,
            "lang": self.lang,
            "num_lines": int(self._syll_df['line_num'].max()),
            "save_parses": save_parses,
            "compression": compression,
            "meter": _meter_to_dict(getattr(self, '_mtr', None)),
        }
        with open(os.path.join(path, "meta.json"), "w") as f:
            json.dump(meta, f, indent=2, default=str)

        return path

    @classmethod
    def load(cls, path):
        """Load a saved TextModel from parquet files.

        Rebuilds TextModel with pre-computed _syll_df, skipping tokenization
        and get_word() entirely. If parse results exist, they're available
        via .parsed_df immediately.

        Args:
            path: directory containing syll.parquet and meta.json

        Returns:
            TextModel with _syll_df pre-loaded (entities still lazy)
        """
        import json
        syll_path = os.path.join(path, "syll.parquet")
        meta_path = os.path.join(path, "meta.json")
        parsed_path = os.path.join(path, "parsed.parquet")

        with open(meta_path) as f:
            meta = json.load(f)

        syll_df = pd.read_parquet(syll_path)

        # source text: from text_file reference, or inline 'txt' (legacy)
        txt = meta.get('txt', '')
        text_file = meta.get('text_file')
        if text_file:
            tpath = os.path.join(path, text_file)
            if text_file.endswith('.gz'):
                import gzip
                with gzip.open(tpath, 'rb') as f:
                    txt = f.read().decode('utf-8')
            else:
                with open(tpath, 'rb') as f:
                    txt = f.read().decode('utf-8')

        # build TextModel without re-tokenizing or calling get_word
        obj = cls.__new__(cls)
        obj._token_dicts = None
        obj._syll_df = syll_df
        obj._children_built = False
        obj._children_data = obj.children_type(parent=obj) if obj.children_type is not None else []
        obj._parse_results = {}
        obj._line_parse_results = {}
        obj._parses = None
        obj._attrs = {'lang': meta.get('lang', DEFAULT_LANG)}
        obj._num = None
        obj._mtr = None
        obj.parent = None
        obj._text = None
        obj._key = None
        obj._txt = txt
        obj.lang = meta.get('lang', DEFAULT_LANG)
        for k, v in obj._attrs.items():
            try:
                setattr(obj, k, v)
            except Exception:
                pass

        # load cached parsed_df if available
        obj._cached_parsed_df = None
        if os.path.exists(parsed_path):
            obj._cached_parsed_df = pd.read_parquet(parsed_path)

        return obj

    def iter_wordtoken_matrix(self):
        yield from self.wordtokens.iter_wordtoken_matrix()

    @cached_property
    def wordtoken_matrix(self):
        return list(self.iter_wordtoken_matrix())

    def get_parseable_units(self, combine_by: Optional[Literal["line", "sent"]] = DEFAULT_COMBINE_BY):
        return self.get_list(combine_by) if combine_by is not None else self.meter.get_parse_units()

    def get_rhyming_lines(self, max_dist: int = RHYME_MAX_DIST) -> Dict[Any, Any]:
        d={}
        for stanza in self.stanzas:
            d.update(stanza.get_rhyming_lines(max_dist=max_dist))
        return d

    @property
    def num_rhyming_lines(self) -> int:
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @property
    def is_rhyming(self) -> bool:
        return self.num_rhyming_lines > 0

    def render(
        self, as_str: bool = False, blockquote: bool = False, **meter_kwargs
    ) -> Any:
        return self.parse(**meter_kwargs).render(as_str=as_str, blockquote=blockquote)


def Text(
    txt: str = "",
    fn: str = "",
    lang: Optional[str] = DEFAULT_LANG,
    parent: Optional[Entity] = None,
    children: Optional[list] = [],
    tokens_df: Optional[pd.DataFrame] = None,
    server: Optional[str] = None,
):
    # Check for remote server (explicit arg or global setting)
    from ..client import get_server, RemoteText
    remote = server or get_server()
    if remote:
        return RemoteText(txt=txt, fn=fn, server=remote)

    return TextModel(
        txt=txt, fn=fn, lang=lang, parent=parent, children=children, tokens_df=tokens_df
    )


class TextList(EntityList):
    pass
