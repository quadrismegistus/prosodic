from .imports import *
from .texts import Text


class WordTokenList(EntityList):
    pass


class Line(Text):
    line_sep = "\n"
    sep: str = "\n"
    child_type: str = "WordToken"
    is_parseable = True
    prefix = "line"
    list_type = WordTokenList
    is_parseable = False
    use_cache = False

    @profile
    def __init__(
        self,
        txt: str = "",
        children=[],
        parent=None,
        tokens_df=None,
        lang=DEFAULT_LANG,
        **kwargs,
    ):
        from .words import WordToken

        if not txt and not children and tokens_df is None:
            raise Exception("Must provide either txt, children, or tokens_df")
        txt = txt.strip()

        if not children:
            if tokens_df is None:
                tokens_df = tokenize_sentwords_df(txt)
            children = [
                WordToken(
                    txt=word_d.get("word_str", ""),
                    lang=lang,
                    parent=self,
                    sent_num=word_d.get("sent_i"),
                    sentpart_num=word_d.get("sent_i"),
                )
                for word_d in tokens_df.to_dict("records")
                if "word_str" in word_d  # and 'word_ispunc'
            ]
        Entity.__init__(self, txt=txt, children=children, parent=parent, **kwargs)
        self._parses = []
        self.is_parseable = True

    @cached_property
    def wordform_matrix(self):
        return self.get_wordform_matrix()

    def get_wordform_matrix(self, resolve_optionality=True):
        from .words import WordFormList

        lim = 1 if not resolve_optionality else None
        ll = [l for l in self.wordforms_all if l]
        ll = [WordFormList(l) for l in itertools.product(*ll)]
        ll.sort()
        return ll[:lim]

    def match_wordforms(self, wordforms):
        from .words import WordFormList

        wordforms_ll = [l for l in self.wordforms_all if l]
        assert len(wordforms) == len(wordforms_ll)

        def iterr():
            for correct_wf, target_wfl in zip(wordforms, wordforms_ll):
                targets = [wf for wf in target_wfl if wf.key == correct_wf.key]
                # if len(targets) != 1:
                # pprint([correct_wf, target_wfl, targets])
                # with logmap(announce=False) as lm:
                # lm.error("too many candidates")

                if targets:
                    yield targets[0]
                else:
                    yield target_wfl[0]

        return WordFormList(iterr())

    def to_json(self):
        return Entity.to_json(self, txt=self.txt)

    def to_html(self, parse=None, as_str=False, css=HTML_CSS, tooltip=False, **kwargs):
        if parse is None:
            parse = min(self._parses)

        output = []

        for wordtoken in self.wordtokens:
            prefstr = get_initial_whitespace(wordtoken.txt)
            if prefstr:
                odx = {"txt": prefstr}
                output.append(odx)

            wordtoken_slots = parse.wordtoken2slots[wordtoken]
            if wordtoken_slots:
                for slot in wordtoken_slots:
                    pos = slot.parent
                    spclass = f"mtr_{'s' if slot.is_prom else 'w'}"
                    stclass = f"str_{'s' if slot.unit.is_stressed else 'w'}"
                    vclass = f"viol_{'y' if pos.violset else 'n'}"
                    odx = {
                        "txt": slot.unit.txt,
                        "meter": spclass,
                        "stress": stclass,
                        "viol": vclass,
                        "viols": list(slot.violset),
                    }
                    output.append(odx)
            else:
                odx = {"txt": wordtoken.txt}
                output.append(odx)

        odf = pd.DataFrame(output)
        odf = odf.fillna(method="ffill")

        def htmlx(row, tooltip=tooltip):
            if not row.txt.strip() or not row.txt[0].isalpha():
                return row.txt

            if tooltip and row.viols:
                # viol_str = ' '.join(sorted(row.viols))
                viol_strs = [f"<li>{viol}</li>" for viol in sorted(row.viols)]
                viol_str = f'<ol>{"".join(viol_strs)}</ol>'
                viol_title = f"Violated {len(row.viols)} constraints: {viol_str}"
                rowtxt = f'{row.txt}<span class="tooltip">{viol_title}</span>'
                tooltip = " tooltip"
            else:
                tooltip = ""
                rowtxt = row.txt

            return f'<span class="{row.meter} {row.stress} {row.viol}{tooltip}">{rowtxt}</span>'

        spans = odf.apply(htmlx, axis=1)
        out = "".join(spans)
        out = f'<style>{css}</style><div class="parse">{out}</div>'
        return to_html(out, as_str=as_str)

    def stats(self, by="parse", **kwargs):
        return self.parses.stats(by=by, **kwargs)

    def stats_d(self, by="parse", **kwargs):
        return self.parses.stats_d(by=by, **kwargs)

    @cached_property
    def num_sylls(self):
        return len(self.syllables)

    @cache
    def rime_distance(self, line):
        if not self.wordforms_nopunc or not line.wordforms_nopunc:
            return np.nan
        return self.wordforms_nopunc[-1].rime_distance(line.wordforms_nopunc[-1])
