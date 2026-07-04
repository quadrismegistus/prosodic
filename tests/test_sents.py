import warnings
warnings.filterwarnings("ignore")
import pytest
from prosodic import TextModel
from prosodic.sents.sents import SentenceList, Sentence


# Tests for sents.py
def test_sentence_list_from_wordtokens():
    text_model = TextModel("Hello world. This is a test.")
    wordtokens = text_model.wordtokens
    sent_list = SentenceList.from_wordtokens(wordtokens)
    assert len(sent_list) == 2
    assert isinstance(sent_list[0], Sentence)
    assert len(sent_list[0]) == 3
    assert len(sent_list[1]) == 5


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__])
