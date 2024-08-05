from .imports import *

class Stanza(Text):
    sep: str = ""
    child_type: str = "Line"
    prefix = "stanza"
    list_type = 'LineList'

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
        from .lines import Line

        if not txt and not children and tokens_df is None:
            raise Exception("Must provide either txt, children, or tokens_df")
        if not children:
            if tokens_df is None:
                tokens_df = tokenize_sentwords_df(txt)
            children = [
                Line(parent=self, tokens_df=line_df)
                for line_i, line_df in tokens_df.groupby("line_i")
            ]
        Entity.__init__(self, txt, children=children, parent=parent, **kwargs)

    def to_json(self):
        return Entity.to_json(self, no_txt=True)

    def _repr_html_(self, as_df=False, df=None):
        return super()._repr_html_(df=df) if as_df else self.to_html(as_str=True)

    def get_rhyming_lines(self, max_dist=RHYME_MAX_DIST):
        return self.children.get_rhyming_lines(max_dist=max_dist)

    @cached_property
    def num_rhyming_lines(self):
        return len(self.get_rhyming_lines(max_dist=RHYME_MAX_DIST))

    @cached_property
    def is_rhyming(self):
        return self.num_rhyming_lines > 0
