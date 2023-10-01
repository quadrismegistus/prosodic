from .imports import *
from .constraints import *


class ParseList(UserList):
    def __repr__(self):
        return repr(self.df)
    @property
    def df(self):
        return pd.DataFrame(
            [
                {
                    'parse':px.txt,
                    **px.attrs
                } 
                for px in self.data
            ]
        ).set_index('parse').fillna(0).applymap(lambda x: x if type(x)==str else int(x))


def parse_mp(parse): return parse.init()


class ParseTextUnit(entity):
    @cached_property
    def wordform_combos(self):
        ll = [l for l in self.wordforms if l]
        return list(itertools.product(*ll))
    
    @cached_property
    def slot_matrix(self):
        ll = [
            [
                syll
                for wordform in row
                for syll in wordform.children
            ]
            for row in self.wordform_combos
        ]
        for l in ll:
            for i,unit in enumerate(l):
                l[i] = ParseSlot(i,unit)
        return ll
    
    @cached_property
    def slots(self): return self.slot_matrix[0]

    
    def parse(self, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W, num_proc=1, progress=True, bound=False):
        self.bound_init = False
        l = self.parse_slots_slow(
            constraints=constraints, 
            max_s=max_s, 
            max_w=max_w, 
            num_proc=num_proc, 
            progress=progress
        )
        l.sort()
        for i,px in enumerate(l): px.parse_rank=i+1

        if bound: l = self.bound_parses(l, progress=progress)
        self.parses_ = ParseList(l)
        return self.parses_[0]

    @cached_property
    def parses(self, **kwargs):
        if not self.parses_: self.parse(**kwargs)
        return self.parses_

    @cached_property
    def best_parses(self, **kwargs): return self.unbounded_parses
    @cached_property
    def best_parse(self): return self.best_parses[0] if self.best_parses else None
    @cached_property
    def unbounded_parses(self): 
        if not self.bound_init: self.bound_parses()
        return ParseList([px for px in self.parses if not px.is_bounded])
    @cached_property
    def bounded_parses(self, **kwargs): 
        if not self.bound_init: self.bound_parses()
        return ParseList([px for px in self.parses if px.is_bounded])
    @cached_property
    def scansions(self, **kwargs):
        index_matches = pd.Series([px.meter_str for px in self.parses]).drop_duplicates().index
        return ParseList([self.parses[i] for i in index_matches])


    def possible_parses(self, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W):
        all_parses = []
        for slots in self.slot_matrix:
            all_parses.extend(
                get_possible_parse_objs(
                    slots, 
                    constraints=constraints, 
                    max_s=max_s, 
                    max_w=max_w
                )
            )
        return all_parses
    
    def parse_slots_slow(self, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W, num_proc=1, progress=True):
        objs = self.possible_parses(
            constraints=constraints,
            max_s=max_s,
            max_w=max_w
        )
        return supermap(
            parse_mp,
            objs,
            desc='Applying constraints',
            progress=progress,
            num_proc=num_proc
        )
    
    def bound_parses(self, parses = None, progress=True):
        if self.bound_init: return
        if parses is None: parses = self.parses
        for parse_i,parse in enumerate(tqdm(parses, desc='Bounding parses', disable=not progress)):
            for comp_parse in parses[parse_i+1:]:
                if comp_parse.is_bounded:
                    continue
                relation = parse.bounding_relation(comp_parse)
                if relation == Bounding.bounded:
                    parse.is_bounded = True
                    parse.bounded_by = comp_parse
                elif relation == Bounding.bounds:
                    comp_parse.is_bounded = True
                    comp_parse.bounded_by = parse
        self.bound_init=True
        return parses



    def parse_slots_fast(self, slots, constraints=[]):
        num_slots = len(slots)
        initial_parse = Parse(num_slots, constraints = constraints)
        parses = initial_parse.extend(slots[0])
        parses[0].comparison_nums.add(1)

        bounded_parses=[]
        # for each slot num in number of slots
        for slot_n in range(1, num_slots):
            new_parses = []
            # loop through current parses
            for parse in parses:
                # add to new_parses the result of parse.extend (several parses)
                new_parses.append(parse.extend(slots[slot_n]))

            # loop through new parse set
            for parse_set_index,parse_set in enumerate(new_parses):
                for parse_index,parse in enumerate(parse_set):
                    parse.comparison_parses = []
                    if len(parse_set) > 1 and parse_index == 0:
                        parse.comparison_nums.add(parse_set_index)

                    for comparison_index in parse.comparison_nums:
                        # should be a label break, but not supported in python
                        # find better solution; redundant checking
                        if parse.is_bounded:
                            break
                        try:
                            for comparison_parse in new_parses[comparison_index]:
                                if parse is comparison_parse:
                                    continue
                                if not comparison_parse.is_bounded:
                                    if parse.can_compare(comparison_parse):
                                        bounding_relation = parse.bounding_relation(comparison_parse)
                                        if bounding_relation == Bounding.bounds:
                                            comparison_parse.is_bounded = True
                                            comparison_parse.bounded_by = parse

                                        elif bounding_relation == Bounding.bounded:
                                            parse.is_bounded = True
                                            parse.bounded_by = comparison_parse
                                            break

                                        elif bounding_relation == Bounding.equal:
                                            parse.comparison_parses.append(comparison_parse)
                                    else:
                                        parse.comparison_parses.append(comparison_parse)
                        except IndexError:
                            pass

            # reset parses
            parses = []
            parse_num = 0
            for parse_set in new_parses:
                for parse in parse_set:
                    if parse.is_bounded:
                        bounded_parses.append(parse)
                    elif parse.score >= 1000:
                        parse.unmetrical = True
                        bounded_parses.append(parse)
                    else:
                        parse.parse_num = parse_num
                        parse_num += 1
                        parses.append(parse)

            for parse in parses:
                parse.comparison_nums = set()
                for comp_parse in parse.comparison_parses:
                    if not comp_parse.is_bounded:
                        parse.comparison_nums.add(comp_parse.parse_num)
                        
        return parses,bounded_parses



@total_ordering
class Parse(entity):
    str2int = {'w':'1','s':'2'}
    def __init__(self, num_total_slots:int, constraints:list=[]):
        super().__init__()
        self.positions = []
        self.constraints = constraints
        self.constraint_names = [c.__name__ for c in self.constraints]
        self.num_slots = 0
        self.num_total_slots = num_total_slots
        self.is_bounded = False
        self.bounded_by = None
        self.unmetrical = False
        self.comparison_nums = set()
        self.comparison_parses = []
        self.parse_num = 0
        self.total_score = None
        self.pause_comparisons = False

    def __lt__(self,other):
        def get_sort_key(px):
            return (
                # (0 if not px.is_bounded else 1),
                px.score, 
                px.average_position_size,
                px.positions[0].is_prom,
                px.num_stressed_sylls,
            )
        return get_sort_key(self) < get_sort_key(other)

    def __eq__(self, other):
        logger.error(f'{self} and {other} could not be compared in sort, ended up equal')
        return not (self<other) and not (other<self)
    
    @cached_property
    def txt(self): return "|".join(m.token for m in self.positions)

    def __repr__(self):
        attrstr=get_attr_str(self.attrs)
        parse=self.txt
        preattr=f'({self.__class__.__name__}: {parse})'
        return f'{preattr}{attrstr}'
    
    def init(self):
        if self._init: return
        self._init=True
        self.constraint_viols # trigger
        return self
    
    @cached_property
    def num_stressed_sylls(self):
        return len([
            slot
            for mpos in self.positions
            for slot in mpos.slots
            if slot.is_stressed
        ])
    
    @cached_property
    def average_position_size(self):
        l = [len(mpos.children) for mpos in self.positions if mpos.children]
        return np.mean(l) if len(l) else np.nan

    @property
    def attrs(self):
        return {
            **self._attrs,
            'rank':self.parse_rank,
            'meter':self.meter_str,
            'stress':self.stress_str,
            'score':self.score,
            **({'is_bounded':True} if self.is_bounded else {}),
            **{c:v for c,v in self.constraint_scores.items() if v!=np.nan and v}
        }

    @cached_property
    def constraint_viols(self):
        # logger.debug(self)
        scores = [mpos.constraint_viols for mpos in self.positions]
        d={}
        nans=[np.nan for _ in range(len(self.slots))]
        for constraint in self.constraints:
            cname=constraint.__name__
            d[cname] = [x for score_d in scores for x in score_d.get(cname,nans)]
        return d
    
    @cached_property
    def constraint_scores(self):
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}

    @cached_property
    def score(self):
        try:
            return sum(self.constraint_scores.values())
        except ValueError:
            return '*'  # could be string if categorical


    # def __copy__(self):
    #     other = Parse(self.num_slots, constraints=self.constraints)
    #     other.num_slots = self.num_slots
    #     for pos in self.positions:
    #         other.positions.append(copy(pos))
    #     other.comparison_nums = copy(self.comparison_nums)
    #     for k,v in list(self.constraint_scores.items()):
    #         other.constraint_scores[k]=copy(v)
    #     return other

    # return a list of all slots in the parse
    @cached_property
    def slots(self):
        return [slot for mpos in self.positions for slot in mpos.slots]


    @cached_property
    def meter_str(self,word_sep=""):
        return ''.join(
            '+' if mpos.is_prom else '-'
            for mpos in self.positions
            for slot in mpos.slots
        )
    
    @cached_property
    def stress_str(self,word_sep=""):
        return ''.join(
            '+' if slot.is_stressed else '-'
            for mpos in self.positions
            for slot in mpos.slots
        ).lower()
    
    # return a representation of the bounding relation between self and parse
    def bounding_relation(self, parse):
        contains_greater_violation = False
        contains_lesser_violation = False
        for constraint in self.constraints:
            cname=constraint.__name__
            mark = self.constraint_scores[cname]
            if mark > parse.constraint_scores[cname]:
                contains_greater_violation = True

            if mark < parse.constraint_scores[cname]:
                contains_lesser_violation = True

        if contains_greater_violation:
            if contains_lesser_violation:
                return Bounding.unequal # contains both greater and lesser violations
            else:
                return Bounding.bounded # contains only greater violations
        else:
            if contains_lesser_violation:
                return Bounding.bounds # contains only lesser violations
            else:
                return Bounding.equal # contains neither greater nor lesser violations

    # # add an extra slot to the parse
    # # returns a list of the parse with a new position added and (if it exists) the parse with the last position extended
    # def extend(self, slot):
    #     #logging.debug('>> extending self (%s) with slot (%s)',self,slot)
    #     self.total_score = None
    #     self.num_slots += 1

    #     extended_parses = [self]

    #     # positions containing just the slot

    #     s_pos = ParsePosition('s', parse=self)
    #     s_pos.append(slot)
    #     w_pos = ParsePosition('w', parse=self)
    #     w_pos.append(slot)

    #     if len(self.positions) == 0:
    #         w_parse = copy(self)
    #         self.positions.append(s_pos)
    #         w_parse.positions.append(w_pos)
    #         extended_parses.append(w_parse)

    #     else:
    #         last_pos = self.positions[-1]

    #         if last_pos.meter_val == 's':
    #             if len(last_pos.slots) < self.max_s:
    #                 s_parse = copy(self) # parse with extended final 's' position
    #                 s_parse.positions[-1].append(slot)
    #                 extended_parses.append(s_parse)
    #             self.positions.append(w_pos)

    #         else:
    #             if len(last_pos.slots) < self.max_w:
    #                 w_parse = copy(self) # parse with extended final 'w' position
    #                 w_parse.positions[-1].append(slot)
    #                 extended_parses.append(w_parse)
    #             self.positions.append(s_pos)

    #         # assign violation scores for the (completed) penultimate position

    #         ## extrametrical?
    #         pos_i=len(self.positions)-2
    #         for constraint in self.constraints:
    #             v_score = constraint.violation_score(self.positions[-2], pos_i=pos_i,slot_i=self.num_slots-1,num_slots=self.total_slots,all_positions=self.positions,parse=self)
    #             if v_score == "*":
    #                 self.constraint_scores[constraint] = "*"
    #             else:
    #                 self.constraint_scores[constraint] += v_score

    #     if self.num_slots == self.total_slots:

    #         # assign violation scores for the (completed) ultimate position
    #         for parse in extended_parses:
    #             for constraint in self.constraints:
    #                 v_score = constraint.violation_score(parse.positions[-1], pos_i=len(parse.positions)-1,slot_i=self.num_slots-1,num_slots=self.total_slots,all_positions=parse.positions,parse=parse)
    #                 if v_score == "*":
    #                     parse.constraint_scores[constraint] = "*"
    #                 else:
    #                     parse.constraint_scores[constraint] += v_score

    #     return extended_parses


    
    # def can_compare(self, parse):
    #     return (
    #         (self.num_slots == self.total_slots) 
    #         or 
    #         (
    #             (self.positions[-1].meter_val == parse.positions[-1].meter_val) 
    #             and 
    #             (len(self.positions[-1].slots) == len(parse.positions[-1].slots))
    #         )
    #     )
            


class ParseSlot(entity):
    def __init__(self, slot_i:int, unit:entity):
        super().__init__()
        self.i=slot_i                    # eg, could be one of 0-9 for a ten-syllable line
        self.unit = unit
        self.children=[unit]
        self.token=unit.txt
        self.featpaths={}
        self.word=unit.parent

    @cached_property
    def is_stressed(self): return self.unit.is_stressed
    @cached_property
    def is_heavy(self): return self.unit.is_heavy
    @cached_property
    def is_strong(self): return self.unit.is_strong
    @cached_property
    def is_weak(self): return self.unit.is_weak

    @cached_property
    def attrs(self):
        return {**self._attrs, **{'is_stressed':self.is_stressed, 'is_heavy':self.is_heavy, 'is_strong':self.is_strong, 'is_weak':self.is_weak}}



class ParsePosition(entity):
    def __init__(self, meter_val:str, parse:Parse, slots=[]): # meter_val represents whether the position is 's' or 'w'
        super().__init__()
        self.meter_val = meter_val
        self.parse=parse
        self.children=self.slots=slots
        for slot in self.slots: slot.meter_val=self.meter_val

    def __copy__(self):
        other = ParsePosition(self.meter_val, parse=self, slots=self.slots[:])
        for k,v in list(self.constraint_scores.items()):
            other.constraint_scores[k]=copy(v)
        return other
    
    def __repr__(self):
        return f'ParsePosition({self.token})'
    
    @cached_property
    def constraint_viols(self):
        # logger.debug(self)
        d={}
        for constraint in self.constraints:
            cname=constraint.__name__
            d[cname] = l = constraint(self)
            assert len(l) == len(self.slots)
        return d

    @cached_property
    def constraint_scores(self):
        return {cname:safesum(cvals) for cname,cvals in self.constraint_viols.items()}


    @cached_property
    def constraints(self): return self.parse.constraints

    @cached_property
    def is_prom(self): return self.meter_val=='s'

    @cached_property
    def token(self):
        if not hasattr(self,'_token') or not self._token:
            token = '.'.join([slot.token for slot in self.slots])
            token=token.upper() if self.meter_val=='s' else token.lower()
            self._token=token
        return self._token






def getlenparse(l): return sum(len(x) for x in l)

def iter_mpos(nsyll, starter=[], pos_types=None, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if pos_types is None:
        wtypes = ['w'*n for n in range(1,max_w+1)]
        stypes = ['s'*n for n in range(1,max_s+1)]
        pos_types=[[x] for x in wtypes + stypes]
        
    news=[]
    for pos_type in pos_types:
        if starter and starter[-1][-1]==pos_type[0][0]: continue
        new = starter + pos_type
        # if starter: print(starter[-1][-1], pos_type[0][0], new)
        #if not is_ok_parse(new): continue
        if getlenparse(new)<=nsyll:
            news.append(new)
    
    # news = battle_parses(news)
    if news: yield from news
    # print('\n'.join('|'.join(x) for x in news))
    for new in news: yield from iter_mpos(nsyll, starter=new, pos_types=pos_types)

def get_possible_parses(nsyll, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if max_s is None: max_s = nsyll
    if max_w is None: max_w = nsyll
    return [l for l in iter_mpos(nsyll,max_s=max_s,max_w=max_w) if getlenparse(l)==nsyll]

def get_possible_parse_objs(slots, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W):
    parse_objs = []
    for parse_poss in get_possible_parses(len(slots), max_s=max_s, max_w=max_w):
        slot_i=0
        parse_obj = Parse(len(slots), constraints=constraints)
        mpos_objs=[]
        for mpos in parse_poss:
            mpos_slots=[]
            for slot_mval in mpos:
                mpos_slots.append(slots[slot_i])
                slot_i+=1
            mpos_obj = ParsePosition(mpos[0], parse=parse_obj, slots=mpos_slots)
            mpos_objs.append(mpos_obj)
        parse_obj.children = parse_obj.positions = mpos_objs
        parse_objs.append(parse_obj)
    return parse_objs



# def genDefault(metername=DEFAULT_METER):
# 	import prosodic
# 	#metername = sorted(prosodic.config['meters'].keys())[0]
# 	meters=prosodic.config['meters']
# 	if metername in meters:
# 		meter=meters[metername]
# 	else:
# 		meter=meters[sorted(meters.keys())[0]]
# 	print('>> no meter specified. defaulting to this meter:')
# 	#raise Exception
# 	print(meter)
# 	return meter


# #def meterShakespeare():
# #	return Meter('strength.s=>')

# DEFAULT_CONSTRAINTS = [
# 	'footmin-w-resolution/1',
# 	'footmin-f-resolution/1',
# 	'strength.w=>-p/1',
# 	'headedness!=rising/1',
# 	'number_feet!=5/1'
# ]




# def get_meter(id=None, name=None, maxS=2, maxW=2, splitheavies=0, constraints=DEFAULT_CONSTRAINTS,return_dict=False):

# 	"""
# 	{'constraints': ['footmin-w-resolution/1',
# 	'footmin-f-resolution/1',
# 	'strength.w=>-p/1',
# 	'headedness!=rising/1',
# 	'number_feet!=5/1'],
# 	'id': 'iambic_pentameter',
# 	'maxS': 2,
# 	'maxW': 2,
# 	'name': 'Iambic Pentameter',
# 	'splitheavies': 0}"""
# 	if 'Meter.Meter' in str(id.__class__): return id

# 	if not id: id='Meter_%s' % now()
# 	if not name: name = id + '['+' '.join(constraints)+']'

# 	config = locals()

# 	import prosodic
# 	if id in prosodic.config['meters']:
# 		return prosodic.config['meters'][id]


# 	if return_dict: return config
# 	return Meter(config)




# class Meter:
# 	Weak="w"
# 	Strong="s"
# 	## for caching meter-parses
# 	parseDict = {}

# 	@staticmethod
# 	def genMeters():
# 		meterd={}
# 		meterd['*StrongSyllableWeakPosition [Shakespeare]']=Meter(['strength.w=>-p/1'], (1,2), False)
# 		meterd['*WeakSyllableStrongPosition']=Meter(['strength.s=>-u/1'], (1,2), False)
# 		meterd['*StressedSyllableWeakPosition']=Meter(['stress.w=>-p/1'], (1,2), False)
# 		meterd['*UnstressedSyllableStrongPosition [Hopkins]']=Meter(['stress.s=>-u/1'], (1,2), False)
# 		return meterd

# 	def __str__(self):
# 		#constraints = '\n'.join(' '.join([slicex) for slicex in slice() )
# 		#constraint_slices=slice(self.constraints,slice_length=3,runts=True)
# 		constraint_slices={}
# 		for constraint in self.constraints:
# 			ckey=constraint.name.replace('-','.').split('.')[0]
# 			if not ckey in constraint_slices:
# 				constraint_slices[ckey]=[]
# 			constraint_slices[ckey]+=[constraint]
# 		constraint_slices = [constraint_slices[k] for k in sorted(constraint_slices)]
# 		constraints = '\n\t\t'.join(' '.join(c.name_weight for c in slicex) for slicex in constraint_slices)

# 		x='<<Meter\n\tID: {5}\n\tName: {0}\n\tConstraints: \n\t\t{1}\n\tMaxS, MaxW: {2}, {3}\n\tAllow heavy syllable split across two positions: {4}\n>>'.format(self.name, constraints, self.posLimit[0], self.posLimit[1], bool(self.splitheavies), self.id)
# 		return x

# 	@cached_property
# 	def constraint_nameweights(self):
# 		return ' '.join(c.name_weight for c in self.constraints)

# 	#def __init__(self,constraints=None,posLimit=(2,2),splitheavies=False,name=None):
# 	def __init__(self,config):
# 		#self.type = type
# 		constraints=config['constraints']
# 		self.posLimit=(config['maxS'],config['maxW'])
# 		self.constraints = []
# 		self.splitheavies=config['splitheavies']
# 		self.name=config.get('name','')
# 		self.id = config['id']
# 		self.config=config
# 		#import prosodic
# 		#print(config)
# 		#self.prosodic_config=prosodic.config
# 		self.prosodic_config=config

# 		if not constraints:
# 			self.constraints.append(Constraint(id=0,name="foot-min",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=1,name="strength.s=>p",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=2,name="strength.w=>u",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=3,name="stress.s=>p",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=4,name="stress.w=>u",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=5,name="weight.s=>p",weight=1,meter=self))
# 			self.constraints.append(Constraint(id=6,name="weight.w=>u",weight=1,meter=self))

# 		elif type(constraints) == type([]):
# 			for i in range(len(constraints)):
# 				c=constraints[i]
# 				if "/" in c:
# 					(cname,weightVal)=c.split("/")
# 					#cweight=int(cweight)
# 					if ";" in weightVal:
# 						weightVals = weightVal.split(";")
# 						cweight=float(weightVals[0])
# 						muVal =float(weightVals[1])
# 						if len(weightVals) > 2:
# 							sigmaVal =float(weightVals[2])
# 					else:
# 						cweight=float(weightVal)
# 						muVal = 0.0
# 						sigmaVal = 10000
# 				else:
# 					cname=c
# 					weightVal=1.0
# 					muVal = 0.0
# 					sigmaVal = 10000
# 				self.constraints.append(Constraint(id=i,name=cname,weight=cweight,meter=self, mu=muVal, sigma=sigmaVal))
# 		"""
# 		else:
# 			if os.path.exists(constraints):
# 				constraintFiles = os.listdir(constraints)
# 				for i in range(len(constraintFiles)):
# 					constraintFile = constraintFiles[i]
# 					if constraintFile[-3:] == ".py":
# 						self.constraints.append(Constraint(id=i,name=os.path.join(constraints, constraintFile[:-3]),weight=1))
# 		"""

# 		self.constraints.sort(key=lambda _c: -_c.weight)

# 	def maxS(self):
# 		return self.posLimit[0]

# 	def maxW(self):
# 		return self.posLimit[1]




# 	def genWordMatrix(self,wordtokens):
# 		wordlist = [w.children for w in wordtokens]

# 		#import prosodic
# 		if self.prosodic_config.get('resolve_optionality',True):
# 			return list(product(*wordlist))	# [ [on, the1, ..], [on, the2, etc]
# 		else:
# 			return [ [ w[0] for w in wordlist ] ]

# 	def genSlotMatrix(self,wordtokens):
# 		matrix=[]

# 		row_wordtokens = wordtokens
# 		rows_wordmatrix = self.genWordMatrix(wordtokens)

# 		for row in rows_wordmatrix:
# 			unitlist = []
# 			id=-1
# 			wordnum=-1
# 			for word in row:
# 				wordnum+=1
# 				syllnum=-1
# 				for unit in word.children:	# units = syllables
# 					syllnum+=1
# 					id+=1
# 					wordpos=(syllnum+1,len(word.children))
# 					slot=Slot(id, unit, word.sylls_text[syllnum], wordpos, word, i_word=wordnum, i_syll_in_word=syllnum,wordtoken=row_wordtokens[wordnum], meter=self)
# 					unitlist.append(slot)

# 			if not self.splitheavies:
# 				matrix.append(unitlist)
# 			else:
# 				unitlist2=[]
# 				for slot in unitlist:
# 					if bool(slot.feature('prom.weight')):
# 						slot1=Slot(slot.i,slot.children[0],slot.token,slot.wordpos,slot.word)
# 						slot2=Slot(slot.i,slot.children[0],slot.token,slot.wordpos,slot.word)

# 						## mark as split
# 						slot1.issplit=True
# 						slot2.issplit=True

# 						## demote
# 						slot2.feats['prom.stress']=0.0
# 						slot1.feats['prom.weight']=0.0
# 						slot2.feats['prom.weight']=0.0

# 						## split token
# 						slot1.token= slot1.token[ : len(slot1.token)/2 ]
# 						slot2.token= slot2.token[len(slot1.token)/2 + 1 : ]

# 						unitlist2.append([slot,[slot1,slot2]])
# 					else:
# 						unitlist2.append([slot])

# 				#unitlist=[]
# 				for row in list(product(*unitlist2)):
# 					unitlist=[]
# 					for x in row:
# 						if type(x)==type([]):
# 							for y in x:
# 								unitlist.append(y)
# 						else:
# 							unitlist.append(x)
# 					matrix.append(unitlist)



# 		# for r in matrix:
# 		# 	for y in r:
# 		# 		print y
# 		# 	print
# 		# 	print

# 		return matrix



# 	def parse(self,wordlist,numSyll=0,numTopBounded=10):
# 		numTopBounded = self.prosodic_config.get('num_bounded_parses_to_store',numTopBounded)
# 		maxsec = self.prosodic_config.get('parse_maxsec',None)
# 		#print '>> NTB!',numTopBounded
# 		from Parse import Parse
# 		if not numSyll:
# 			return []


# 		slotMatrix = self.genSlotMatrix(wordlist)
# 		if not slotMatrix: return None

# 		constraints = self.constraints


# 		allParses = []
# 		allBoundedParses=[]

# 		import time
# 		clockstart=time.time()
# 		for slots_i,slots in enumerate(slotMatrix):
# 			#for slot in slots:
# 				#print slot
# 				#print slot.feats
# 				#print

# 			## give up?
# 			if maxsec and time.time()-clockstart > maxsec:
# 				if self.prosodic_config.get('print_to_screen',None):
# 					print('!! Time limit ({0}s) elapsed in trying to parse line:'.format(maxsec), ' '.join(wtok.token for wtok in wordlist))
# 				return [],[]

# 			_parses,_boundedParses = self.parseLine(slots)

# 			"""
# 			for prs in _parses:
# 				print 'UNBOUNDED:'
# 				print prs.__report__()
# 				print

# 			for prs in _parses:
# 				print 'BOUNDED:'
# 				print prs.__report__()
# 				print

# 			print
# 			print
# 			"""

# 			allParses.append(_parses)
# 			allBoundedParses+=_boundedParses

# 		parses,_boundedParses = self.boundParses(allParses)

# 		parses.sort()

# 		allBoundedParses+=_boundedParses

# 		allBoundedParses.sort(key=lambda _p: (-_p.numSlots, _p.score()))
# 		allBoundedParses=allBoundedParses[:numTopBounded]
# 		#allBoundedParses=[]

# 		"""print parses
# 		print
# 		print allBoundedParses
# 		for parse in allBoundedParses:
# 			print parse.__report__()
# 			print
# 			print parse.boundedBy if type(parse.boundedBy) in [str,unicode] else parse.boundedBy.__report__()
# 			print
# 			print
# 			print
# 		"""

# 		return parses,allBoundedParses

# 	def boundParses(self, parseLists):
# 		unboundedParses = []
# 		boundedParses=[]
# 		for listIndex in range(len(parseLists)):
# 			for parse in parseLists[listIndex]:
# 				for parseList in parseLists[listIndex+1:]:
# 					for compParse in parseList:
# 						if compParse.isBounded:
# 							continue
# 						relation = parse.boundingRelation(compParse)
# 						if relation == Bounding.bounded:
# 							parse.isBounded = True
# 							parse.boundedBy = compParse
# 						elif relation == Bounding.bounds:
# 							compParse.isBounded = True
# 							compParse.boundedBy = parse

# 		for parseList in parseLists:
# 			for parse in parseList:
# 				if not parse.isBounded:
# 					unboundedParses.append(parse)
# 				else:
# 					boundedParses.append(parse)

# 		return unboundedParses,boundedParses

# 	def parseLine(self, slots):

# 		numSlots = len(slots)

# 		initialParse = Parse(self, numSlots)
# 		parses = initialParse.extend(slots[0])
# 		parses[0].comparisonNums.add(1)

# 		boundedParses=[]


# 		for slotN in range(1, numSlots):

# 			newParses = []
# 			for parse in parses:
# 				newParses.append(parse.extend(slots[slotN]))

# 			for parseSetIndex in range(len(newParses)):

# 				parseSet = newParses[parseSetIndex]

# 				for parseIndex in range(len(parseSet)):

# 					parse = parseSet[parseIndex]
# 					parse.comparisonParses = []

# 					if len(parseSet) > 1 and parseIndex == 0:
# 						parse.comparisonNums.add(parseSetIndex)

# 					for comparisonIndex in parse.comparisonNums:

# 						# should be a label break, but not supported in Python
# 						# find better solution; redundant checking
# 						if parse.isBounded:
# 							break

# 						try:
# 							for comparisonParse in newParses[comparisonIndex]:

# 								if parse is comparisonParse:
# 									continue

# 								if not comparisonParse.isBounded:

# 									if parse.canCompare(comparisonParse):

# 										boundingRelation = parse.boundingRelation(comparisonParse)

# 										if boundingRelation == Bounding.bounds:
# 											# print parse.__report__()
# 											# print '--> bounds -->'
# 											# print comparisonParse.__report__()
# 											# print
# 											comparisonParse.isBounded = True
# 											comparisonParse.boundedBy = parse

# 										elif boundingRelation == Bounding.bounded:
# 											# print
# 											# print comparisonParse.__report__()
# 											# print '--> bounds -->'
# 											# print parse.__report__()
# 											# print
# 											parse.isBounded = True
# 											parse.boundedBy = comparisonParse
# 											break

# 										elif boundingRelation == Bounding.equal:
# 											parse.comparisonParses.append(comparisonParse)

# 									else:
# 										parse.comparisonParses.append(comparisonParse)
# 						except IndexError:
# 							pass

# 			parses = []
# 			#boundedParses=[]
# 			parseNum = 0

# 			for parseSet in newParses:
# 				for parse in parseSet:
# 					if parse.isBounded:
# 						boundedParses+=[parse]
# 					elif parse.score() >= 1000:
# 						parse.unmetrical = True
# 						boundedParses+=[parse]
# 					else:
# 						parse.parseNum = parseNum
# 						parseNum += 1
# 						parses.append(parse)


# 			for parse in parses:

# 				parse.comparisonNums = set()

# 				for compParse in parse.comparisonParses:
# 					if not compParse.isBounded:
# 						parse.comparisonNums.add(compParse.parseNum)



# 		return parses,boundedParses

# 	def printParses(self,parselist,lim=False,reverse=True):		# onlyBounded=True, [option done through "report" now]
# 		n = len(parselist)
# 		l_i = list(reversed(list(range(n)))) if reverse else list(range(n))
# 		parseiter = reversed(parselist) if reverse else parselist
# 		#parselist.reverse()
# 		o=""
# 		for i,parse in enumerate(parseiter):
# 			#if onlyBounded and parse.isBounded:
# 			#	continue

# 			o+='-'*20+'\n'
# 			o+="[parse #" + str(l_i[i]+1) + " of " + str(n) + "]: " + str(parse.getErrorCount()) + " errors"

# 			if parse.isBounded:
# 				o+='\n[**** Harmonically bounded ****]\n'+str(parse.boundedBy)+' --[bounds]-->'
# 			elif parse.unmetrical:
# 				o+='\n[**** Unmetrical ****]'
# 			o+='\n'+str(parse)+'\n'
# 			o+='[meter]: '+parse.str_meter()+'\n'

# 			o+=parse.__report__(proms=False)+"\n"
# 			o+=self.printScores(parse.constraint_scores)
# 			o+='-'*20
# 			o+="\n\n"
# 			i-=1
# 		return o

# 	def printScores(self, scores):
# 		output = "\n"
# 		for key, value in sorted(((str(k.name),v) for (k,v) in list(scores.items()))):
# 			if not value: continue
# 			#output += makeminlength("[*"+key+"]:"+str(value),24)
# 			#output+='[*'+key+']: '+str(value)+"\n"
# 			output+='[*'+key+']: '+str(value)+"  "
# 		#output = output[:-1]
# 		if not output.strip(): output=''
# 		output +='\n'
# 		return output


# def parse_ent(ent,meter,init,toprint=True):
# 	#print init, type(init), dir(init)
# 	ent.parse(meter,init=init)
# 	init._Text__parses[meter.id].append( ent.allParses(meter) )
# 	init._Text__bestparses[meter.id].append( ent.bestParse(meter) )
# 	init._Text__boundParses[meter.id].append( ent.boundParses(meter) )
# 	init._Text__parsed_ents[meter.id].append(ent)
# 	if toprint:
# 		ent.scansion(meter=meter,conscious=True)
# 	return ent

# def parse_ent_mp(input_tuple):
# 	(ent,meter,init,toprint) = input_tuple
# 	return parse_ent(ent,meter,init,toprint)





# class representing the potential bounding relations between to parses
class Bounding:
    bounds = 0 # first parse harmonically bounds the second
    bounded = 1 # first parse is harmonically bounded by the second
    equal = 2 # the same constraint violation scores
    unequal = 3 # unequal scores; neither set of violations is a subset of the other


# @total_ordering
# class Parse(entity):
# 	str2int = {'w':'1','s':'2'}
# 	#def __hash__(self):
# 	#	str = ""
# 	#	for x in self.meter:
# 	#		str+=Parse.str2int[x]
# 	#	return int(str)

# 	def __init__(self,meter,totalSlots):
# 		# set attrs
# 		self.positions = []
# 		self.meter = meter
# 		self.constraints = meter.constraints
# 		self.constraint_scores = {}
# 		for constraint in self.constraints:
# 			self.constraint_scores[constraint] = 0
# 		self.constraintNames = [c.name for c in self.constraints]
# 		self.numSlots = 0
# 		self.totalSlots = totalSlots
# 		self.isBounded = False
# 		self.boundedBy = None
# 		self.unmetrical = False
# 		self.comparisonNums = set()
# 		self.comparisonParses = []
# 		self.parseNum = 0
# 		self.totalScore = None
# 		self.pauseComparisons = False

# 	def __copy__(self):
# 		other = Parse(self.meter, self.totalSlots)
# 		other.numSlots = self.numSlots
# 		for pos in self.positions:
# 			other.positions.append(copy(pos))

# 		other.comparisonNums = copy(self.comparisonNums)
# 		for k,v in list(self.constraint_scores.items()):
# 			other.constraint_scores[k]=copy(v)
# 		#other.constraint_scores=self.constraint_scores.copy()
# 		#print self.constraint_scores
# 		#print other.constraint_scores

# 		return other

# 	# return a list of all slots in the parse
# 	def slots(self,by_word=False):
# 		slots = []
# 		last_word_i=None
# 		for pos in self.positions:
# 			for slot in pos.slots:
# 				if not by_word:
# 					slots.append(slot)
# 				else:
# 					if last_word_i==None or last_word_i != slot.i_word:
# 						slots.append([])
# 					slots[-1].append(slot)
# 					last_word_i=slot.i_word
# 		return slots


# 	def str_meter(self,word_sep=""):
# 		str_meter=""
# 		wordTokNow=None
# 		for pos in self.positions:
# 			for slot in pos.slots:
# 				if word_sep and wordTokNow and slot.wordtoken != wordTokNow:
# 					str_meter+=word_sep
# 				wordTokNow=slot.wordtoken
# 				str_meter+=pos.meterVal
# 		return str_meter

# 	# add an extra slot to the parse
# 	# returns a list of the parse with a new position added and (if it exists) the parse with the last position extended
# 	def extend(self, slot):
# 		#logging.debug('>> extending self (%s) with slot (%s)',self,slot)
# 		from MeterPosition import MeterPosition
# 		self.totalScore = None
# 		self.numSlots += 1

# 		extendedParses = [self]

# 		# positions containing just the slot

# 		sPos = MeterPosition(self.meter, 's')
# 		sPos.append(slot)
# 		wPos = MeterPosition(self.meter, 'w')
# 		wPos.append(slot)

# 		if len(self.positions) == 0:
# 			wParse = copy(self)
# 			self.positions.append(sPos)
# 			wParse.positions.append(wPos)
# 			extendedParses.append(wParse)

# 		else:
# 			lastPos = self.positions[-1]

# 			if lastPos.meterVal == 's':
# 				if len(lastPos.slots) < self.meter.maxS() and not slot.issplit:
# 					sParse = copy(self) # parse with extended final 's' position
# 					sParse.positions[-1].append(slot)
# 					extendedParses.append(sParse)
# 				self.positions.append(wPos)

# 			else:
# 				if len(lastPos.slots) < self.meter.maxW() and not slot.issplit:
# 					wParse = copy(self) # parse with extended final 'w' position
# 					wParse.positions[-1].append(slot)
# 					extendedParses.append(wParse)
# 				self.positions.append(sPos)

# 			# assign violation scores for the (completed) penultimate position

# 			## EXTRAMETRICAL?
# 			pos_i=len(self.positions)-2
# 			for constraint in self.constraints:
# 				vScore = constraint.violationScore(self.positions[-2], pos_i=pos_i,slot_i=self.numSlots-1,num_slots=self.totalSlots,all_positions=self.positions,parse=self)
# 				if vScore == "*":
# 					self.constraint_scores[constraint] = "*"
# 				else:
# 					self.constraint_scores[constraint] += vScore

# 		if self.numSlots == self.totalSlots:

# 			# assign violation scores for the (completed) ultimate position
# 			for parse in extendedParses:
# 				for constraint in self.constraints:
# 					vScore = constraint.violationScore(parse.positions[-1], pos_i=len(parse.positions)-1,slot_i=self.numSlots-1,num_slots=self.totalSlots,all_positions=parse.positions,parse=parse)
# 					if vScore == "*":
# 						parse.constraint_scores[constraint] = "*"
# 					else:
# 						parse.constraint_scores[constraint] += vScore

# 		#logging.debug('>> self extended to be (%s) with extendedParses (%s)',self,extendedParses)
# 		return extendedParses

# 	def getErrorCount(self):
# 		return self.score()

# 	def getErrorCountN(self):
# 		return self.getErrorCount() / len(self.positions)

# 	def formatConstraints(self,normalize=True,getKeys=False):
# 		vals=[]
# 		keys=[]
# 		for k,v in sorted(self.constraint_scores.items()):
# 			if normalize:
# 				#vals.append(v/len(self.positions))
# 				if bool(v):
# 					vals.append(1)
# 				else:
# 					vals.append(0)
# 			else:
# 				vals.append(v)

# 			if getKeys:
# 				keys.append(k)
# 				#keys[k]=len(vals)-1
# 		if getKeys:
# 			return (vals,keys)
# 		else:
# 			return vals

# 	@cached_property
# 	def totalCount(self):
# 		return sum(self.constraintCounts.values())

# 	@cached_property
# 	def constraintCounts(self):
# 		#return dict((c,int(self.constraint_scores[c] / c.weight)) for c in self.constraint_scores)
# 		cc={}
# 		for constraint in self.constraints:
# 			cn=0
# 			for pos in self.positions:
# 				if pos.constraint_scores[constraint]:
# 					cn+=1
# 			cc[constraint]=cn
# 		return cc

# 	@cached_property
# 	def num_sylls(self):
# 		return sum(len(pos.slots) for pos in self.positions)

# 	def score(self):
# 		#if self.totalScore == None:
# 		score = 0
# 		for constraint, value in list(self.constraint_scores.items()):
# 			if value == "*":
# 				self.totalScore = "*"
# 				return self.totalScore
# 			score += value
# 		self.totalScore = score

# 		return int(self.totalScore) if int(self.totalScore) == self.totalScore else self.totalScore

# 	"""
# 	Python 3 DEPRECATED
# 	def __cmp__(self, other):
# 		## @TODO: parameterize this: break ties by favoring the more binary parse
# 		x,y=self.score(),other.score()
# 		if x<y: return -1
# 		if x>y: return 1

# 		# Break tie
# 		return 0

# 		xs=self.str_meter()
# 		ys=other.str_meter()
# 		return cmp(xs.count('ww')+xs.count('ss'), ys.count('ww')+ys.count('ss'))
# 		# if x==y:
# 		#
# 		# return cmp(self.score(), other.score())
# 	"""
# 	def __lt__(self,other):
# 		return self.score() < other.score()

# 	def __eq__(self, other):
# 		return self.score() == other.score()

# 	def posString(self,viols=False):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
# 		output = []
# 		for pos in self.positions:
# 			x=str(pos)
# 			if viols and pos.has_viol: x+='*'
# 			output.append(x)
# 		return '|'.join(output)

# 	def posString2(self,viols=False):
# 		last_word = None
# 		output=''
# 		for pos in self.positions:
# 			for slot in pos.slots:
# 				slotstr=slot.token.upper() if pos.meterVal=='s' else slot.token.lower()
# 				if last_word != slot.wordtoken:
# 					output+=' '+slotstr
# 					last_word=slot.wordtoken
# 				else:
# 					output+='.'+slotstr
# 		return output.strip()

# 	def str_stress(self):		# eg NE|ver|CAME|poi|SON|from|SO|sweet|A|place
# 		output = []
# 		for pos in self.positions:
# 			slotx=[]
# 			for slot in pos.slots:
# 				if not slot.feats['prom.stress']:
# 					slotx.append('U')
# 				elif slot.feats['prom.stress']==1:
# 					slotx.append('P')
# 				else:
# 					slotx.append('S')
# 			output+=[''.join(slotx)]
# 		return string.join(output, '|')

# 	def words(self):
# 		last_word = None
# 		words=[]
# 		for slot in self.slots():
# 			slot_word=slot.word
# 			slot_wordtoken=slot.wordtoken
# 			if last_word != slot_wordtoken:
# 				words+=[slot_word]
# 				last_word=slot_wordtoken
# 		return words

# 	def wordtokens(self):
# 		last_word = None
# 		words=[]
# 		for slot in self.slots():
# 			slot_word=slot.wordtoken
# 			if last_word != slot_word:
# 				words+=[slot_word]
# 				last_word=slot_word
# 		return words

# 	def set_wordtokens_to_best_word_options(self):
# 		for wordtok,wordobj in zip(self.wordtokens(),self.words()):
# 			wordtok.set_as_best_word_option(wordobj)



# 	def __repr__(self):
# 		return self.posString()
# 		#return "["+str(self.getErrorCount()) + "] " + self.getUpDownString()

# 	def __repr2__(self):
# 		return str(self.getErrorCount())

# 	def str_ot(self):
# 		ot=[]
# 		#ot+=[self.str_meter()]
# 		#for k,v in sorted(self.constraint_scores.items()):
# 		for c in self.constraints:
# 			v=self.constraint_scores[c]
# 			ot+=[str(v) if int(v)!=float(v) else str(int(v))]
# 		return "\t".join(ot)

# 	def __report__(self,proms=False):
# 		o = ""
# 		i=0

# 		for pos in self.positions:
# 			unitlist = ""
# 			factlist = ""
# 			for unit in pos.slots:
# 				unitlist += self.u2s(unit.token) + " "
# 				#factlist += unit.stress + unit.weight + " "
# 			unitlist = unitlist[:-1]
# 			#factlist = factlist[:-1]
# 			unitlist = makeminlength(unitlist,10)

# 			if proms:
# 				feats = ""
# 				for unit in pos.slots:
# 					for k,v in list(unit.feats.items()):
# 						if (not "prom." in k): continue
# 						if v:
# 							feats += "[+" + str(k) + "] "
# 						else:
# 							feats += "[-" + str(k) + "] "
# 					feats += '\t'
# 				feats = feats.strip()

# 			viols = ""
# 			for k,v in list(pos.constraint_scores.items()):
# 				if v:
# 					viols+=str(k)
# 			viols = viols.strip()
# 			if proms:
# 				viols = makeminlength(viols,60)

# 			if pos.meterVal == "s":
# 				unitlist = unitlist.upper()
# 			else:
# 				unitlist = unitlist.lower()

# 			i+=1
# 			o+=str(i) +'\t'+ pos.meterVal2 + '\t' + unitlist + '\t' + viols
# 			if proms:
# 				o+=feats + '\n'
# 			else:
# 				o+='\n'
# 		return o[:-1]

# 	def isIambic(self):
# 		if len(self.positions) < 2:
# 			return None
# 		else:
# 			return self.positions[0].meterVal == 'w' and self.positions[1].meterVal == 's'

# 	# return True if two parses can be compared for harmonic bounding
# 	def canCompare(self, parse):

# 		isTrue = (self.numSlots == self.totalSlots) or ((self.positions[-1].meterVal == parse.positions[-1].meterVal) and (len(self.positions[-1].slots) == len(parse.positions[-1].slots)))
# 		if isTrue:
# 			pass
# 			#logging.debug('Parse1: %s\nLastMeterVal1: %s\nLastNumSlots1: %s\n--can compare-->\nParse2: %s\nLastMeterVal2: %s\nLastNumSlots2: %s',self,self.positions[-1].meterVal,len(self.positions[-1].slots),parse,parse.positions[-1].meterVal,len(parse.positions[-1].slots))
# 		return isTrue
# 		#return (self.numSlots == self.totalSlots)
# 		#return False

# 	def violations(self,boolean=False):
# 		if not boolean:
# 			return self.constraint_scores
# 		else:
# 			return [(k,(v>0)) for (k,v) in list(self.constraint_scores.items())]

# 	@cached_property
# 	def violated(self):
# 		viold=[]
# 		for c,viol in list(self.constraint_scores.items()):
# 			if viol:
# 				viold+=[c]
# 		return viold

# 	def constraintScorez(self):
# 		toreturn={}
# 		for c in self.constraints:
# 			toreturn[c]=0
# 			for pos in self.positions:
# 				toreturn[c]+=pos.constraint_scores[c]
# 		return toreturn

# 	# return a representation of the bounding relation between self and parse
# 	def boundingRelation(self, parse):

# 		containsGreaterViolation = False
# 		containsLesserViolation = False

# 		for constraint in self.constraints:
# 			mark = self.constraint_scores[constraint]
# 			mark2 = parse.constraint_scores[constraint]

# 			#print str(mark)+"\t"+str(mark2)

# 			if mark > parse.constraint_scores[constraint]:
# 				containsGreaterViolation = True

# 			if mark < parse.constraint_scores[constraint]:
# 				containsLesserViolation = True

# 		if containsGreaterViolation:

# 			if containsLesserViolation:
# 				return Bounding.unequal # contains both greater and lesser violations

# 			else:
# 				##logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]),self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]))
# 				return Bounding.bounded # contains only greater violations

# 		else:

# 			if containsLesserViolation:
# 				##logging.debug('Parse1: %s\nViols1: %s\n--bounds-->\nParse2: %s\nViols2: %s',self,str([(k,v) for k,v in sorted(self.constraintCounts.items()) if v]),parse,str([(k,v) for k,v in sorted(parse.constraintCounts.items()) if v]))
# 				return Bounding.bounds # contains only lesser violations

# 			else:
# 				return Bounding.equal # contains neither greater nor lesser violations



# import string
# from copy import copy
# from Parse import Parse
# class MeterPosition(Parse):
# 	def __init__(self, meter, meterVal): # meterVal represents whether the position is 's' or 'w'
# 		self.slots=[]
# 		self.children=self.slots
# 		self.meter = meter
# 		self.constraint_scores = {}
# 		for constraint in meter.constraints:
# 			self.constraint_scores[constraint] = 0
# 		self.meterVal = meterVal
# 		for slot in self.slots:
# 			slot.meter=meterVal

# 		self.feat('prom.meter',(meterVal=='s'))
# 		#self.feat('meter',self.meterVal2)
# 		#self.token = ""

# 	def __copy__(self):
# 		other = MeterPosition(self.meter, self.meterVal)
# 		other.slots = self.slots[:]
# 		for k,v in list(self.constraint_scores.items()):
# 			other.constraint_scores[k]=copy(v)
# 		return other

# 	@cached_property
# 	def has_viol(self):
# 		return bool(sum(self.constraint_scores.values()))

# 	@cached_property
# 	def violated(self):
# 		viold=[]
# 		for c,viol in list(self.constraint_scores.items()):
# 			if viol:
# 				viold+=[c]
# 		return viold

# 	@cached_property
# 	def isStrong(self):
# 		return self.meterVal.startswith("s")

# 	def append(self,slot):
# 		#self.token = ""
# 		self.slots.append(slot)

# 	@cached_property
# 	def meterVal2(self):
# 		return ''.join([self.meterVal for x in self.slots])

# 	@cached_property
# 	def mstr(self):
# 		return ''.join([self.meterVal for n in range(len(self.slots))])

# 	def posfeats(self):
# 		posfeats={'prom.meter':[]}
# 		for slot in self.slots:
# 			for k,v in list(slot.feats.items()):
# 				if (not k in posfeats):
# 					posfeats[k]=[]
# 				posfeats[k]+=[v]
# 			posfeats['prom.meter']+=[self.meterVal]

# 		for k,v in list(posfeats.items()):
# 			posfeats[k]=tuple(v)

# 		return posfeats
# 	#
# 	# def __repr__(self):
# 	#
# 	# 	if not self.token:
# 	# 		slotTokens = []
# 	#
# 	# 		for slot in self.slots:
# 	# 			#slotTokens.append(self.u2s(slot.token))
# 	# 			slotTokens.append(slot.token)
# 	#
# 	# 		self.token = '.'.join(slotTokens)
# 	#
# 	# 		if self.meterVal == 's':
# 	# 			self.token = self.token.upper()
# 	# 		else:
# 	# 			self.token = self.token.lower()
# 	# 	return self.token


# 	def __repr__(self):
# 		return self.token

# 	@cached_property
# 	def token(self):
# 		if not hasattr(self,'_token') or not self._token:
# 			token = '.'.join([slot.token for slot in self.slots])
# 			token=token.upper() if self.meterVal=='s' else token.lower()
# 			self._token=token
# 		return self._token





# from entity import entity
# class MeterSlot(entity):
# 	def __init__(self,i,unit,token,wordpos,word,i_word=0,i_syll_in_word=0,wordtoken=None,meter=None):
# 		self.i=i					# eg, could be one of 0-9 for a ten-syllable line
# 		self.children=[unit]
# 		self.token=token
# 		self.featpaths={}
# 		self.wordpos=wordpos
# 		self.word=word
# 		self.issplit=False
# 		self.i_word=i_word
# 		self.i_syll_in_word=i_syll_in_word
# 		self.wordtoken=wordtoken
# 		self.meter=meter

# 		#self.feat('slot.wordpos',wordpos)
# 		self.feat('prom.stress',unit.feature('prom.stress'))
# 		self.feat('prom.strength',unit.feature('prom.strength'))
# 		self.feat('prom.kalevala',unit.feature('prom.kalevala'))
# 		self.feat('prom.weight',unit.children[0].feature('prom.weight'))
# 		self.feat('shape',unit.str_shape())
# 		self.feat('prom.vheight',unit.children[0].feature('prom.vheight'))
# 		self.feat('word.polysyll',self.word.numSyll>1)

# 		## Phrasal stress
# 		self.feat('prom.phrasal_stress',self.phrasal_stress)
# 		self.feat('prom.phrasal_strength',self.phrasal_strength)
# 		self.feat('prom.phrasal_head',self.phrasal_head)

# 	@cached_property
# 	def phrasal_strength(self):
# 		if not self.wordtoken: return None
# 		if self.word.numSyll>1 and self.stress != 'P': return None
# 		if self.wordtoken.feats.get('phrasal_stress_peak',''): return True
# 		if self.wordtoken.feats.get('phrasal_stress_valley',''): return False
# 		return None

# 	@cached_property
# 	def phrasal_head(self):
# 		if not self.wordtoken: return None
# 		if self.word.numSyll>1 and self.stress != 'P': return None
# 		if self.wordtoken.feats.get('phrasal_head',''): return True
# 		return None

# 	@cached_property
# 	def phrasal_stress(self):
# 		if not self.wordtoken: return None
# 		if self.word.numSyll>1 and self.stress != 'P': return None

# 		if self.meter.config.get('phrasal_stress_norm_context_is_sentence',0):
# 			return self.wordtoken.phrasal_stress
# 		else:
# 			return self.wordtoken.phrasal_stress_line


# 	def str_meter(self):
# 		return self.meter

# 	def str_token(self):
# 		if not hasattr(self,'meter'):
# 			return self.token
# 		else:
# 			if self.meter=="s":
# 				return self.token.upper()
# 			else:
# 				return self.token.lower()

# 	@cached_property
# 	def stress(self):
# 		if self.feature('prom.stress')==1.0:
# 			return "P"
# 		elif self.feature('prom.stress')==0.5:
# 			return "S"
# 		elif self.feature('prom.stress')==0.0:
# 			return "U"




