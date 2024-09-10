from ..imports import *
from ..lib.metricaltree.deptree import *
from ..lib.metricaltree.metricaltree import *

STRESS_STRS = set("`'")
ALLOW_AMBIG_MTREE = False


class SentenceTree(MetricalTree):
    def __init__(
        self,
        node,
        children,
        dep=None,
        lstress=np.nan,
        pstress=np.nan,
        stress=np.nan,
        allow_ambig=ALLOW_AMBIG_MTREE,
        wordtoken=None,
        **kwargs,
    ):

        self._lstress = lstress
        self._pstress = pstress
        self._stress = stress
        super(MetricalTree, self).__init__(node, children, dep)
        self.set_label()
        self._phrasal_head = np.nan
        self._phrasal_stress_peak = np.nan
        self._phrasal_stress_valley = np.nan
        self._pstrength = np.nan
        self._stress_num_binary = np.nan
        self._stress_num = np.nan
        self._seg = None
        self._nsyll = np.nan
        self._nstress = np.nan
        self._wordtoken = wordtoken
        self._word_tok = "" if not wordtoken else wordtoken._txt.strip()
        self._ltress = np.nan
        self._attrs = {}
        self._preterm_index = None

        if self._preterm:
            assert self._wordtoken
            wtok = self._wordtoken
            wtok._preterm = self

            if (
                self._cat in self._unstressedTags
            ):  # or self._dep in self._unstressedDeps:
                wtok.force_unstress()
            elif (
                self._cat in self._ambiguousTags
            ):  # or self._dep in self._ambiguousDeps:
                wtok.force_ambig_stress()

            wordtype = wtok.wordtype
            if wordtype.children:
                wordform = wordtype.children[0]
                self._num_variants = wordtype.num_forms
                self._is_ambig = self._num_variants > 1
                self._nsyll = wordform.num_sylls
                self._seg = wordform.ipa
                self._nstress = wordform.num_stressed_sylls
                self._stress_num_binary = float(int(wordform.is_stressed)) - 1
                self._stress_num = self._stress_num_binary
                self._lstress = float(self._stress_num_binary)

            self.set_label()

    @classmethod
    def from_sent(cls, sent):
        deptree_str = get_treeparse_str(sent.nlp)
        deptree = DependencyTree.fromstring(deptree_str)
        preterms=list(deptree.preterminals())
        assert len(preterms)==len(sent.children), 'Should equal number of wordtokens'
        for preterm,token in zip(preterms, sent.children):
            preterm._wordtoken = token
            token._preterm = preterm
        tree = SentenceTree.from_deptree(deptree)
        tree.sent = sent
        tree.wordtokens = sent.wordtokens
        return tree

    def set_preterm_index(self):
        """
        Assigns an index to each preterminal node in the tree.
        The index starts from 1 and increases in order of appearance.
        """
        preterms = list(self.preterminals())
        for index, preterm in enumerate(preterms, start=1):
            preterm._preterm_index = index

    @classmethod
    def convert(cls, tree):
        """
        Convert a tree between different subtypes of Tree.  ``cls`` determines
        which class will be used to encode the new tree.

        :type tree: Tree
        :param tree: The tree that should be converted.
        :return: The new Tree.
        """
        if isinstance(tree, Tree):
            assert isinstance(tree, DependencyTree)
            children = [cls.convert(child) for child in tree]
            wordtoken = getattr(tree, "_wordtoken", None)
            newtree = cls(
                node=tree._cat, children=children, dep=tree._dep, wordtoken=wordtoken
            )
            return newtree
        else:
            return tree

    @classmethod
    def from_deptree(cls, deptree):
        tree = cls.convert(deptree)
        tree.set_preterm_index()
        tree.set_pstress()
        tree.set_stress()
        find_phrasal_heads(tree)
        tree.set_phrasal_peaks()
        return tree
    
    def set_label(self):
        if self._preterm and not np.isnan(self._stress):
            self._label = '%s/%s' % (self._cat, int(self._stress))
        else:
            self._label = self._cat

    # def set_labels(self):
    #     self.set_label()
    #     for child in self:
    #         child.set_labels()

    @property
    def lstress(self):
        return self._lstress

    @property
    def pstress(self):
        return self._pstress

    @property
    def pstress_pos(self):
        return -(self._pstress - 1)

    @property
    def stress(self):
        return self._stress

    @property
    def stress_pos(self):
        return -(self._stress - 1)

    @property
    def seg(self):
        return self._seg if self._seg is not None else []

    @property
    def nseg(self):
        return len(self._seg) if self._seg is not None else np.nan

    @property
    def nsyll(self):
        return self._nsyll

    @property
    def nstress(self):
        return self._nstress

    # =====================================================================
    # Set the lexical stress of the node
    def set_lstress(self, allow_ambig=ALLOW_AMBIG_MTREE):
        # self.gen_word_info()

        if self._preterm:
            #log.debug(f"setting lstress for {self._wordtoken}")
            if self[0].lower() in super(MetricalTree, self)._contractables:
                self._lstress = np.nan
            elif self._cat in super(MetricalTree, self)._punctTags:
                self._lstress = np.nan
            elif self._cat in MetricalTree._unstressedTags:
                self._lstress = -1
            elif allow_ambig and self._cat in MetricalTree._ambiguousTags:
                self._lstress = -0.5
            elif self._dep in MetricalTree._unstressedDeps:
                self._lstress = -1
            elif allow_ambig and self._dep in MetricalTree._ambiguousDeps:
                self._lstress = -0.5
            elif allow_ambig and self._nsyll == 1 and self._is_ambig:
                self._lstress = -0.5
            elif allow_ambig:
                self._lstress = self._stress_num - 1.0
            else:
                self._lstress = self._stress_num_binary - 1.0

            # print(self,self._lstress)
        else:
            for child in self:
                child.set_lstress()

    def set_phrasal_peaks(self):
        preterms = list(self.preterminals())
        for i2, w2 in enumerate(preterms):
            w1 = preterms[i2 - 1] if i2 else None
            w3 = preterms[i2 + 1] if (i2 + 1) < len(preterms) else None
            if np.isnan(w2._pstress):
                continue
            if w1 and not np.isnan(w1._pstress) and w1._pstress < w2._pstress:
                w1._phrasal_stress_valley = 1
                w1._phrasal_stress_peak = 0
                w1._pstrength = -1.0

                w2._phrasal_stress_peak = 1
                w2._phrasal_stress_valley = 0
                w2._pstrength = 1.0
            if w3 and not np.isnan(w3._pstress) and w3._pstress < w2._pstress:
                w3._phrasal_stress_valley = 1
                w3._phrasal_stress_peak = 0
                w3._pstrength = -1.0

                w2._phrasal_stress_peak = 1
                w2._phrasal_stress_valley = 0
                w2._pstrength = 1.0

    @property
    def prom_lstress(self):
        # return self.lstress + 1 if not np.isnan(self.lstress) else np.nan
        return self.lstress

    @property
    def preterms(self):
        return list(self.preterminals())

    @property
    def prom_pstress(self):
        return self.pstress
        # preterms = list(self.preterminals())
        # pstress_values = [preterm.pstress for preterm in preterms if not np.isnan(preterm.pstress)]
        # if not pstress_values:
        #     return np.nan
        # min_pstress = float(min(pstress_values))
        # max_pstress = max(pstress_values) - min_pstress
        # return (self.pstress - min_pstress) / max_pstress if max_pstress else np.nan

    @property
    def prom_tstress(self):
        return self.stress
        # preterms = list(self.preterminals())
        # stress_values = [preterm.stress for preterm in preterms if not np.isnan(preterm.stress)]
        # if not stress_values:
        #     return np.nan
        # min_stress = float(min(stress_values))
        # max_stress = max(stress_values) - min_stress
        # return (self.stress - min_stress) / max_stress if max_stress else np.nan

    @property
    def prom_pstrength(self):
        return self._pstrength

    @property
    def mtree_ishead(self):
        return self._phrasal_head

    @property
    def preterm_index(self):
        return self._preterm_index

    @property
    def is_preterm(self):
        return bool(self._preterm)

    @property
    def preterm_str(self):
        return self[0] if self.is_preterm else ""

    @property
    def wordtoken(self):
        return self._wordtoken

    @property
    def wordtype(self):
        return self.wordtoken.wordtype if self.wordtoken else None
    
    @property
    def wordform(self):
        return self.wordtype.children[0] if self.wordtype and self.wordtype.children else None

    @property
    def prefix_attrs(self):
        return nicedict({
            **self.attrs,
            **({} if not self.wordtoken else self.wordtoken.prefix_attrs),
            **({} if not self.wordtype else self.wordtype.prefix_attrs),
            **({} if not self.wordform else self.wordform.prefix_attrs),
        })
    
    @property
    def attrs(self):
        return {
            "syntax_cat": self._cat,
            "syntax_dep": self._dep,
            "syntax_stress": self.prom_tstress,
            "syntax_lstress": self.prom_lstress,
            "syntax_pstress": self.prom_pstress,
            "syntax_pstrength": self.prom_pstrength,
            # "syntax_phead": self.mtree_ishead,
        }

    @property
    def df(self):
        odf = pd.DataFrame(
            preterm.prefix_attrs 
            for preterm in self.preterminals()
        )
        return niceindex(odf)


def recurse_tree(tree, node_i=0, path=[]):
    o = []
    if not hasattr(tree, "node_i"):
        tree.node_i = node_i
        node_i += 1

    # path+=[f'{tree.node_i}-{tree.label}']
    if not tree.is_leaf():
        path += [f"{tree.node_i}-{tree.label}"]
        for x in tree.children:
            o += recurse_tree(x, node_i=node_i, path=list(path))
    else:
        o += [tuple(path)]
        path = []
    return o


def get_dtree_str(sent):
    o = []
    for dep in sent.dependencies:
        w1, rel, w2 = dep
        ostr = f"{rel}({w1.text}-{w1.id}, {w2.text}-{w2.id})"
        o += [ostr]
    return "\n".join(o)


def get_ctree_str(sent):
    return str(sent.constituency)


def get_treeparse_str(sent):
    ctree = get_ctree_str(sent)
    dtree = get_dtree_str(sent)
    return f"{ctree}\n\n{dtree}"


def get_mtree(sent, **kwargs):
    try:
        tree_str = get_treeparse_str(sent)
        depobj = DependencyTree.fromstring(tree_str)
        metrobj = SentenceTree.convert(depobj)
        return metrobj
    # except (IndexError,KeyError,AttributeError,ValueError) as e:
    except AssertionError as e:
        print("!!", e)
        pass


def find_phrasal_heads(self):
    for subtree in self:
        if type(subtree) != str:
            numsubs = len(subtree)
            firstsub, lastsub = subtree[0], subtree[-1]
            if numsubs > 1 and not subtree._preterm and lastsub._preterm:
                if lastsub._word_tok:
                    lastsub._phrasal_head = 1
                # print('phrasal head', str(subtree))
                for sub in subtree[:-1]:
                    if sub._word_tok:
                        sub._phrasal_head = 0
                    # print('not phrasal head', str(sub))
            find_phrasal_heads(subtree)
