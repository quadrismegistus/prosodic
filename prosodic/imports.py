import os, sys
sys.path.insert(0,'/Users/ryan/github/hashstash')
sys.path.insert(0,'/Users/rj416/github/hashstash')
from logmap import logmap
logmap.enable()
import itertools
from base64 import b64decode, b64encode
from functools import wraps
from pprint import pprint, pformat
import orjson
import json
import io
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
from typing import Iterator, Set, Dict, List, Literal, Union, Optional
from types import GeneratorType
import re
import os
import sys
from contextlib import contextmanager, redirect_stdout, redirect_stderr
import csv
from hashstash import HashStash, log, logger, get_obj_addr, progress_bar, stuff, serialize, unstuff, deserialize, encode_hash, call_function_politely, stashed_result
from importlib import resources

PATH_HERE = os.path.abspath(os.path.dirname(__file__))
PATH_REPO = os.path.dirname(PATH_HERE)
PATH_PROSODIC = PATH_HERE
PATH_LANGS = os.path.join(PATH_PROSODIC, "langs")
PATH_LIB = os.path.join(PATH_PROSODIC, "lib")
sys.path.append(PATH_LIB)
PATH_PHONS = os.path.join(PATH_LANGS, "phonemes.json")
PATH_WEB = os.path.join(PATH_PROSODIC, "web")
PATH_REPO_DATA = os.path.join(PATH_REPO, "data")
PATH_DICTS = os.path.join(PATH_REPO_DATA, "dicts")
PATH_HOME = os.path.expanduser("~/prosodic_data")
PATH_HOME_DATA = os.path.join(PATH_HOME, "data")
PATH_HOME_DATA_CACHE = os.path.join(PATH_HOME_DATA, "cache")
os.makedirs(PATH_HOME_DATA, exist_ok=True)

stash = HashStash(PATH_HOME_DATA_CACHE, engine='memory', serializer='hashstash', compress='lz4', b64=True)
stash_was = None

import panphon
import panphon.sonority


USE_CACHE = False
USE_REDIS = False
HASHSTR_LEN = None
DEFAULT_NUM_PROC = None
SYLL_SEP = "."

DEFAULT_USE_REGISTRY = True
DEFAULT_COMBINE_BY = "line"

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
LOG_LEVEL = 'CRITICAL'
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
    "C:\\Program Files\\eSpeak NG\\libespeak-ng.dll",
    "C:\\Program Files (x86)\\eSpeak NG\\libespeak-ng.dll",
    "C:\\Program Files (x64)\\eSpeak NG\\libespeak-ng.dll",
    "C:\\Program Files (Arm)\\eSpeak NG\\libespeak-ng.dll",
]
DF_INDEX = [
    "stanza_num",
    "line_num",
    "line_txt",
    "linepart_num",
    "linepart_txt",
    "parse_rank",
    "parse_txt",
    "bestparse_txt",
    "parse_meter",
    "parse_stress",
    "parse_meter_str",
    "parse_stress_str",
    "sent_num",
    "sentpart_num",
    # "preterm_num",
    # "preterm_str",
    "wordtoken_num",
    "wordtoken_txt",
    # "wordtoken_lang",
    # "preterm_str",
    "wordtype_txt",
    "wordtype_lang",
    # "wordtoken_txt",
    "wordform_num",
    "wordform_txt",
    "wordform_ipa",
    "wordform_ipa_origin",
    "wordform_stress",
    "wordform_weight",
    "meterpos_num",
    "meterpos_txt",
    "meterpos_val",
    "syll_num",
    "syll_txt",
    "syll_ipa",
    "meterslot_num",
    "meterslot_txt",
    "phon_txt",
    "grid_i",
]
DF_COLS_RENAME = {
    "wordtoken_sent_num": "sent_num",
    "wordtoken_sentpart_num": "sentpart_num",
    "wordtoken_line_num": "line_num",
    "wordtoken_linepart_num": "linepart_num",
    "wordtoken_para_num": "stanza_num",
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
    # "wordtype_num_forms": "num_wordforms",
}
DF_BADCOLS = {
    "word_txt",
    "word_num",
    "wordform_txt",
    "preterm_num",
    "preterm_txt",
    "preterm_str",
    "wordtoken_lang",
    "wordtype_num",
    "wordtype_num_forms",
    "wordtype_is_punc",
    "wordtype_lang",
    "wordform_force_unstress",
    "wordform_force_ambig_stress",
    "text_lang",
    "wordtoken_lang",
}

DF_INDEX = [x for x in DF_INDEX if x not in DF_BADCOLS]

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
# logging.logger = logging.getLogger()
# while logging.log.hasHandlers():
#     logging.log.removeHandler(logging.log.handlers[0])

# local imports

sonnet = """Those hours, that with gentle work did frame
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
Leese but their show; their substance still lives sweet."""

sonnet2 = """Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,"""


GROUPBY_STANZA = ["stanza_num"]
GROUPBY_LINE = GROUPBY_STANZA + ["line_num", "sent_num", "sentpart_num"]
GROUPBY_WORD = GROUPBY_LINE + ["wordtoken_num", "wordform_num"]
GROUPBY_SYLL = GROUPBY_WORD + ["syll_num"]



DEFAULT_CONSTRAINTS = [
    "w_peak",
    "w_stress",
    "s_unstress",
    "unres_across",
    "unres_within",
    "foot_size",
    # "pentameter"
]




from .utils import *
from .ents import *
from .words import *
from .texts import *
from .sents import *
from .langs import *
from .parsing import *

GLOBALS = globals()
GLOBALS["list"] = list

CHILDCLASSLISTS = {
    TextModel: WordTokenList,
    Stanza: LineList,
    Line: WordTokenList,
    WordToken: WordTypeList,
    WordType: WordFormList,
    WordForm: SyllableList,
    Syllable: PhonemeList,
    Phoneme: None,

    Parse: ParsePositionList,
    ParsePosition: ParseSlotList,

    Sentence: WordTokenList,
    SentPart: WordTokenList,
    LinePart: WordTokenList,
}

SELFCLASSES = {
    "textmodel": TextModel,
    "text": TextModel,
    "stanza": Stanza,
    "line": Line,
    "wordtoken": WordToken,
    "word": WordToken,
    "wordtype": WordType,
    "wordform": WordForm,
    "syllable": Syllable,
    "syll": Syllable,
    "phoneme": Phoneme,
    "phoneme": Phoneme,
    "parse": Parse,
    "parseposition": ParsePosition,
    "parseslot": ParseSlot,
    "sentence": Sentence,
    "sentpart": SentPart,
    "linepart": LinePart,
    "sent": Sentence,
}

PLURAL_ATTRS = {"texts", "textmodels", "stanzas", "lines", "wordtokens", "wordtokens", "wordtypes", "wordforms", "syllables", "phonemes", "parses", "sylls", "words", "lineparts", "sentparts", "sentences", "sentences", "sents"}
SINGULAR_ATTRS = {"text", "textmodel", "stanza", "line", "wordtoken", "word", "wordtype", "wordform", "syllable", "phoneme", "parse", "syll", "linepart", "sentpart", "sentence", "sent"}


LISTCLASSES = {
    "stanza": StanzaList,
    "line": LineList,
    "text": TextList,
    "textmodel": TextList,
    "texts": TextList,
    "textmodels":TextList,
    "wordtoken": WordTokenList,
    "wordtype": WordTypeList,
    "wordform": WordFormList,
    "syllable": SyllableList,
    "syll": SyllableList,
    "phoneme": PhonemeList,
    "parse": ParseList,
    "stanzalist": StanzaList,
    "linelist": LineList,
    "wordtokenlist": WordTokenList,
    "wordtypelist": WordTypeList,
    "wordformlist": WordFormList,
    "syllablelist": SyllableList,
    "phonemelist": PhonemeList,
    "parselist": ParseList,
    "stanzas": StanzaList,
    "lines": LineList,
    "words": WordTokenList,
    "wordtokens": WordTokenList,
    "wordtypes": WordTypeList,
    "wordforms": WordFormList,
    "syllables": SyllableList,
    "sylls": SyllableList,
    "phonemes": PhonemeList,
    "parses": ParseList,
    "sentences": SentenceList,
    "sentence": SentenceList,
    "sentpart": SentPartList,
    "sentparts": SentPartList,
    "lineparts": LinePartList,
    "linepart": LinePartList,
    "sents": SentenceList,
    "sent": SentenceList
}

CLASSPREFIXES = {
    TextModel: "Text",
    Stanza: "Stanza",
    Line: "Line",
    WordToken:"Token",
    WordType: "Type",
    WordForm: "Form",
    Syllable: "Syll",
    Phoneme: "Phon",
    Parse: "Parse",
    ParsePosition: "MPos",
    ParseSlot: "MSlot",

    TextList: "Texts",
    StanzaList: "Stanzas",
    LineList: "Lines",
    WordTokenList: "Tokens",
    WordTypeList: "Types",
    WordFormList: "Forms",
    SyllableList: "Sylls",
    PhonemeList: "Phonemes",
    ParseList: "Parses",

    SentenceList: "Sentences",
    SentPartList: "SentParts",
    LinePartList: "LineParts",
    Sentence: "Sent",
    SentPart: "SentPart",
    LinePart: "LinePart",
}

ALL_CLASSES = {**LISTCLASSES, **SELFCLASSES}

# Add this new dictionary after the existing class mappings
CLASS_DEPTHS = {
    TextList: -1,
    TextModel: 0,
    
    WordTokenList: 1,
    Stanza: 1,
    Line: 1,
    LinePart: 1,
    SentPart: 1,
    Sentence: 1,

    StanzaList: 1,
    LineList: 1,
    SentPartList: 1,
    SentenceList: 1,
    LinePartList: 1,

    WordToken: 2,

    WordTypeList: 3,
    WordType: 4,
    WordFormList: 5,
    WordForm: 6,
    SyllableList: 7,
    Syllable: 8,
    PhonemeList: 9,
    Phoneme: 10,
    
    ParseList: 1,
    Parse: 1,
    ParsePosition: 2,
    ParseSlot: 3,
}

def pluralize_class_name(class_name):
    class_name = class_name.replace('list','')
    return class_name+'s' if not class_name.endswith('s') else class_name

def singularize_class_name(class_name):
    return class_name[:-1] if class_name.endswith('s') else class_name


def get_list_class(class_name):
    return get_class(get_list_class_name(class_name))

def get_ent_class(class_name):
    return get_class(singularize_class_name(class_name.lower()))

def get_class_depth(class_name):
    return CLASS_DEPTHS.get(get_class(class_name),-1)

def get_class(class_name):
    """
    Get the class object based on a variety of possible nicknames.
    
    Args:
        class_name (str): A string representing the class name or nickname.
        
    Returns:
        type: The corresponding class object, or None if not found.
    """
    class_name = str(class_name).lower().replace('_', '').replace(' ', '')
    return ALL_CLASSES.get(class_name)

def get_list_class_name(list_class):
    return pluralize_class_name(list_class.lower())