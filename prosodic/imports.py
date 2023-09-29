import os,sys
PATH_HERE = os.path.abspath(os.path.dirname(__file__))
PATH_REPO = os.path.dirname(PATH_HERE)
PATH_MTREE = os.path.join(PATH_REPO, 'metricaltree')
sys.path.append(PATH_MTREE)
DASHES=['--','–','—']
REPLACE_DASHES = True
PSTRESS_THRESH_DEFAULT = 2
TOKENIZER=r'[^\s+]+'
SEPS_PHRASE=set(',:;–—()[].!?"“”’‘')
SEP_STANZA='\n\n'
SEP_PARA='\n\n'
SEP_LINE='\n'
DEFAULT_PARSE_MAXSEC=30
DEFAULT_LINE_LIM=None
DEFAULT_PROCESSORS={'tokenize':'combined'}
MAX_SYLL_IN_PARSE_UNIT=14
MIN_SYLL_IN_PARSE_UNIT=None
MIN_WORDS_IN_PHRASE=2
MAX_WORDS_IN_PHRASE=15
DEFAULT_LANG='en'


# sys imports
import re
from typing import Optional

# non-sys imports
from functools import cached_property, lru_cache as cache
import ftfy
import nltk
import pandas as pd
from langdetect import detect as detect_lang

# local imports
from .utils import *
from .ents import *
from .tokenizers import *
from .texts import *
from .lines import *
from .words import *