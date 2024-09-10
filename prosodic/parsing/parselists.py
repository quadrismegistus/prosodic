from typing import List, Dict, Any, Optional, Union
from ..imports import *
from .utils import *

class ParseList(EntityList):
    """
    A list of Parse objects representing possible metrical parses for a line of poetry.

    Attributes:
        index_name (str): Name of the index for this list type.
        prefix (str): Prefix used for attribute names.
        show_bounded (bool): Whether to show bounded parses.
        is_scansions (bool): Whether this list represents scansions.
        line (Optional[Line]): The Line object this ParseList is associated with.
    """

    index_name: str = "parse"
    prefix: str = "parselist"
    show_bounded: bool = False
    is_scansions: bool = False

    # def __init__(self, *args: Any, wordtokens: Optional['WordTokenList'] = None, **kwargs: Any) -> None:
    #     """
    #     Initialize a ParseList.

    #     Args:
    #         *args: Variable length argument list.
    #         line: The Line object this ParseList is associated with.
    #         **kwargs: Arbitrary keyword arguments.
    #     """
    #     super().__init__(*args, **kwargs)
    #     self.parent = self.wordtokens = wordtokens
    #     self.data = list(self.data)

    @classmethod
    def from_combinations(cls, parselistlist, parent=None):
        from .parses import Parse
        pll = [list(parselist) for parselist in parselistlist if parselist and len(parselist)]
        new_parses = cls(
            [
                Parse.concat(*parse_combo, wordtokens_cls=type(parent) if parent is not None else None)
                for parse_combo in itertools.product(*pll)
            ],
            parent=parent,
        )
        new_parses.bound(progress=False)
        new_parses.rank()
        return new_parses

    def to_dict(self, **kwargs):
        return super().to_dict(parent=self.parent.to_dict(incl_children=True), **kwargs)
    
    @classmethod
    def from_dict(cls, data):
        cls_name, cls_data = next(iter(data.items()))
        assert cls.__name__ == cls_name
        children = [Entity.from_dict(xdata) for xdata in cls_data.pop('children',[])]
        parent = Entity.from_dict(cls_data.pop('parent')) if 'parent' in cls_data else None
        return cls(children=children, parent=parent)

    @property
    def num_parses(self) -> int:
        """
        Get the number of unbounded parses.

        Returns:
            The number of unbounded parses.
        """
        return self.num_unbounded

    @property
    def attrs(self) -> Dict[str, Any]:
        """
        Get the attributes of this ParseList.

        Returns:
            A dictionary of attributes.
        """
        return {
            **self._attrs,
        }

    @property
    def meter(self) -> Optional['Meter']:
        """
        Get the meter associated with this ParseList.

        Returns:
            The Meter object, if available.
        """
        for parse in self:
            if parse.meter:
                return parse.meter
        if self.line:
            return self.line.meter

    @property
    def all(self) -> 'ParseList':
        """
        Get all parses, including scansions.

        Returns:
            A ParseList containing all parses.
        """
        return self.scansions

    @property
    def best(self) -> 'ParseList':
        """
        Get the best parse.

        Returns:
            The best Parse object, or None if no parses are available.
        """
        return self.best_parses

    @cached_property
    def unbounded(self) -> 'ParseList':
        """
        Get unbounded parses.

        Returns:
            A ParseList containing only unbounded parses.
        """
        return ParseList(
            children=[
                px for px in self.scansions if px is not None and not px.is_bounded
            ],
            type=self.type,
        )

    @cached_property
    def bounded(self) -> 'ParseList':
        """
        Get bounded parses.

        Returns:
            A ParseList containing only bounded parses.
        """
        return ParseList(
            [px for px in self.scansions if px is not None and px.is_bounded],
            show_bounded=True,
            type=self.type,
        )

    @property
    def best_parse(self) -> Optional['Parse']:
        """
        Get the best parse.

        Returns:
            The best Parse object, or None if no parses are available.
        """
        return min(self.data) if self.data else None
    
    @property
    def best_parses(self) -> 'ParseList':
        """
        Get bounded parses.

        Returns:
            A ParseList containing only bounded parses.
        """
        return ParseList(
            [px for px in self.scansions if px is not None and px.parse_rank==1],
            show_bounded=False,
            type=self.type,
        )


    @property
    def num_unbounded(self) -> int:
        """
        Get the number of unbounded parses.

        Returns:
            The number of unbounded parses.
        """
        return len(self.unbounded)

    @property
    def num_bounded(self) -> int:
        """
        Get the number of bounded parses.

        Returns:
            The number of bounded parses.
        """
        return len(self.bounded)

    @property
    def num_all(self) -> int:
        """
        Get the total number of parses.

        Returns:
            The total number of parses.
        """
        return len(self.scansions)

    @property
    def num_all_with_combos(self) -> int:
        """
        Get the total number of parses including combinations.

        Returns:
            The total number of parses including combinations.
        """
        return len(self.data)

    @property
    def parses(self) -> 'ParseList':
        """
        Get all parses.

        Returns:
            This ParseList object.
        """
        return self

    def bound(self, progress: bool = False) -> 'ParseList':
        """
        Bound the parses in this ParseList.

        Args:
            progress: Whether to show progress during bounding.

        Returns:
            A ParseList containing unbounded parses after bounding.
        """
        parses = [p for p in self.data if not p.is_bounded]
        iterr = tqdm(parses, desc="Bounding parses", disable=not progress, position=0)
        for parse_i, parse in enumerate(iterr):
            # parse.init()
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

    def rank(self) -> None:
        """
        Rank the parses in this ParseList.
        """
        self.data.sort()
        for i, parse in enumerate(self.data):
            parse.parse_rank = i + 1

    @property
    def line(self) -> Optional['Line']:
        """
        Get the Line object associated with this ParseList.

        Returns:
            The Line object, if available.
        """
        for parse in self.data:
            if parse.line:
                return parse.line

    @property
    def lines(self) -> 'LineList':
        """
        Get a list of unique Line objects associated with this ParseList.

        Returns:
            A LineList containing unique Line objects.
        """
        return LineList(unique(parse.line for parse in self.data))

    @property
    def prefix_attrs(self) -> Dict[str, Any]:
        """
        Get prefix attributes for this ParseList.

        Returns:
            A dictionary of prefix attributes.
        """
        return {
            **({} if not self.line else self.line.prefix_attrs),
            **super().prefix_attrs,
        }

    @cache
    def stats_d(self, by: Optional[str] = None, norm: Optional[bool] = None, incl_bounded: bool = False, **kwargs: Any) -> Dict[str, Any]:
        """
        Get statistics for this ParseList.

        Args:
            by: How to group the statistics.
            norm: Whether to normalize the statistics.
            incl_bounded: Whether to include bounded parses.
            **kwargs: Additional keyword arguments.

        Returns:
            A dictionary of statistics.
        """
        odf = self.stats(by=by, norm=norm, incl_bounded=incl_bounded, **kwargs)
        aggby = self._get_aggby(odf)
        resd = dict(odf.agg(aggby))
        return {
            **self.prefix_attrs,
            **{k: v for k, v in resd.items() if k not in self.prefix_attrs},
        }

    def _get_groupby(self, by: Optional[str] = None) -> List[str]:
        """
        Get the grouping columns for statistics.

        Args:
            by: How to group the statistics.

        Returns:
            A list of column names to group by.
        """
        if by is None:
            by = "parse"  # if self.type != "text" else "line"
        if by == "stanza":
            groupby = ["stanza_num"]
        elif by == "line":
            groupby = ["stanza_num", "line_num", "line_txt"]
        else:
            groupby = []
        return groupby

    def _get_aggby(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Get the aggregation functions for statistics.

        Args:
            df: The DataFrame to aggregate.

        Returns:
            A dictionary mapping column names to aggregation functions.
        """
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
    def stats(self, norm: Optional[bool] = None, incl_bounded: Optional[bool] = None, by: Optional[str] = None, **kwargs: Any) -> pd.DataFrame:
        """
        Get statistics for this ParseList as a DataFrame.

        Args:
            norm: Whether to normalize the statistics.
            incl_bounded: Whether to include bounded parses.
            by: How to group the statistics.
            **kwargs: Additional keyword arguments.

        Returns:
            A DataFrame containing statistics.
        """
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
            print(odf.columns)
            print(odf)
            odf = setindex(odf, groupby)
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

    def _repr_html_(self) -> str:
        """
        Get an HTML representation of this ParseList.

        Returns:
            An HTML string representing this ParseList.
        """
        df = (
            self.unbounded.df
            if not self.show_bounded and self.num_unbounded
            else self.scansions.df
        )
        return super()._repr_html_(df=df)

    @property
    def df(self) -> pd.DataFrame:
        """
        Get a DataFrame representation of this ParseList.

        Returns:
            A DataFrame representing this ParseList.
        """
        return self.stats()

    @property
    def df_norm(self) -> pd.DataFrame:
        """
        Get a normalized DataFrame representation of this ParseList.

        Returns:
            A normalized DataFrame representing this ParseList.
        """
        return self.stats(norm=True)

    @property
    def df_raw(self) -> pd.DataFrame:
        """
        Get a raw DataFrame representation of this ParseList.

        Returns:
            A raw DataFrame representing this ParseList.
        """
        return self.stats(norm=False)

    def get_df(self, *x: Any, **y: Any) -> pd.DataFrame:
        """
        Get a DataFrame representation of this ParseList.

        Args:
            *x: Positional arguments.
            **y: Keyword arguments.

        Returns:
            A DataFrame representing this ParseList.
        """
        l = self.unbounded if not self.show_bounded else self.scansions
        l = [p.get_df() for p in l]
        return pd.concat(l).sort_index() if l else pd.DataFrame()

    @property
    def df_syll(self) -> pd.DataFrame:
        """
        Get a syllable-level DataFrame representation of this ParseList.

        Returns:
            A syllable-level DataFrame representing this ParseList.
        """
        bad_keys = {"line_numparse"}
        odf = self.get_df()
        return odf[[c for c in odf if not bad_keys or c not in bad_keys]]

    @cached_property
    def scansions(self) -> 'ParseList':
        """
        Get unique scansions for this ParseList.

        Returns:
            A ParseList containing unique scansions.
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

    @property
    def num_lines(self) -> int:
        """
        Get the number of lines in the ParseList.

        Returns:
            int: The number of lines.
        """
        return len(self.lines)

    def render(self, as_str: bool = False, blockquote: bool = False) -> Union[str, 'HTML']:
        """
        Render the ParseList as HTML.

        Args:
            as_str: Whether to return the result as a string.
            blockquote: Whether to render each line as a blockquote.

        Returns:
            Union[str, 'HTML']: The rendered HTML, either as a string or an HTML object.
        """
        return self.to_html(as_str=as_str, blockquote=blockquote)

    def to_html(self, as_str: bool = False, blockquote: bool = False) -> Union[str, 'HTML']:
        """
        Convert the ParseList to HTML.

        Args:
            as_str: Whether to return the result as a string.
            blockquote: Whether to render each line as a blockquote.

        Returns:
            Union[str, 'HTML']: The HTML representation, either as a string or an HTML object.
        """
        html_strs = (
            line.to_html(blockquote=blockquote, as_str=True) for line in self.lines
        )
        html = "</li>\n<li>".join(html_strs)
        html = f'<ol class="parselist"><li>{html}</li></ol>'
        return to_html(html, as_str=as_str)




class ParseListList(ParseList):
    pass