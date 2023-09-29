import os,sys
PATH_HERE = os.path.abspath(os.path.dirname(__file__))
PATH_REPO = os.path.dirname(PATH_HERE)
PATH_REPO_DATA = os.path.join(PATH_REPO,'data')
PATH_DICTS = os.path.join(PATH_REPO_DATA, 'dicts')
PATH_HOME = os.path.expanduser('~/prosodic_data')
PATH_HOME_DATA = os.path.join(PATH_HOME, 'data')
os.makedirs(PATH_HOME_DATA, exist_ok=True)


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
LOG_FORMAT = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <cyan>{function}</cyan> | <level>{message}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan>'
LOG_LEVEL = 10


# sys imports
import re
from typing import Optional
import warnings
warnings.filterwarnings('ignore')

# non-sys imports
from functools import cached_property, lru_cache as cache
import ftfy
import nltk
import pandas as pd
from langdetect import detect as detect_lang
from loguru import logger
logger.remove()
logger.add(
    sink=sys.stderr,
    format=LOG_FORMAT, 
    level=LOG_LEVEL
)

# local imports
from .utils import *
from .ents import *
from .tokenizers import *
from .texts import *
from .lines import *
from .words import *
from .langs import *
from .syllables import *
from .phonemes import *