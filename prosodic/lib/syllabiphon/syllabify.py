import panphon
import panphon.sonority
import collections

ENG_CONFL = {
    9: 9,
    8: 9,
    7: 7,
    6: 6,
    5: 5,
    4: 4,
    3: 4,
    2: 4,
    1: 4,
}

class Syllabify:
    def __init__(self, confl=ENG_CONFL):
        self.ft = panphon.FeatureTable()
        self.son = panphon.sonority.Sonority()
        self.confl = confl

    def _sonority(self, ph):
        return self.confl[self.son.sonority(ph)]

    def _to_grid(self, word):
        Seg = collections.namedtuple('Seg', ['ph', 'son'])
        segs = self.ft.ipa_segs(word)
        return [Seg(ph, self._sonority(ph)) for ph in segs]

    def find_boundaries(self, grid):
        boundaries = [True for _ in grid] + [True]
        for i, _ in list(enumerate(boundaries))[1:-1]:
            # print(boundaries)
            if grid[i-1].son < grid[i].son:
                # print('Rule 1')
                boundaries[i] = False
            if grid[i-1].son > grid[i].son:
                # print('Rule 2')
                if i < len(grid) - 1 and grid[i].son >= grid[i+1].son:
                    # print('Rule 2a')
                    boundaries[i] = False
                elif i == len(grid) - 1:
                    # print('Rule 2b')
                    boundaries[i] = False
            try:
                if grid[i-2].son == grid[i-1].son and grid[i-1].son == grid[i].son:
                    boundaries[i] = False
                    # print('Rule 3')
            except IndexError:
                pass
        return boundaries

    def _syl_seg(self, word):
        grid = self._to_grid(word)
        b = self.find_boundaries(grid)
        syls, syl = [], []
        for i, seg in enumerate(grid):
            if b[i] and syl:
                syls.append(syl)
                syl = []
            syl.append(grid[i])
        syls.append(syl)
        return syls

    def syl_seg(self, word):
        return [seg.ph for seg in self._syl_seg(word)]

    def parse_syl(self, syl):
        max_son = max([seg.son for seg in syl])
        ons, nuc, cod = '', '', ''
        i = 0
        while syl[i].son < max_son:
            ons += syl[i].ph
            i += 1
        nuc = syl[i].ph
        i += 1
        cod = ''.join([seg.ph for seg in syl[i:]])
        Syl = collections.namedtuple('Syl', ['ons', 'nuc', 'cod'])
        return Syl(ons, nuc, cod)

    def syl_parse(self, word):
        syls = self._syl_seg(word)
        return [self.parse_syl(s) for s in syls]