import warnings
warnings.filterwarnings("ignore")
import pytest
from prosodic import TextModel
from prosodic.sents.sents import SentenceList, Sentence
from prosodic.sents.trees import SentenceTree
from prosodic.sents.grids import SentenceGrid
from prosodic.sents.syntax import get_nlp, get_nlp_doc

# Tests for sents.py
def test_sentence_list_from_wordtokens():
    text_model = TextModel("Hello world. This is a test.")
    wordtokens = text_model.wordtokens
    sent_list = SentenceList.from_wordtokens(wordtokens)
    assert len(sent_list) == 2
    assert isinstance(sent_list[0], Sentence)
    assert len(sent_list[0]) == 3
    assert len(sent_list[1]) == 5

# Tests for trees.py
def test_sentence_tree_from_sent():
    text_model = TextModel("Hello world.")
    sent = text_model.sents[0]
    tree = SentenceTree.from_sent(sent)
    assert isinstance(tree, SentenceTree)
    assert len(list(tree.preterminals())) == 3
    assert tree.sent == sent

# Tests for grids.py
def test_sentence_grid_from_wordtokens():
    text_model = TextModel("Hello world.")
    wordtokens = text_model.wordtokens
    grid = SentenceGrid.from_wordtokens(wordtokens)
    assert isinstance(grid, SentenceGrid)
    assert len(grid) == 3
    assert grid.wordtokens == wordtokens

# Tests for syntax.py
def test_get_nlp():
    nlp = get_nlp(lang="en")
    assert nlp is not None
    assert hasattr(nlp, 'procstr')

def test_get_nlp_doc():
    doc = get_nlp_doc("This is a test sentence.")
    assert doc is not None
    assert len(doc.sentences) == 1
    assert len(doc.sentences[0].words) == 5

# Additional test for SentenceTree properties
def test_sentence_tree_properties():
    text_model = TextModel("The quick brown fox jumps over the lazy dog.")
    sent = text_model.sents[0]
    tree = SentenceTree.from_sent(sent)
    
    assert tree.df is not None
    assert len(tree.df) == 10  # Number of words in the sentence
    assert 'syntax_cat' in tree.df.columns
    assert 'syntax_dep' in tree.df.columns
    assert 'syntax_stress' in tree.df.columns

# Additional test for SentenceGrid properties
def test_sentence_grid_properties():
    text_model = TextModel("The quick brown fox jumps over the lazy dog.")
    wordtokens = text_model.wordtokens
    grid = SentenceGrid.from_wordtokens(wordtokens)
    
    assert grid.df is not None
    assert len(grid.df) == 10  # Number of words in the sentence

    df=grid.df.reset_index()
    assert 'grid_i' in df.columns
    assert 'syntax_stress' in df.columns
    assert 'wordtype_txt' in df.columns

# Run the tests
if __name__ == "__main__":
    pytest.main([__file__])
