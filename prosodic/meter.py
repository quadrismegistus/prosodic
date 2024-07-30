from .imports import *
from .constraints import *
from .texts import Text

NUM_GOING = 0
# METER
DEFAULT_METER_KWARGS = dict(
    constraints=DEFAULT_CONSTRAINTS,
    categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS,
    max_s=METER_MAX_S,
    max_w=METER_MAX_W,
    resolve_optionality=METER_RESOLVE_OPTIONALITY,
    exhaustive=False,
)
MTRDEFAULT = DEFAULT_METER_KWARGS


class Meter(Entity):
    prefix = "meter"

    def __init__(
        self,
        constraints=MTRDEFAULT["constraints"],
        categorical_constraints=MTRDEFAULT["categorical_constraints"],
        max_s=MTRDEFAULT["max_s"],
        max_w=MTRDEFAULT["max_w"],
        resolve_optionality=MTRDEFAULT["resolve_optionality"],
        exhaustive=MTRDEFAULT["exhaustive"],
        **kwargs,
    ):
        self.constraints = get_constraints(constraints)
        self.categorical_constraints = get_constraints(categorical_constraints)
        self.max_s = max_s
        self.max_w = max_w
        self.resolve_optionality = resolve_optionality
        self.exhaustive = exhaustive
        super().__init__()

    @property
    def use_cache(self):
        return caching_is_enabled()

    @property
    def use_cache_lines(self):
        return self.use_cache

    @property
    def use_cache_texts(self):
        return False

    def to_json(self):
        return super().to_json(**self.attrs)

    @cached_property
    def constraint_names(self):
        return tuple(c.__name__ for c in self.constraints)

    @cached_property
    def categorical_constraint_names(self):
        return tuple(c.__name__ for c in self.categorical_constraints)

    @cached_property
    def attrs(self):
        return {
            "constraints": self.constraint_names,
            "categorical_constraints": self.categorical_constraint_names,
            "max_s": self.max_s,
            "max_w": self.max_w,
            "resolve_optionality": self.resolve_optionality,
            "exhaustive": self.exhaustive,
        }

    @cache
    def get_pos_types(self, nsylls=None):
        max_w = nsylls if self.max_w is None else self.max_w
        max_s = nsylls if self.max_s is None else self.max_s
        wtypes = ["w" * n for n in range(1, max_w + 1)]
        stypes = ["s" * n for n in range(1, max_s + 1)]
        return wtypes + stypes

    def get_wordform_matrix(self, line):
        return line.get_wordform_matrix(resolve_optionality=self.resolve_optionality)

    def parse(self, text_or_line, **kwargs):
        return ParseList(
            self.parse_iter(
                text_or_line,
                **kwargs,
            ),
            type=self.__class__.__name__.lower(),
            line=text_or_line if text_or_line.is_parseable else None,
        )

    def parse_iter(self, text_or_line, force=False, **kwargs):
        if type(text_or_line) in {Text, Stanza}:
            yield from self.parse_text_iter(text_or_line, force=force, **kwargs)
        elif text_or_line.is_parseable:
            yield from self.parse_line(text_or_line, force=force, **kwargs)
        else:
            raise Exception(f"Object {text_or_line} not parseable")

    def parse_line(self, line, force=False, **kwargs):
        assert line.is_parseable
        if line.num_sylls < 2:
            return ParseList(type="line", line=line)

        if not force and self.use_cache_lines and caching_is_enabled():
            parses = self.parses_from_cache(line)
            line._parses = parses
            if parses:
                return parses

        if self.exhaustive:
            parses = self.parse_line_exhaustive(line)
        else:
            parses = self.parse_line_fast(line)

        if self.use_cache_lines and caching_is_enabled():
            self.cache(val_obj=parses, key=self.get_key(line))

        return parses

    def get_key(self, line):
        return hashstr(self.key, line.key)

    def parses_from_cache(self, line, as_dict=False):
        from .parsing import ParseList

        key = self.get_key(line)
        clsn = line.__class__.__name__.lower()
        # with logmap(
        #         f'checking for cached {clsn} parses under key "{key[:8]}..."'
        # ) as lm:
        dat = self.from_cache(key=key, as_dict=True)
        if dat:
            nchild = len(dat.get("children", [])) if dat else 0
            # lm.log(f"found {nchild:,} parses")
            if as_dict:
                return dat
            with logmap("converting cache result to parses"):
                return ParseList.from_json(
                    dat,
                    line=line,
                    progress=nchild >= 100,
                )

    def parse_line_fast(self, line, force=False):
        from .parsing import ParseList, Parse

        assert line.is_parseable
        parses = ParseList(
            [
                Parse(
                    wfl,
                    pos,
                    meter=self,
                    parent=line,
                )
                for wfl in self.get_wordform_matrix(line)
                for pos in self.get_pos_types(nsylls=wfl.num_sylls)
            ],
            line=line,
        )
        for n in range(1000):
            # logger.debug(f'Now at {i}A, there are {len(parses)} parses')
            parses = ParseList(
                [
                    newparse
                    for parse in parses
                    for newparse in parse.branch()
                    if not parse.is_bounded
                    and newparse is not None
                    and parse is not None
                ],
                type="line",
                line=line,
            )
            parses.bound(progress=False)
            if all(p.is_complete for p in parses):
                break
        else:
            logger.error(f"did not complete parsing: {line}")
        parses.bound(progress=False)
        parses.rank()
        line._parses = parses
        return line._parses

    # slower, exhaustive parser

    def parse_line_exhaustive(self, line, progress=None):
        from .parsing import ParseList, Parse

        assert line.is_parseable

        def iter_parses():
            wfm = self.get_wordform_matrix(line)
            all_parses = []
            combos = [
                (wfl, scansion)
                for wfl in wfm
                for scansion in get_possible_scansions(
                    wfl.num_sylls, max_s=self.max_s, max_w=self.max_w
                )
            ]
            wfl = wfm[0]
            logger.trace(
                f"Generated {len(combos)} from a wordfrom matrix of size {len(wfm), wfl, wfl.num_sylls, self.max_s, self.max_s, len(get_possible_scansions(wfl.num_sylls))}"
            )
            iterr = tqdm(combos, disable=not progress, position=0)
            for wfl, scansion in iterr:
                parse = Parse(wfl, scansion, meter=self, parent=line)
                all_parses.append(parse)
            logger.trace(f"Returning {len(all_parses)} parses")
            return all_parses

        parses = ParseList(iter_parses(), type="line", line=line)
        parses.bound(progress=False)
        parses.rank()
        line._parses = parses
        return line._parses

    def parse_text(self, text, num_proc=DEFAULT_NUM_PROC, progress=True):
        iterr = self.parse_text_iter(text, num_proc=num_proc, progress=progress)
        deque(iterr, maxlen=0)

    def parse_text_iter(
        self,
        text,
        progress=True,
        force=False,
        num_proc=DEFAULT_NUM_PROC,
        use_mp=True,
        **kwargs,
    ):
        global NUM_GOING
        NUM_GOING += 1
        # print(NUM_GOING,type(type),text)
        from .parsing import ParseList

        assert type(text) in {Text, Stanza}

        done = False
        if not force and self.use_cache_texts and caching_is_enabled():
            parses = self.parses_from_cache(text)
            if parses:
                text._parses = parses
                for st in text:
                    st._parses = ParseList(type="stanza")
                    for l in st:
                        l._parses = ParseList(type="list")
                for parse in parses:
                    if parse.stanza_num:
                        stanza = text.stanzas[parse.stanza_num - 1]
                        stanza._parses.append(parse)
                        line = stanza.lines[parse.line_num - 1]
                        line._parses.append(parse)

                yield from text.parseable_units
                done = True

        if not done:
            text._parses = ParseList(type="text")
            lines = text.parseable_units
            numlines = len(lines)

            # reset parses for stanzas
            for stanza in unique(line.stanza for line in lines):
                stanza._parses = ParseList(type="text")

            # if num_proc is None: num_proc = 1 if numlines<=14 else mp.cpu_count()-1
            if not use_mp:
                num_proc = 1
            if num_proc is None:
                num_proc = mp.cpu_count() // 2 if mp.cpu_count() > 1 else 1
            desc = f"parsing {numlines} {text.parse_unit_attr}"

            if num_proc > 1:
                desc += f" [{num_proc}x]"
            with logmap(desc) as lm:
                if num_proc > 1:
                    iterr = self._parse_text_iter_mp(
                        text,
                        progress=progress,
                        force=force,
                        num_proc=num_proc,
                        lm=lm,
                        desc="parsing",
                    )

                # @TODO: not working?
                else:
                    iterr = (
                        self.parse_line(
                            line,
                            force=force,
                            **kwargs,
                        )
                        for line in lm.iter_progress(
                            text.parseable_units,
                            desc="parsing",
                        )
                    )

                # newstanzas = set()
                for i, parselist in enumerate(iterr):
                    line = text.parseable_units[i]
                    parselist.line = line
                    line._parses = parselist
                    text._parses.extend(parselist)
                    line.stanza._parses.extend(parselist)
                    yield line
                    if line.num and line.stanza and line.stanza.num:
                        # if not line.stanza.num in newstanzas:
                        # newstanzas.add(line.stanza.num)
                        lm.log(
                            f"stanza {line.stanza.num:02}, line {line.num:02}: {line.best_parse.txt if line.best_parse else line.txt}",
                            linelim=70,
                        )

            if self.use_cache_texts and caching_is_enabled():
                self.cache(val_obj=text._parses, key=self.get_key(text))

    def _parse_text_iter_mp(
        self,
        text,
        force=False,
        progress=True,
        num_proc=DEFAULT_NUM_PROC,
        lm=None,
        **progress_kwargs,
    ):
        from .parsing import ParseList

        assert lm
        objs = [
            (
                line.to_json(),
                self.to_json(),
                force or not self.use_cache_lines or not caching_is_enabled(),
            )
            for line in text.parseable_units
        ]
        iterr = lm.imap(
            _parse_iter, objs, progress=progress, num_proc=num_proc, **progress_kwargs
        )
        for i, parselist_json in enumerate(iterr):
            line = text.parseable_units[i]
            yield ParseList.from_json(parselist_json, line=line)


def _parse_iter(obj):
    line_json, meter_json, force = obj
    line, meter = from_json(line_json), from_json(meter_json)
    if not force:
        parse_data = meter.parses_from_cache(line, as_dict=True)
        if parse_data:
            return parse_data

    parses = meter.parse_line(line, force=True)
    return parses.to_json()
