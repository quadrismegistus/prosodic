from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path

import yaml

from panphon import _panphon
from panphon import permissive


class Collapser(object):
    def __init__(self, tablename='dogolpolsky_prime.yml', feature_set='spe+', feature_model='strict'):
        fm = {'strict': _panphon.FeatureTable,
              'permissive': permissive.PermissiveFeatureTable}
        self.fm = fm[feature_model](feature_set=feature_set)
        self.rules = self._load_table(tablename)

    def _load_table(self, tablename):
        fn = os.path.join('data', tablename)
        fn = os.path.join(os.path.dirname(__file__), fn)
        with open(fn, 'r', encoding='utf-8') as f:
            rules = []
            table = yaml.load(f.read(), Loader=yaml.FullLoader)
            for rule in table:
                rules.append((_panphon.fts(rule['def']), rule['label']))
        return rules

    def collapse(self, s):
        segs = []
        for seg in self.fm.seg_regex.findall(s):
            fts = self.fm.fts(seg)
            for mask, label in self.rules:
                if self.fm.match(mask, fts):
                    segs.append(label)
                    break
        return ''.join(segs)
