import os, sys
from logmap import logmap, logger

logmap.enable()
from base64 import b64decode, b64encode
from functools import wraps
from pprint import pprint, pformat
import orjson
import json
from multiset import Multiset
from tqdm import tqdm
import logging
from langdetect import detect as detect_lang
import pandas as pd
import nltk
import numpy as np
import ftfy
import builtins
import multiprocessing as mp
from collections import deque
import requests
import textwrap
import random
import string
from functools import cached_property, lru_cache as cache, total_ordering
from copy import copy
import itertools
import zlib
import time
import warnings
from collections import UserList, Counter, defaultdict
from typing import Optional
import re
import os
import sys
from contextlib import contextmanager

PATH_HERE = os.path.abspath(os.path.dirname(__file__))
PATH_REPO = os.path.dirname(PATH_HERE)
PATH_WEB = os.path.join(PATH_REPO, "prosodic", "web")
PATH_REPO_DATA = os.path.join(PATH_REPO, "data")
PATH_DICTS = os.path.join(PATH_REPO_DATA, "dicts")
PATH_HOME = os.path.expanduser("~/prosodic_data")
PATH_HOME_DATA = os.path.join(PATH_HOME, "data")
PATH_HOME_DATA_CACHE = os.path.join(PATH_HOME_DATA, "cache")
os.makedirs(PATH_HOME_DATA, exist_ok=True)

USE_CACHE = False
USE_REDIS = False
HASHSTR_LEN = None
DEFAULT_NUM_PROC = None
REDIS_HOST = "212.227.240.128"

PATH_MTREE = os.path.join(PATH_REPO, "metricaltree")
sys.path.append(PATH_MTREE)
DASHES = ["--", "–", "—"]
REPLACE_DASHES = True
PSTRESS_THRESH_DEFAULT = 2
TOKENIZER = r"[^\s+]+"
SEPS_PHRASE = set(',:;–—()[].!?"“”’‘')
SEP_STANZA = "\n\n"
SEP_PARA = "\n\n"
SEP_LINE = "\n"
DEFAULT_PARSE_MAXSEC = 30
DEFAULT_LINE_LIM = None
DEFAULT_PROCESSORS = {"tokenize": "combined"}
MAX_SYLL_IN_PARSE_UNIT = 14
MIN_SYLL_IN_PARSE_UNIT = None
MIN_WORDS_IN_PHRASE = 2
MAX_WORDS_IN_PHRASE = 15
DEFAULT_LANG = "en"
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <cyan>{function}</cyan> | <level>{message}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan>"
LOG_LEVEL = 5
DEFAULT_METER = "default_english"
METER_MAX_S = 2
METER_MAX_W = 2
METER_RESOLVE_OPTIONALITY = True
DEFAULT_CATEGORICAL_CONSTRAINTS = []
ESPEAK_PATHS = [
    "/opt/homebrew/Cellar/espeak/",
    "/usr/lib/espeak/",
    "/usr/lib/x86_64-linux-gnu/",
    "/usr/lib/",
    "/usr/local/lib/",
]
DF_INDEX = [
    "stanza_num",
    "line_num",
    "line_txt",
    "parse_rank",
    "parse_txt",
    "bestparse_txt",
    "parse_meter",
    "parse_stress",
    "parse_meter_str",
    "parse_stress_str",
    "sent_num",
    "sentpart_num",
    "wordtoken_num",
    "word_lang",
    "wordtype_lang",
    "wordtoken_txt",
    "wordform_num",
    "meterpos_num",
    "meterpos_txt",
    "meterpos_val",
    "syll_num",
    "syll_txt",
    "syll_ipa",
    "meterslot_num",
    "meterslot_txt",
    "phon_txt",
]
DF_COLS_RENAME = {
    "wordtoken_sent_num": "sent_num",
    "wordtoken_sentpart_num": "sentpart_num",
    "meterpos_meter_val": "meterpos_val",
    "meterslot_w_peak": "*w_peak",
    "meterslot_w_stress": "*w_stress",
    "meterslot_s_unstress": "*s_unstress",
    "meterslot_unres_across": "*unres_across",
    "meterslot_unres_within": "*unres_within",
    "meterslot_foot_size": "*foot_size",
    "parse_line_num": "line_num",
    "parse_stanza_num": "stanza_num",
    "parse_line_txt": "line_txt",
    "parselist_num_parses": "line_numparse",
    "word_lang": "wordtoken_lang",
}
DF_BADCOLS = ["word_txt", "word_num", "wordform_txt"]
LANGS = {}
HTML_CSS = """

.miniquote { margin-left:0em;margin-top:.5em;font-family:monospace; font-size:.8em;}
.parse { line-height:2.5em; letter-spacing:.1em;}
.parselist { list-style-type: none; }
.parselist li { padding-left:2em;}
.parselist li:nth-child(5n) { list-style-type: decimal; }
.parse { text-decoration-offset:5px; }

.viol_y { text-decoration-color:#f43838; color: #f43838; }
.mtr_s { text-decoration: overline; }
.str_s { font-weight:600; }
.parselist > li:first-of-type { list-style-type: decimal; }
.parselist > li:last-of-type { list-style-type: decimal; }
"""
RHYME_MAX_DIST = 1


# .str_s { text-decoration: underline dotted; text-underline-offset: 3px; }
# .str_s.mtr_s { text-decoration: overline; text-underline-offset: 3px; }
# .viol_y { color:#f43838; }
# .str_s.mtr_s.viol_y { text-decoration: underline overline; text-decoration-color: #f43838; text-underline-offset: 3px; }
# .str_s.mtr_s.viol_n { text-decoration: underline overline; text-underline-offset: 3px; }
# .str_s.mtr_w.viol_y { text-decoration: underline dotted; text-decoration-color: #f43838; text-underline-offset: 3px; }
# .str_s.mtr_w.viol_n { text-decoration: underline dotted; text-underline-offset: 3px; }
# .str_w.mtr_w.viol_y { text-decoration: none; color: #f43838; }
# .str_w.mtr_w.viol_n { text-decoration: none; }
# .mtr_s.viol_y { text-decoration: overline; text-decoration-color: #f43838; text-underline-offset: .5em; }
# .mtr_s.viol_n { text-decoration: overline; text-underline-offset: .5em; }

# sys imports
warnings.filterwarnings("ignore")

# patches
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func):
        return func

    builtins.profile = profile

# non-sys imports
pd.options.display.width = 200
pd.options.display.max_rows = 10
logging.logger = logging.getLogger()
while logging.logger.hasHandlers():
    logging.logger.removeHandler(logging.logger.handlers[0])

# local imports

sonnet = """
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


GROUPBY_STANZA = ["stanza_num"]
GROUPBY_LINE = GROUPBY_STANZA + ["line_num", "sent_num", "sentpart_num"]
GROUPBY_WORD = GROUPBY_LINE + ["wordtoken_num", "wordform_num"]
GROUPBY_SYLL = GROUPBY_WORD + ["syll_num"]


from .utils import *
from .tokenizers import *
from .ents import *
from .texts import *
from .lines import *
from .words import *
from .syllables import *
from .phonemes import *
from .langs import *
from .parsing import *
from .meter import *

GLOBALS = globals()

INITCLASSES = {
    "Text": Text,
    "Stanza": Stanza,
    "Line": Line,
    "WordToken": WordToken,
    "WordType": WordType,
    "WordForm": WordForm,
    "Syllable": Syllable,
    "Phoneme": Phoneme,
    "WordFormList": WordFormList,
    "Parse": Parse,
    "ParsePosition": ParsePosition,
    "ParseSlot": ParseSlot,
    "ParseList": ParseList,
}

CHILDCLASSES = {
    "Text": Stanza,
    "Stanza": Line,
    "Line": WordToken,
    "WordToken": WordType,
    "WordType": WordForm,
    "WordForm": Syllable,
    "Syllable": PhonemeClass,
    "Phoneme": None,
    "WordFormList": WordForm,
    "ParseList": Parse,
    "Parse": ParsePosition,
    "ParsePosition": ParseSlot,
}

CHILDCLASSLISTS = {
    "Text": StanzaList,
    "Stanza": LineList,
    "Line": WordTokenList,
    "WordToken": WordTypeList,
    "WordType": WordFormList,
    "WordForm": SyllableList,
    "Syllable": PhonemeList,
    "Phoneme": None,
}
