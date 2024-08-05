from .imports import *
from .ents import Entity

class EntityList(Entity):
    """
    A list of Entity objects.
    """

    def __init__(self, children=[], parent=None, **kwargs):
        """
        Initialize an EntityList object.

        Args:
            children (list): List of child entities.
            parent (Entity): The parent entity.
            **kwargs: Additional attributes to set on the entity.
        """
        self.parent = parent
        self.children = [x for x in children]
        self._attrs = kwargs
        self._txt = None
        for k, v in self._attrs.items():
            setattr(self, k, v)

    @cached_property
    def txt(self):
        """
        Get the text content of the entity list.

        Returns:
            None: Always returns None for EntityList objects.
        """
        return None



class StanzaList(EntityList):
    pass


class LineList(EntityList):
    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        line2rhyme = defaultdict(list)
        for line in self.data:
            prev_lines = self.data[: line.i]
            if not prev_lines:
                continue
            for line2 in prev_lines:
                dist = line.rime_distance(line2)
                if max_dist is None or dist <= max_dist:
                    line2rhyme[line].append((dist, line2))
        return {i: min(v) for i, v in line2rhyme.items()}


class WordTokenList(EntityList):
    pass


class ParseList(EntityList):
    index_name = "parse"
    prefix = "parselist"
    show_bounded = False
    is_scansions = False

    def __init__(self, *args, line=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.line = line
        # self.rank()

    @staticmethod
    def from_json(json_d, line=None, progress=False):
        from .parsing import Parse
        with logmap(announce=progress) as lm:
            parses = lm.imap(
                Parse.from_json,
                json_d["children"],
                kwargs=dict(line=line),
                progress=progress,
                num_proc=1,
            )
        return ParseList(parses, parent=line, type=json_d.get("type"))

    @cached_property
    def num_parses(self):
        return self.num_unbounded

    @cached_property
    def attrs(self):
        return {
            # **self.line.stanza.prefix_attrs,
            # **(self.line.prefix_attrs if self.line else {}),
            **self._attrs,
            # 'parses_num': self.num_parses,
            # 'num_all_parses':self.num_all_parses
        }

    @cached_property
    def meter(self):
        for parse in self:
            if parse.meter:
                return parse.meter
        if self.line:
            return self.line.meter

    def to_json(self, fn=None):
        return Entity.to_json(
            (self.scansions if self.meter and not self.meter.exhaustive else self),
            fn=fn,
            type=self.type,
        )

    @cached_property
    def all(self):
        return self.scansions

    @cached_property
    def best(self):
        return min(self.data) if self.data else None

    @cached_property
    def unbounded(self):
        return ParseList(
            children=[
                px for px in self.scansions if px is not None and not px.is_bounded
            ],
            type=self.type,
        )

    @cached_property
    def bounded(self):
        return ParseList(
            [px for px in self.scansions if px is not None and px.is_bounded],
            show_bounded=True,
            type=self.type,
        )

    @cached_property
    def best_parse(self):
        return self.best

    @cached_property
    def num_unbounded(self):
        return len(self.unbounded)

    @cached_property
    def num_bounded(self):
        return len(self.bounded)

    @cached_property
    def num_all(self):
        return len(self.scansions)

    @cached_property
    def num_all_with_combos(self):
        return len(self.data)

    @cached_property
    def parses(self):
        return self

    def bound(self, progress=False):
        parses = [p for p in self.data if not p.is_bounded]
        iterr = tqdm(parses, desc="Bounding parses", disable=not progress, position=0)
        for parse_i, parse in enumerate(iterr):
            parse.constraint_viols  # init
            if parse.is_bounded:
                continue
            for comp_parse in parses[parse_i + 1 :]:
                if comp_parse.is_bounded:
                    continue
                if not parse.can_compare(comp_parse):
                    continue
                relation = parse.bounding_relation(comp_parse)
                if relation == Bounding.bounded:
                    parse.is_bounded = True
                    parse.bounded_by.append(
                        (comp_parse.meter_str, comp_parse.stress_str)
                    )
                elif relation == Bounding.bounds:
                    comp_parse.is_bounded = True
                    comp_parse.bounded_by.append((parse.meter_str, parse.stress_str))
        self._bound_init = True
        return self.unbounded

    def rank(self):
        self.data.sort()
        for i, parse in enumerate(self.data):
            parse.parse_rank = i + 1

    @cached_property
    def line(self):
        for parse in self.data:
            if parse.line:
                return parse.line

    @cached_property
    def lines(self):
        return LineList(unique(parse.line for parse in self.data))

    @cached_property
    def prefix_attrs(self):
        return {
            **({} if not self.line else self.line.prefix_attrs),
            **super().prefix_attrs,
            # **{
            #     f'{self.prefix}_{k}': v
            #     for (
            #         k,
            #         v,
            #     ) in self.attrs.items()
            # }
        }

    @cache
    def stats_d(self, by=None, norm=None, incl_bounded=False, **kwargs):
        odf = self.stats(by=by, norm=norm, incl_bounded=incl_bounded, **kwargs)
        aggby = self._get_aggby(odf)
        resd = dict(odf.agg(aggby))
        return {
            **self.prefix_attrs,
            **{k: v for k, v in resd.items() if k not in self.prefix_attrs},
        }

    def _get_groupby(self, by=None):
        if by is None:
            by = "parse"  # if self.type != "text" else "line"
        if by == "stanza":
            groupby = ["stanza_num"]
        elif by == "line":
            groupby = ["stanza_num", "line_num", "line_txt"]
        else:
            groupby = []
        return groupby

    def _get_aggby(self, df):
        df_q = df.select_dtypes("number")

        def getagg(col):
            if col.endswith("_norm"):
                return "mean"
            if self.type in {"text", "stanza"}:
                return "median"
            return "median"

        aggby = {col: getagg(col) for col in df_q}
        return aggby

    @cache
    def stats(self, norm=None, incl_bounded=None, by=None, **kwargs):
        if incl_bounded is None:
            incl_bounded = self.show_bounded
        if by == "syll":
            odf = self.df_syll
            if not incl_bounded:
                odf = odf[odf.parse_is_bounded == 0]
            return odf
        odf = pd.DataFrame(
            parse.stats_d(norm=norm)
            for parse in self
            if incl_bounded or not parse.is_bounded
        )
        odf.columns = [
            (
                f"parse_{c}"
                if c[0] != "*" and c.split("_")[0] not in {"stanza", "line"}
                else c
            )
            for c in odf
        ]
        groupby = self._get_groupby(by=by)
        if groupby:
            odf = odf.set_index(groupby)
            aggby = self._get_aggby(odf)
            odf = odf.groupby(groupby).agg(aggby)
            odf = odf.drop("parse_rank", axis=1)
            if not "line_num" in set(groupby):
                odf = odf.drop("line_num", axis=1)
            return odf.sort_index()
        else:
            odf["parse_rank"] = (
                odf.groupby(["stanza_num", "line_num"])
                .parse_rank.rank(method="min")
                .apply(force_int)
            )
            return setindex(odf, DF_INDEX).sort_index()

    def _repr_html_(self):
        df = (
            self.unbounded.df
            if not self.show_bounded and self.num_unbounded
            else self.scansions.df
        )
        return super()._repr_html_(df=df)

    @cached_property
    def df(self):
        return self.stats()

    @cached_property
    def df_norm(self):
        return self.stats(norm=True)

    @cached_property
    def df_raw(self):
        return self.stats(norm=False)

    def get_df(self, *x, **y):
        l = self.unbounded if not self.show_bounded else self.scansions
        l = [p.get_df() for p in l]
        return pd.concat(l).sort_index() if l else pd.DataFrame()

    @cached_property
    def df_syll(self, bad_keys={"line_numparse"}):
        # odf = self.get_df().assign(**self._attrs)
        odf = self.get_df()
        return odf[[c for c in odf if not bad_keys or c not in bad_keys]]

    @cached_property
    def scansions(self, **kwargs):
        """
        Unique scansions
        """
        if self.is_scansions:
            return self

        plist = []
        mstrs = set()
        countd = Counter()
        for parse in sorted(self.data):
            lkey = (parse.stanza_num, parse.line_num)
            key = (parse.stanza_num, parse.line_num, parse.meter_str)
            if key not in mstrs:
                mstrs.add(key)
                countd[lkey] += 1
                parse.parse_rank = countd[lkey]
                plist.append(parse)

        return ParseList(plist, is_scansions=True, show_bounded=True, type=self.type)

    @cached_property
    def num_lines(self):
        return len(self.lines)

    def render(self, as_str=False, blockquote=False):
        return self.to_html(as_str=as_str, blockquote=blockquote)

    def to_html(self, as_str=False, blockquote=False):
        html_strs = (
            line.to_html(blockquote=blockquote, as_str=True) for line in self.lines
        )
        html = "</li>\n<li>".join(html_strs)
        html = f'<ol class="parselist"><li>{html}</li></ol>'
        return to_html(html, as_str=as_str)



class SyllableList(EntityList):
    pass


class WordTypeList(EntityList):
    pass


@total_ordering
class WordFormList(EntityList):
    def __repr__(self):
        return " ".join(wf.token_stress for wf in self.data)

    @cached_property
    def slots(self):
        return [syll for wordform in self.data for syll in wordform.children]

    @cached_property
    def num_stressed_sylls(self):
        return sum(
            int(syll.is_stressed)
            for wordform in self.data
            for syll in wordform.children
        )

    @cached_property
    def num_sylls(self):
        return sum(1 for wordform in self.data for syll in wordform.children)

    @cached_property
    def first_syll(self):
        for wordform in self.data:
            for syll in wordform.children:
                return syll

    @cached_property
    def sort_key(self):
        sylls_is_odd = int(bool(self.num_sylls % 2))
        first_syll_stressed = (
            2 if self.first_syll is None else int(self.first_syll.is_stressed)
        )
        return (
            sylls_is_odd,
            self.num_sylls,
            self.num_stressed_sylls,
            first_syll_stressed,
        )

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    def __eq__(self, other):
        # return self.sort_key==other.sort_key
        return self is other





class PhonemeList(EntityList):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def do_phons(phons):
            vowel_yet = False
            for phon in phons:
                if not phon.is_vowel:
                    if not vowel_yet:
                        phon._attrs["is_onset"] = True
                        phon._attrs["is_rime"] = False
                        phon._attrs["is_nucleus"] = False
                        phon._attrs["is_coda"] = False
                    else:
                        phon._attrs["is_onset"] = False
                        phon._attrs["is_rime"] = True
                        phon._attrs["is_nucleus"] = False
                        phon._attrs["is_coda"] = True
                else:
                    vowel_yet = True
                    phon._attrs["is_onset"] = False
                    phon._attrs["is_rime"] = True
                    phon._attrs["is_nucleus"] = True
                    phon._attrs["is_coda"] = False

        # get syll specific feats
        phons_by_syll = group_ents(self.children, "syllable")

        for phons in phons_by_syll:
            do_phons(phons)
