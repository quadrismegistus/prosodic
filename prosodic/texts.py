from .imports import *
from .constraints import DEFAULT_CONSTRAINTS
from .parsing import ParseList


class Text(entity):
	sep: str = ''
	child_type: str = 'Stanza'

	def __init__(self,
			txt: str = '',
			filename: str = '',
			lang: Optional[str] = DEFAULT_LANG,
			parent: Optional[entity] = None,
			children: Optional[list] = None,
			init: bool = True,
			**kwargs
			):
		if not txt and not filename and not children:
			raise Exception('must provide either txt, filename, or children objects')

		self._txt = get_txt(txt,filename)
		if self.is_text: self._txt=self._txt.strip()
		
		self.fn = filename

		if self.__class__.__name__ == 'Text':
			self.lang=lang if lang else (detect_lang(self._txt) if self._txt else '??')
		
		self.parent = parent
		self.children = [] if children is None else children
		self._attrs = kwargs
		self.is_parsed = False
		for k,v in self._attrs.items(): setattr(self,k,v)
		self._init = False
		if init: self.init()

	@cached_property
	def words_df(self): 
		odf=pd.DataFrame(tokenize_sentwords_iter(self.txt))
		odf=odf.set_index(['stanza_i','sent_i','sentpart_i','line_i','word_i','word_str'])
		return odf
	@property
	def lines_df(self): 
		odf=pd.DataFrame(l.attrs for l in self.lines)
		odf=odf.set_index(['stanza_i','sent_i','sentpart_i','line_i'])
		return odf

	@profile
	def init(self):
		if self._init: return self
		self._init=True
		from .lines import Stanza, Line
		from .words import Word
		logger.trace(self.__class__.__name__)

		df = self.words_df.reset_index()
		text_stanzas = []
		for stanza_i,stanza_df in df.groupby('stanza_i'):
			stanza_d = {k:v for k,v in dict(stanza_df.iloc[0]).items() if k.split('_')[0] not in {'word','line'}}
			stanza_lines = []
			for line_i,line_df in stanza_df.groupby('line_i'):
				line_words = []
				line_d = {k:v for k,v in dict(line_df.iloc[0]).items() if k.split('_')[0] not in {'word'}}
				for i,word_row in line_df.iterrows():
					word_d=dict(word_row)
					word_d['word_lang'] = self.lang
					token = word_row.word_str
					wordforms = self.lang_obj.get(token.strip())
					word = Word(token, children=wordforms, **word_d)
					line_words.append(word)
				line = Line(children=line_words, **line_d)
				for word in line_words: word.parent = line
				stanza_lines.append(line)
			stanza = Stanza(children=stanza_lines, parent=self, **stanza_d)
			for line in stanza_lines: line.parent = stanza
			text_stanzas.append(stanza)
		self.children = text_stanzas
		return self

	@property
	def attrs(self):
		return {'txt':self.txt.strip(), **self._attrs}


	@property
	def txt(self):
		logger.trace(self.__class__.__name__)
		if hasattr(self,'_txt') and self._txt: txt = self._txt
		elif self.children: txt=self.sep.join(child.txt for child in self.children)
		else: txt=''
		return clean_text(txt)

	@cached_property
	def lang_obj(self):
		logger.trace(self.__class__.__name__)
		from .langs import English
		if self.lang=='en': return English()

	# @cache
	@profile
	def parse(self, constraints=DEFAULT_CONSTRAINTS, max_s=METER_MAX_S, max_w=METER_MAX_W, num_proc=1, progress=True, resolve_optionality=METER_RESOLVE_OPTIONALITY, categorical_constraints=DEFAULT_CATEGORICAL_CONSTRAINTS):
		kwargs=dict(
			constraints=constraints, 
			max_s=max_s, 
			max_w=max_w, 
			num_proc=1, 
			progress=False,
			resolve_optionality=resolve_optionality,
			categorical_constraints=categorical_constraints
		)
		parse_objs = self.lines
		objs = [(line,kwargs) for line in parse_objs]
		supermap(
			parse_line_mp,
			objs,
			num_proc=num_proc,
			progress=progress,
			desc='Parsing lines'
		)
		self.is_parsed = True
		return self.parses_df

	@property
	def best_parses(self):
		return ParseList([l.best_parse for l in self.lines])
	
	@property
	def parses_df_exact(self):
		if not self.is_parsed: return self.parse()
		odf=pd.DataFrame([l.parse_stats for l in self.lines])
		odf=odf.set_index(['stanza_i','sent_i','sentpart_i','line_i','txt','parse'])
		return odf
	
	@property
	def parses_df(self):
		return self.parses_df_exact.fillna(0).round(1).applymap(lambda x: x if x else '')
	


@profile
def parse_line_mp(args):
	from .lines import Line
	line,kwargs = args
	# line = Line(line_str)
	# logger.debug(line)
	parse=line.parse(**kwargs)
	# logger.debug(parse)
	return parse
    

class Subtext(Text): 
	def init(self): return self