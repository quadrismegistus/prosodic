from ..imports import *

class SentenceGrid(EntityList):
    @classmethod
    def from_wordtokens(cls, wordtokens):
        grid = cls(children = wordtokens.data)
        grid.wordtokens = wordtokens
        grid.sents = wordtokens.sents
        return grid    
        
    @cached_property
    def trees(self):
        return self.sents.trees

    @cached_property
    def trees_df(self):
        tdf = self.sents.trees_df.reset_index()
        return niceindex(tdf[tdf.wordtoken_num.isin(self.wordtokens.numset)])
    
    @cached_property
    def df(self):
        df = self.trees_df.copy()
        for y in df:
            try:
                if df[y].max() == 0.0:
                    df[y] = (df[y] + abs(df[y].min()) + 1).fillna(0)
            except (TypeError, ValueError):
                pass
        df['grid_i']=[i+1 for i in range(len(df))]
        return niceindex(df.reset_index())


    def plot(self, x='grid_i', y="syntax_stress", label="wordtype_txt", **kwargs):
        from plotnine import ggplot, aes, geom_col, geom_text, theme_void, options
        options.figure_size = (11, 5)
        figdf = self.df.reset_index()[[x, y, label]]
        figdf[y] = figdf[y] + abs(figdf[y].min()) + 1
        figdf[y] = figdf[y].fillna(0)
        
        return (
            ggplot(
                figdf,
                aes(
                    x=x,
                    y=y,
                    label=label,
                ),
            )
            + geom_col(alpha=0.25)
            + geom_text(size=15)
            + theme_void()
        )
    
    def _repr_html_(self):
        return self.plot()
