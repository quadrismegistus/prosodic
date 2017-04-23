#!/usr/bin/env python # -*- coding: utf-8 -*-
#8/31/15: 1200-1600
#9/06/15: 1330-1945
#9/08/15: 1130-1430
#9/15 3:30-6:30 <- taken care of?
#11/25 eh, like 30 mins

import os
from collections import defaultdict
import cPickle as pkl
import numpy as np
#import pandas as pd
#import matplotlib.pyplot as plt
import codecs
import nltk
from nltk import compat
from nltk.tree import Tree
import nltk.data
from deptree import DependencyTree, DependencyTreeParser
import re,time

DATE = '2015-04-20'
MODELS_VERSION = '3.5.2'
EJML_VERSION = '0.23'

DIR_ROOT = '.'
sylcmu = None

INFO_DO_NOT_STORE = ['contour','sent','nsyll','nseg','seg','nstress','word']


def set_paths(dir_root='.'):
    global DIR_ROOT,sylcmu
    DIR_ROOT = dir_root
    os.environ['STANFORD_PARSER'] = os.path.join(dir_root,'Stanford Library/stanford-parser-full-%s/stanford-parser.jar' % DATE)
    os.environ['STANFORD_MODELS'] = os.path.join(dir_root,'Stanford Library/stanford-parser-full-%s/stanford-parser-%s-models.jar' % (DATE, MODELS_VERSION))
    os.environ['STANFORD_EJML']   = os.path.join(dir_root,'Stanford Library/stanford-parser-full-%s/ejml-%s.jar' % (DATE, EJML_VERSION))

    """
    then=time.time()
    print '>> loading CMU for MetricalParser...'
    sylcmu = pkl.load(open(os.path.join(dir_root,'Pickle Jar/sylcmu.pkl')))
    now=time.time()
    print '>> done loading in',round(now-then,2),'seconds'
    """
    sylcmu = {}


sent_splitter = nltk.data.load('tokenizers/punkt/english.pickle')

#***********************************************************************
# Multiprocessing worker
def parse_worker(q):
    """"""

    parser = DependencyTreeParser(model_path='Stanford Library/stanford-parser-full-%s/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz' % DATE)
    parser = MetricalTreeParser(parser)
    for filename in iter(q.get, 'STOP'):
        print 'Working on %s...' % filename
        sents = []
        with codecs.open(filename, encoding='utf-8') as f:
            for line in f:
                sents.extend(pause_splitter(line))
        df = parser.stats_raw_parse_sents(sents, arto=True)
        df.to_csv(codecs.open('%s.csv' % filename, 'w', encoding='utf-8'), index=False)
        print 'Finished with %s.' % filename
    return True

# Return parser
def return_parser(dir_root):
    model_path='Stanford Library/stanford-parser-full-%s/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz' % DATE
    fnfn=os.path.join(dir_root,model_path)
    parser = DependencyTreeParser(model_path=fnfn)
    parser = MetricalTreeParser(parser)
    return parser

#***********************************************************************
# Split a text on certain punctuation
def pause_splitter(s):
    """"""

    s = s.strip()
    s = re.sub('([:;]|--+)', '\g<1>\n', s)
    s = s.split('\n')
    s = [sent for sents in s for sent in sent_splitter.tokenize(sents)]
    return s

def pause_splitter_tokens(tokens,split_by={':',';','--',u'—',u'–'}):
    """"""
    sents=[]
    sent=[]
    for tok in tokens:
        sent+=[tok]
        if tok in split_by:
            if sent: sents+=[sent]
            sent=[]
    if sent: sents+=[sent]
    return sents

def split_sentences_from_tokens(l):
    return sent_splitter.sentences_from_tokens(l)

#***********************************************************************
# Metrical Tree class
class MetricalTree(DependencyTree):
    """"""

    _unstressedWords = ('it',)
    _unstressedTags  = ('CC', 'PRP$', 'TO', 'UH', 'DT')
    _unstressedDeps  = ('det', 'expl', 'cc', 'mark')
    _ambiguousWords = ('this', 'that', 'these', 'those')
    _ambiguousTags  = ('MD', 'IN', 'PRP', 'WP$', 'PDT', 'WDT', 'WP', 'WRB')
    _ambiguousDeps  = ('cop', 'neg', 'aux', 'auxpass')
    _stressedWords = tuple()

    #=====================================================================
    # Initialize
    def __init__(self, node, children, dep=None, lstress=0, pstress=np.nan, stress=np.nan):
        """"""

        self._lstress = lstress
        self._pstress = pstress
        self._stress = stress
        super(MetricalTree, self).__init__(node, children, dep)
        self.set_label()
        if self._preterm:
            if self[0].lower() in sylcmu:
                syll_info = sylcmu[self[0].lower()]
                self._seg = syll_info[0]
                self._nsyll = len(syll_info[1])
                self._nstress = len(filter(lambda x: x[1] in ('P', 'S'), syll_info[1]))
            else:
                self._seg = None
                self._nsyll = np.nan
                self._nstress = np.nan

    #=====================================================================
    # Get the lexical stress of the node
    def lstress(self):
        """"""

        return self._lstress

    #=====================================================================
    # Get the phrasal stress of the node
    def pstress(self):
        """"""

        return self._pstress

    #=====================================================================
    # Get the stress of the node
    def stress(self):
        """"""

        return self._stress

    #=====================================================================
    # Get the segments
    def seg(self):
        """"""

        return self._seg if self._seg is not None else []

    #=====================================================================
    # Get the number of segments
    def nseg(self):
        """"""

        return len(self._seg) if self._seg is not None else np.nan

    #=====================================================================
    # Get the number of syllables
    def nsyll(self):
        """"""

        return self._nsyll

    #=====================================================================
    # Get the number of stresses
    def nstress(self):
        """"""

        return self._nstress

    #=====================================================================
    # Get the lexical stress of the leaf nodes
    def lstresses(self, leaves=True):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                yield (preterminal._lstress, preterminal[0])
            else:
                yield preterminal._lstress

    #=====================================================================
    # Get the phrasal stress of the leaf nodes
    def pstresses(self, leaves=True):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                yield (preterminal._pstress, preterminal[0])
            else:
                yield preterminal._pstress

    #=====================================================================
    # Get the lexical stress of the leaf nodes
    def stresses(self, leaves=True, arto=False):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                if arto:
                    if preterminal._stress is None:
                        yield (None, preterminal[0])
                    elif preterminal._lstress == -1:
                        yield (0, preterminal[0])
                    else:
                        yield (-(preterminal._stress-1), preterminal[0])
                else:
                    yield (preterminal._stress, preterminal[0])
            else:
                if arto:
                    if preterminal._stress is None:
                        yield None
                    elif preterminal._lstress == -1:
                        yield 0
                    else:
                        yield -(preterminal._stress-1)
                else:
                    yield preterminal._stress

    #=====================================================================
    # Get the number of syllables of the leaf nodes
    def nsylls(self, leaves=True):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                yield (preterminal._nsyll, preterminal[0])
            else:
                yield preterminal._nsyll

    #=====================================================================
    # Set the lexical stress of the node
    def set_lstress(self):
        """"""

        if self._preterm:
            if self[0].lower() in super(MetricalTree, self)._contractables:
                self._lstress = np.nan
            elif self._cat in super(MetricalTree, self)._punctTags:
                self._lstress = np.nan

            elif self[0].lower() in MetricalTree._unstressedWords:
                self._lstress = -1
            elif self[0].lower() in MetricalTree._ambiguousWords:
                self._lstress = -.5
            elif self[0].lower() in MetricalTree._stressedWords:
                self._lstress = 0

            elif self._cat in MetricalTree._unstressedTags:
                self._lstress = -1
            elif self._cat in MetricalTree._ambiguousTags:
                self._lstress = -.5

            elif self._dep in MetricalTree._unstressedDeps:
                self._lstress = -1
            elif self._dep in MetricalTree._ambiguousDeps:
                self._lstress = -.5

            else:
                self._lstress = 0

            if self[0].lower() == 'that' and (self._cat == 'DT' or self._dep == 'det'):
                self._lstress = -.5
        else:
            for child in self:
                child.set_lstress()
        self.set_label()

    #=====================================================================
    # Set the phrasal stress of the tree
    def set_pstress(self):
        """"""

        # Basis
        if self._preterm:
            try: assert self._lstress != -.5
            except: raise ValueError('The tree must be disambiguated before assigning phrasal stress')
            self._pstress = self._lstress
        else:
            # Recurse
            for child in self:
                child.set_pstress()
            assigned = False
            # Noun compounds (look for sequences of N*)
            if self._cat == 'NP':
                skipIdx = None
                i = len(self)
                for child in self[::-1]:
                    i -= 1
                    if child._cat.startswith('NN'):
                        if not assigned and skipIdx is None:
                            skipIdx = i
                            child._pstress = -1
                            child.set_label()
                        elif not assigned:
                            child._pstress = 0
                            child.set_label()
                            assigned = True
                        else:
                            child._pstress = -1
                            child.set_label()
                    elif assigned:
                        child._pstress = -1
                        child.set_label()
                    else:
                        if not assigned and skipIdx is not None:
                            self[skipIdx]._pstress = 0
                            self[skipIdx].set_label()
                            assigned = True
                            child._pstress = -1
                            child.set_label()
                        else:
                            break
                if not assigned and skipIdx is not None:
                    self[skipIdx]._pstress = 0
                    self[skipIdx].set_label()
                    assigned = True
            # Everything else
            if not assigned:
                for child in self[::-1]:
                    if not assigned and child._pstress == 0:
                        assigned = True
                    elif not np.isnan(child._pstress):
                        child._pstress = -1
                        child.set_label()
            if not assigned:
                self._pstress = -1
            else:
                self._pstress = 0
        self.set_label()

    #=====================================================================
    # Set the total of the tree
    def set_stress(self, stress=0):
        """"""

        self._stress = self._lstress + self._pstress + stress
        if not self._preterm:
            for child in self:
                child.set_stress(self._stress)
        self.set_label()

    #=====================================================================
    # Reset the label of the node (cat < dep < lstress < pstress < stress
    def set_label(self):
        """"""

        if self._stress is not np.nan:
            self._label = '%s/%s' % (self._cat, self._stress)
        elif self._pstress is not np.nan:
            self._label = '%s/%s' % (self._cat, self._pstress)
        elif self._lstress is not np.nan:
            self._label = '%s/%s' % (self._cat, self._lstress)
        elif self._dep is not None:
            self._label = '%s/%s' % (self._cat, self._dep)
        else:
            self._label = '%s' % self._cat

    #=====================================================================
    # Convert between different subtypes of Metrical Trees
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
            children = [cls.convert(child) for child in tree]
            if isinstance(tree, MetricalTree):
                return cls(tree._cat, children, tree._dep, tree._lstress)
            elif isinstance(tree, DependencyTree):
                return cls(tree._cat, children, tree._dep)
            else:
                return cls(tree._label, children)
        else:
            return tree

    #=====================================================================
    # Approximate the number of ambiguous parses
    def ambiguity(self, stress_polysyll=False):
        """"""

        nambig = 0
        for preterminal in self.preterminals():
            if preterminal.lstress() == -.5:
                if not stress_polysyll or (preterminal.nsyll() == 1):
                    nambig += 1
        return nambig

    #=====================================================================
    # Generate all possible trees
    # Syll=True sets all polysyllabic words to stressed
    def ambiguate(self, stress_polysyll=False):
        """"""

        if self._preterm:
            if self._lstress != -.5:
                return [self.copy()]
            else:
                alts = []
                if not stress_polysyll or self._nsyll == 1:
                    self._lstress = -1
                    alts.append(self.copy())
                self._lstress = 0
                alts.append(self.copy())
                self._lstress = -.5
                return alts
        else:
            alts = [[]]
            for child in self:
                child_alts = child.disambiguate(syll)
                for i in xrange(len(alts)):
                    alt = alts.pop(0)
                    for child_alt in child_alts:
                        alts.append(alt + [child_alt])
            return [MetricalTree(self._cat, alt, self._dep) for alt in alts]

    #=====================================================================
    # Disambiguate a tree with the maximal stressed pattern
    def max_stress_disambiguate(self):
        """"""

        if self._preterm:
            if self._lstress != -.5:
                return [self.copy()]
            else:
                alts = []
                self._lstress = 0
                alts.append(self.copy())
                self._lstress = -.5
                return alts
        else:
            alts = [[]]
            for child in self:
                child_alts = child.max_stress_disambiguate()
                for i in xrange(len(alts)):
                    alt = alts.pop(0)
                    for child_alt in child_alts:
                        alts.append(alt + [child_alt])
            return [MetricalTree(self._cat, alt, self._dep) for alt in alts]

    #=====================================================================
    # Disambiguate a tree with the minimal stressed pattern
    def min_stress_disambiguate(self, stress_polysyll=False):
        """"""

        if self._preterm:
            if self._lstress != -.5:
                return [self.copy()]
            else:
                alts = []
                if not stress_polysyll or self._nsyll == 1:
                    self._lstress = -1
                else:
                    self._lstress = 0

                alts.append(self.copy())
                self._lstress = -.5
                return alts
        else:
            alts = [[]]
            for child in self:
                child_alts = child.min_stress_disambiguate(stress_polysyll)
                for i in xrange(len(alts)):
                    alt = alts.pop(0)
                    for child_alt in child_alts:
                        alts.append(alt + [child_alt])
            return [MetricalTree(self._cat, alt, self._dep) for alt in alts]

    #=====================================================================
    # Copy the tree
    def copy(self, deep=False):
        """"""

        if not deep:
            return type(self)(self._cat, self, dep=self._dep, lstress=self._lstress)
        else:
            return type(self).convert(self)

#***********************************************************************
# Parser for Metrical Trees
class MetricalTreeParser:
    """"""

    #=====================================================================
    # Initialize
    def __init__(self, deptreeParser=None):
        """"""

        if deptreeParser is None:
            sys.stderr.write('No deptreeParser provided, defaulting to PCFG\n')
            deptreeParser = 'PCFG'
        if isinstance(deptreeParser, compat.string_types):
            deptreeParser = DependencyTreeParser(model_path='stanford-parser-full-%s/edu/stanford/nlp/models/lexparser/english%s.ser.gz' % (DATE, deptreeParser))
        elif not isinstance(deptreeParser, DependencyTreeParser):
            raise ValueError('Provided an invalid dependency tree parser')
        self.deptreeParser = deptreeParser

    #=====================================================================
    # Use StanfordParser to parse a list of tokens
    def dep_parse_sents(self, sentences, verbose=False):
        """"""

        return self.deptreeParser.parse_sents(sentences, verbose)

    #=====================================================================
    # Use StanfordParser to parse a raw sentence
    def dep_raw_parse(self, sentence, verbose=False):
        """"""

        return self.deptreeParser.raw_parse(sentence, verbose)

    #=====================================================================
    # Use StanfordParser to parse multiple raw sentences
    def dep_raw_parse_sents(self, sentences, verbose=False):
        """"""

        return self.deptreeParser.raw_parse_sents(sentences, verbose)

    #=====================================================================
    # Use StanfordParser to parse multiple preprocessed sentences
    def dep_tagged_parse_sent(self, sentence, verbose=False):
        """"""

        return self.deptreeParser.tagged_parse_sent(sentence, verbose)

    #=====================================================================
    # Use StanfordParser to parse multiple preprocessed sentences
    def dep_tagged_parse_sents(self, sentences, verbose=False):
        """"""

        return self.deptreeParser.tagged_parse_sents(sentences, verbose)

    #=====================================================================
    # Parse a list of tokens into lexical Metrical Trees
    def lex_parse_sents(self, sentences, verbose=False):
        """"""

        sentences = self.dep_parse_sents(sentences, verbose)
        for tree in sentences:
            for t in tree:
                t = MetricalTree.convert(t)
                t.set_lstress()
                yield t

    #=====================================================================
    # Parse a raw sentence into lexical Metrical Trees
    def lex_raw_parse(self, sentence, verbose=False):
        """"""

        sentence = self.dep_raw_parse(sentence, verbose)
        for t in sentence:
            t = MetricalTree.convert(t)
            t.set_lstress()
            yield t

    #=====================================================================
    # Parse a string into lexical Metrical Trees
    def lex_raw_parse_sents(self, sentences, verbose=False):
        """"""

        sentences = self.dep_raw_parse_sents(sentences, verbose)
        for tree in sentences:
            for t in tree:
                t = MetricalTree.convert(t)
                t.set_lstress()
                yield t

    #=====================================================================
    # Parse a tagged sentence into lexical Metrical Trees
    def lex_tagged_parse(self, sentence, verbose=False):
        """"""

        sentence = self.dep_tagged_parse(sentence, verbose)
        for t in sentence:
            t = MetricalTree.convert(t)
            t.set_lstress()
            yield t

    #=====================================================================
    # Parse a raw sentence into lexical Metrical Trees
    def lex_tagged_parse_sents(self, sentences, verbose=False):
        """"""

        sentences = self.dep_tagged_parse_sents(sentences, verbose)
        for tree in sentences:
            for t in tree:
                t = MetricalTree.convert(t)
                t.set_lstress()
                yield t

    #=====================================================================
    # Parse a list of tokens into phrasal Metrical Trees
    def phr_parse_sents(self, sentences, stress_polysyll=False, verbose=True):
        """"""

        for t in self.lex_parse_sents(sentences, verbose):
            trees = t.disambiguate(stress_polysyll)
            for tree in trees:
                tree.set_pstress()
                tree.set_stress()
            yield trees

    #=====================================================================
    # Parse a string into phrasal Metrical Trees
    def phr_raw_parse(self, sentences, stress_polysyll=False, verbose=True):
        """"""

        for t in self.lex_raw_parse(sentences, verbose):
            trees = t.disambiguate(stress_polysyll)
            for tree in trees:
                tree.set_pstress()
                tree.set_stress()
            yield trees

    #=====================================================================
    # Parse a list of strings into phrasal Metrical Trees
    def phr_raw_parse_sents(self, sentences, stress_polysyll=False, verbose=True):
        """"""

        for t in self.lex_raw_parse_sents(sentences, verbose):
            trees = t.disambiguate(stress_polysyll)
            for tree in trees:
                tree.set_pstress()
                tree.set_stress()
            yield trees

    #=====================================================================
    # Parse a list of tagged strings into phrasal Metrical Trees
    def phr_tagged_parse(self, sentences, stress_polysyll=False, verbose=True):
        """"""

        for t in self.lex_tagged_parse(sentences, verbose):
            trees = t.disambiguate(stress_polysyll)
            for tree in trees:
                tree.set_pstress()
                tree.set_stress()
            yield trees

    #=====================================================================
    # Parse a list of strings into phrasal Metrical Trees
    def phr_tagged_parse_sents(self, sentences, stress_polysyll=False, verbose=True):
        """"""

        for t in self.lex_tagged_parse_sents(sentences, verbose):
            trees = t.disambiguate(stress_polysyll)
            for tree in trees:
                tree.set_pstress()
                tree.set_stress()
            yield trees

    #=============================================================
    def get_stats(self, generator, arto=False,format_pandas=False):
        """"""

        data = defaultdict(list)
        i = 0
        for t in generator:
            i += 1
            ambig1 = t.ambiguity(stress_polysyll=False)
            ambig2 = t.ambiguity(stress_polysyll=True)
            tree1 = t.max_stress_disambiguate()[0]
            tree1.set_pstress()
            tree1.set_stress()
            tree2a = t.min_stress_disambiguate(stress_polysyll=True)[0]
            tree2a.set_pstress()
            tree2a.set_stress()
            tree2b = t.min_stress_disambiguate(stress_polysyll=False)[0]
            tree2b.set_pstress()
            tree2b.set_stress()

            j = 0
            preterms1 = list(tree1.preterminals())
            min1 = float(min([preterm.stress() for preterm in preterms1 if not np.isnan(preterm.stress())]))
            max1 = max([preterm.stress() for preterm in preterms1 if not np.isnan(preterm.stress())]) - min1
            preterms2a = list(tree2a.preterminals())
            min2a = float(min([preterm.stress() for preterm in preterms2a if not np.isnan(preterm.stress())]))
            max2a = max([preterm.stress() for preterm in preterms2a if not np.isnan(preterm.stress())]) - min2a
            preterms2b = list(tree2b.preterminals())
            min2b = float(min([preterm.stress() for preterm in preterms2b if not np.isnan(preterm.stress())]))
            max2b = max([preterm.stress() for preterm in preterms2b if not np.isnan(preterm.stress())]) - min2b
            preterms_raw = list(t.preterminals())
            minmean = float(min([np.mean([preterm1.stress(), preterm2a.stress(), preterm2b.stress()]) for preterm1, preterm2a, preterm2b in zip(preterms1, preterms2a, preterms2b) if not np.isnan(preterm1.stress())]))
            maxmean = max([np.mean([preterm1.stress(), preterm2a.stress(), preterm2b.stress()]) for preterm1, preterm2a, preterm2b in zip(preterms1, preterms2a, preterms2b) if not np.isnan(preterm1.stress())]) - minmean
            sent = ' '.join([preterm[0] for preterm in preterms_raw])
            sentlen = len(preterms_raw)
            for preterm1, preterm2a, preterm2b, preterm_raw in zip(preterms1, preterms2a, preterms2b, preterms_raw):
                j += 1
                data['widx'].append(j)
                data['norm_widx'].append(float(j) / sentlen if sentlen else np.nan)
                data['word'].append(preterm1[0])
                if preterm_raw._lstress == 0:
                    data['lexstress'].append('yes')
                elif preterm_raw._lstress == -.5:
                    data['lexstress'].append('ambig')
                elif preterm_raw._lstress == -1:
                    data['lexstress'].append('no')
                else:
                    data['lexstress'].append('???')
                data['seg'].append(' '.join(preterm1.seg()))
                data['nseg'].append(preterm1.nseg())
                data['nsyll'].append(preterm1.nsyll())
                data['nstress'].append(preterm1.nstress())
                data['pos'].append(preterm1.category())
                data['dep'].append(preterm1.dependency())
                if arto:
                    data['m1'].append(-(preterm1.stress()-1))
                    data['m2a'].append(-(preterm2a.stress()-1))
                    data['m2b'].append(-(preterm2b.stress()-1))
                    data['mean'].append(-(np.mean([preterm1.stress(), preterm2a.stress(), preterm2b.stress()])-1))
                else:
                    data['m1'].append(preterm1.stress())
                    data['m2a'].append(preterm2a.stress())
                    data['m2b'].append(preterm2b.stress())
                    data['mean'].append(np.mean([preterm1.stress(), preterm2a.stress(), preterm2b.stress()]))
                data['norm_m1'].append((preterm1.stress()-min1)/max1 if max1 else np.nan)
                data['norm_m2a'].append((preterm2a.stress()-min2a)/max2a if max2a else np.nan)
                data['norm_m2b'].append((preterm2b.stress()-min2b)/max2b if max2b else np.nan)
                data['norm_mean'].append((np.mean([preterm1.stress(), preterm2a.stress(), preterm2b.stress()])-minmean)/maxmean if maxmean else np.nan)
                data['sidx'].append(i)
                data['sent'].append(sent)
                data['ambig_words'].append(ambig1)
                data['ambig_monosyll'].append(ambig2)
            data['contour'].extend([' '.join(str(x) for x in data['mean'][-(j):])]*j)

        if format_pandas:
            for k, v in data.iteritems():
                data[k] = pd.Series(v)
            df=pd.DataFrame(data, columns=['widx', 'norm_widx', 'word', 'seg', 'lexstress',
                                               'nseg', 'nsyll', 'nstress',
                                               'pos', 'dep',
                                               'm1', 'm2a', 'm2b', 'mean',
                                               'norm_m1', 'norm_m2a', 'norm_m2b', 'norm_mean',
                                               'sidx', 'sent', 'ambig_words', 'ambig_monosyll',
                                               'contour'])
            return df

        keys=data.keys()
        old=[]
        num_rows=len(data[keys[0]])
        for i_row in range(num_rows):
            dx={}
            for k in keys:
                dx[k]=data[k][i_row]
            old+=[dx]

        return old

    #=====================================================================
    # Parse a list of tokens into phrasal Metrical Trees
    def stats_parse_sents(self, sentences, arto=False, verbose=True):
        """"""

        return self.get_stats(self.lex_parse_sents(sentences, verbose), arto=arto)

    #=====================================================================
    # Parse a string into phrasal Metrical Trees
    def stats_raw_parse(self, sentence, arto=False, verbose=True):
        """"""

        return self.get_stats(self.lex_raw_parse(sentence, verbose), arto=arto)

    #=====================================================================
    # Parse a string into phrasal Metrical Trees
    def stats_raw_parse_sents(self, sentences, arto=False, verbose=True):
        """"""

        return self.get_stats(self.lex_raw_parse_sents(sentences, verbose), arto=arto)

    #=====================================================================
    # Parse a list of tagged tokens into phrasal Metrical Trees
    def stats_tagged_parse(self, sentence, arto=False, verbose=True):
        """"""

        return self.get_stats(self.lex_tagged_parse(sentence, verbose), arto=arto)

    #=====================================================================
    # Parse a list of tagged tokens into phrasal Metrical Trees
    def stats_tagged_parse_sents(self, sentences, arto=False, verbose=True):
        """"""

        return self.get_stats(self.lex_tagged_parse_sents(sentence, verbose), arto=arto)

#***********************************************************************
# Test the module
if __name__ == '__main__':
    """"""

    import glob
    import re
    import multiprocessing as mp
    import sys

    files = sys.argv[1:]
    try:
        workers = mp.cpu_count()
    except:
        workers = 1

    q = mp.Queue()
    for filename in files:
        q.put(filename)
    for worker in xrange(workers):
        q.put('STOP')
    processes = []
    for worker in xrange(workers):
        process = mp.Process(target=parse_worker, args=(q,))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()
    print 'Done!'
