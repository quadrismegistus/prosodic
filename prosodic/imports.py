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
DEFAULT_METER='default_english'
METER_MAX_S = 2
METER_MAX_W = 2
METER_RESOLVE_OPTIONALITY = True
PATH_PARSE_CACHE = os.path.join(PATH_HOME_DATA,'parse_cache.sqlitedict')
DEFAULT_CATEGORICAL_CONSTRAINTS = ['foot_size']
ESPEAK_PATHS=['/opt/homebrew/Cellar/espeak', '/usr/bin/espeak-ng']

# sys imports
import re
from typing import Optional
from collections import UserList
import warnings
warnings.filterwarnings('ignore')
import time
import itertools
from copy import copy
from functools import cached_property, lru_cache as cache, total_ordering
import string
import random
import textwrap

# patches
import builtins
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func): return func
    builtins.profile = profile

# non-sys imports
import ftfy
import numpy as np
import nltk
nltk.download('punkt',quiet=True)
import pandas as pd
pd.options.display.width=200
from langdetect import detect as detect_lang
from loguru import logger
logger.remove()
logger.add(
    sink=sys.stderr,
    format=LOG_FORMAT, 
    level=LOG_LEVEL
)
from tqdm import tqdm
from multiset import Multiset

# local imports
from .utils import *
from .ents import *
from .tokenizers import *
from .texts import *
from .lines import *
from .langs import *
from .words import *
from .syllables import *
from .phonemes import *
from .parsing import *




sonnet="""
Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,
Will play the tyrants to the very same
And that unfair which fairly doth excel;
For never-resting time leads summer on
To hideous winter, and confounds him there;
Sap checked with frost, and lusty leaves quite gone,
Beauty o’er-snowed and bareness every where:
Then were not summer’s distillation left,
A liquid prisoner pent in walls of glass,
Beauty’s effect with beauty were bereft,
Nor it, nor no remembrance what it was:
But flowers distill’d, though they with winter meet,
Leese but their show; their substance still lives sweet.
"""