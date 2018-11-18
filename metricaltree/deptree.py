#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Natural Language Toolkit: Updated interface to the Stanford Parser
#
# Copyright (C) 2015 Tim Dozat
# Author: Tim Dozat <tdozat@stanford.edu>
# Author of the Stanford Parser nltk code: Steven Xu <xxu@student.unimelb.edu.au>
#
# For license information, see LICENSE.TXT


from __future__ import unicode_literals

import tempfile
import os
import re
from subprocess import PIPE

import nltk
import nltk.data
from nltk import compat
from nltk import Tree
from nltk.internals import find_jar, find_jar_iter, config_java, java, _java_options

from nltk.parse.api import ParserI

_stanford_url = 'http://nlp.stanford.edu/software/lex-parser.shtml'

#***********************************************************************
# Dependency-augmented syntactic tree class
class DependencyTree(Tree):
    """"""

    _contractables = ("m", "s", "ll", "d", "nt", "re", "ve", "'m", "'s", "'ll", "'d", "n't", "'re", "'ve")
    _punctTags = ('.', ',', ':')

    #=====================================================================
    # Initialize
    def __init__(self, node, children=None, dep=None):
        """"""

        self._cat = node
        self._dep = dep
        self._preterm = False
        self._label = None
        super(DependencyTree, self).__init__(node, children)
        if len(self) == 1 and isinstance(self[0], compat.string_types):
            self._preterm = True
        self.set_label()

    #=====================================================================
    # Get the preterminal value of the node
    def preterminal(self):
        """"""

        return self._preterm

    #=====================================================================
    # Get the categorial value of the node
    def category(self):
        """"""

        return self._cat

    #=====================================================================
    # Get the dependency label of the node
    def dependency(self):
        """"""

        return self._dep

    #=====================================================================
    # Get the dependency labels of the leaf nodes
    def preterminals(self, leaves=True):
        """"""

        if self._preterm:
            if leaves:
                yield self
            else:
                yield self._label
        else:
            for child in self:
                for preterminal in child.preterminals(leaves=leaves):
                    yield preterminal

    #=====================================================================
    # Get the category labels of the leaf nodes
    def categories(self, leaves=True):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                yield (preterminal._cat, preterminal[0])
            else:
                yield preterminal._cat

    #=====================================================================
    # Get the dependency labels of the leaf nodes
    def dependencies(self, leaves=True):
        """"""

        for preterminal in self.preterminals(leaves=True):
            if leaves:
                yield (preterminal._dep, preterminal[0])
            else:
                yield preterminal._dep

    #=====================================================================
    # Reset the label of the node
    def set_label(self):
        """"""

        if self._dep is None:
            self._label = self._cat
        else:
            self._label = '%s/%s' % (self._cat, self._dep)

    #=====================================================================
    # Set the category of the node
    def set_category(self, cat):
        """"""

        self._cat = cat
        self.set_label()

    #=====================================================================
    # Set the dependency of this node
    def set_dep(self, dep):
        """"""

        self._dep = dep
        self.set_label()

    #=====================================================================
    # Set the dependency labels of all the leaf nodes
    def set_deps(self, deps):
        """"""

        preterminals = self.preterminals()
        for preterminal in preterminals:
            if re.match('\w', preterminal._cat[0]):
                preterminal.set_dep(deps.pop(0))

    #=====================================================================
    # Create a list of tuples from the preterminals
    def to_tuples(self):
        """"""

        for preterminal in self.preterminals():
            yield (preterminal[0], preterminal.category(), preterminal.dependency())

    #=====================================================================
    # Get the last preterminal
    def _get_last_preterm(self):
        """"""

        if self._preterm:
            return self
        else:
            return self[-1]._get_last_preterm()

    #=====================================================================
    # Pop the first contractables
    def _pop_first_contractable(self):
        """"""

        if self._preterm:
            if self[0] in _contractables:
                return self
            else:
                return None
        else:
            first_contractable = self[0]._pop_first_contractable()
            if self[0] == first_contractable or len(self[0]) == 0:
                self.children.pop(0)
                self.pop(0)
            return first_contractable

    #=====================================================================
    # Merge contractables
    def contract(self):
        """"""

        for child in self:
            if isinstance(child, DependencyTree):
                child.contract()
        i = len(self) - 2
        while i >= 0:
            child = self[i]
            last_preterm = child._get_last_preterm()
            j = i + 1
            while j < len(self):
                next_child = self[j]
                first_contractable = next_child._pop_first_contractable()
                if first_contractable is not None:
                    # Merge their cats/leaves
                    last_preterm._cat += '+'+first_contractable.category()
                    last_preterm[0] += first_goeswith[0]
                    last_preterm.children[0] += first_goeswith.children[0]
                    # Disown empty children
                    if len(next_child) == 0:
                        self.pop(j)
                    else:
                        break
                else:
                    break
            i -= 1

    #=====================================================================
    # Basically, read the output of the stanford parser
    @classmethod
    def fromstring(cls, s):
        """"""

        cTree, dGraph = s.split('\n\n')
        dTree = Tree.fromstring(cTree)
        dTree = DependencyTree.convert(dTree)
        deps = []
        dGraph = dGraph.split('\n')
        lastWord = ''
        for dep in dGraph:
            try:
                dep, thisWord = re.match('(.+?)\(.*?, (.*?)\)', dep).groups()
                if thisWord != lastWord:
                    deps.append(dep)
                    lastWord = thisWord
            except:
                print ''
        dTree.set_deps(deps)
        return dTree

    #=====================================================================
    # Convert between different subtypes of Dependency Trees
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
            if isinstance(tree, DependencyTree):
                return cls(tree._cat, children, tree._dep)
            else:
                return cls(tree._label, children)
        else:
            return tree

    #=====================================================================
    # Copy the tree
    def copy(self, deep=False):
        """"""

        if not deep:
            return type(self)(self._cat, self, dep=self._dep)
        else:
            return type(self).convert(self)

#***********************************************************************
# Updated interface to the Stanford Parser
class DependencyTreeParser(ParserI):
    """"""

    _MODEL_JAR_PATTERN = r'stanford-parser-(\d+)(\.(\d+))+-models\.jar'
    _EJML_JAR_PATTERN = r'ejml-(\d+)(\.(\d+))+\.jar'
    _JAR = 'stanford-parser.jar'

    #=====================================================================
    # Initialize
    def __init__(self,  path_to_jar=None, path_to_models_jar=None, path_to_ejml_jar=None, model_path='edu/stanford/nlp/models/parser/lexparser/englishPCFG.ser.gz', encoding='utf8', verbose=False, java_options='-mx3G'):
        """"""

        self._stanford_jar = find_jar(
          self._JAR, path_to_jar,
          env_vars=('STANFORD_PARSER',),
          searchpath=(), url=_stanford_url,
          verbose=verbose)

        # find the most recent model
        self._model_jar=max(
          find_jar_iter(
            self._MODEL_JAR_PATTERN, path_to_models_jar,
            env_vars=('STANFORD_MODELS',),
            searchpath=(), url=_stanford_url,
            verbose=verbose, is_regex=True),
          key=lambda model_name: re.match(self._MODEL_JAR_PATTERN, model_name))

        # find the most recent ejml
        self._ejml_jar=max(
          find_jar_iter(
            self._EJML_JAR_PATTERN, path_to_ejml_jar,
            env_vars=('STANFORD_EJML',),
            searchpath=(), url=_stanford_url,
            verbose=verbose, is_regex=True),
          key=lambda ejml_name: re.match(self._EJML_JAR_PATTERN, ejml_name))

        self.model_path = model_path
        self._encoding = encoding
        self.java_options = java_options

    #=====================================================================
    # Parse the output
    @staticmethod
    def _parse_trees_output(output_):
        """"""

        res = []
        cur_lines = []
        finished_tree = False
        for line in output_.splitlines(False):
            if line == '' and finished_tree:
                res.append(iter([DependencyTree.fromstring('\n'.join(cur_lines))]))
                cur_lines = []
                finished_tree = False
            else:
                cur_lines.append(line)
                if line == '' and not finished_tree:
                    finished_tree = True
        return iter(res)

    #=====================================================================
    # Use StanfordParser to parse a list of tokens
    def parse_sents(self, sentences, verbose=False):
        """"""

        cmd = [
          'edu.stanford.nlp.parser.lexparser.LexicalizedParser',
          '-model', self.model_path,
          '-sentences', 'newline',
          '-outputformat', 'penn,typedDependencies',
          '-tokenized',
          '-escaper', 'edu.stanford.nlp.process.PTBEscapingProcessor',
        ]
        return self._parse_trees_output(self._execute(
          cmd, '\n'.join(' '.join(sentence) for sentence in sentences), verbose))

    #=====================================================================
    # Use StanfordParser to parse a raw sentence
    def raw_parse(self, sentence, verbose=False):
        """"""

        return next(self.raw_parse_sents([sentence], verbose))

    #=====================================================================
    # Use StanfordParser to parse raw sentences
    def raw_parse_sents(self, sentences, verbose=False):
        """"""

        cmd = [
          'edu.stanford.nlp.parser.lexparser.LexicalizedParser',
          '-model', self.model_path,
          '-sentences', 'newline',
          '-outputFormat', 'penn,typedDependencies',
        ]
        return self._parse_trees_output(self._execute(cmd, '\n'.join(sentences), verbose))

    #=====================================================================
    # Use StanfordParser to parse a tagged sentence
    def tagged_parse(self, sentence, verbose=False):
        """"""

        return next(self.tagged_parse_sents([sentence], verbose))

    #=====================================================================
    # Use StanfordParser to parse tagged sentences
    def tagged_parse_sents(self, sentences, verbose=False):
        """"""

        tag_separator = '/'
        cmd = [
          'edu.stanford.nlp.parser.lexparser.LexicalizedParser',
          '-model', self.model_path,
          '-sentences', 'newline',
          '-outputFormat', 'penn,typedDependencies',
          '-tokenized',
          '-tagSeparator', tag_separator,
          '-tokenizerFactory', 'edu.stanford.nlp.process.WhitespaceTokenizer',
          '-tokenizerMethod', 'newCoreLabelTokenizerFactory',
        ]
        # We don't need to escape slashes as "splitting is done on the last instance of the character in the token"
        return self._parse_trees_output(self._execute(
          cmd, '\n'.join(' '.join(tag_separator.join(tagged) for tagged in sentence) for sentence in sentences), verbose))

    #=====================================================================
    # Execute
    def _execute(self, cmd, input_, verbose=False):
        """"""

        encoding = self._encoding
        cmd.extend(['-encoding', encoding])

        default_options = ' '.join(_java_options)

        # Configure java.
        config_java(options=self.java_options, verbose=verbose)

        # Windows is incompatible with NamedTemporaryFile() without passing in delete=False.
        with tempfile.NamedTemporaryFile(mode='wb', delete=False) as input_file:
            # Write the actual sentences to the temporary input file
            if isinstance(input_, compat.text_type) and encoding:
                input_ = input_.encode(encoding)
            input_file.write(input_)
            input_file.flush()

            cmd.append(input_file.name)

            # Run the tagger and get the output.
            stdout, stderr = java(cmd, classpath=(self._stanford_jar, self._model_jar, self._ejml_jar), stdout=PIPE, stderr=PIPE)
            stdout = stdout.decode(encoding)

        os.unlink(input_file.name)

        # Return java configurations to their default values.
        config_java(options=default_options, verbose=False)

        return stdout

#***********************************************************************
# Set up the module
def setup_module(module):
    """"""

    from nose import SkipTest

    try:
        StanfordParser(
          model_path='edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz'
        )
    except LookupError:
        raise SkipTest('doctests from nltk.parse.stanford are skipped because the stanford parser jar doesn\'t exist')

#***********************************************************************
# Test the module
if __name__ == '__main__':
    """"""

    import doctest
    import os

    doctest.testmod(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)

    import nltk.data
    sent_splitter = nltk.data.load('tokenizers/punkt/english.pickle')
    import codecs
    import cPickle as pkl
    import time
    import sys

    DATE = '2015-04-20'
    MODELS_VERSION = '3.5.2'
    EJML_VERSION = '0.23'

    os.environ['STANFORD_PARSER'] = 'StanfordLibrary/stanford-parser-full-%s/stanford-parser.jar' % DATE
    os.environ['STANFORD_MODELS'] = 'StanfordLibrary/stanford-parser-full-%s/stanford-parser-%s-models.jar' % (DATE, MODELS_VERSION)
    os.environ['STANFORD_EJML'] = 'StanfordLibrary/stanford-parser-full-%s/ejml-%s.jar' % (DATE, EJML_VERSION)
    parser = DependencyTreeParser(model_path='StanfordLibrary/stanford-parser-full-%s/edu/stanford/nlp/models/lexparser/englishRNN.ser.gz' % DATE)

    #=====================================================================
    basename = sys.argv[1].decode('utf-8')
    tuples = []
    i = 0
    lps = 0
    t_0 = time.time()
    lines = sum(1 for line in codecs.open('Text Book/Tolkien/%s.txt'%basename, encoding='utf-8'))
    try:
        with codecs.open('Text Book/Tolkien/%s.txt'%basename, encoding='utf-8') as f:
            for line in f:
                i += 1
                for sent in sent_splitter.tokenize(line.strip()):
                    trees = parser.raw_parse(sent)
                    for tree in trees:
                        tuples.append(list(tree.to_tuples()))
                t_i = time.time()
                lps = i/(t_i-t_0)
                lpm = lps*60
                lph = lpm*60
                etc = (lines-i)/lph
                etc_h = int(etc)
                etc_m = (etc-etc_h)*60
                print 'Line %d/%d: %.1f lpm, %dh %.1fm left         \r' % (i, lines, lpm, etc_h, etc_m),
                sys.stdout.flush()
    except:
        print 'Stopped while parsing line %d   ' % i
    pkl.dump(tuples, open('Pickle Jar/%s.pkl'%basename, 'w'), protocol=pkl.HIGHEST_PROTOCOL)
