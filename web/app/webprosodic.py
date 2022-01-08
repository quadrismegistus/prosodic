from prosodic import *

### METER

METERS=None
def get_meters(mdir=dir_meters):
	global METERS
	if METERS is None:
		METERS=loadMeters(dir_meters)
	return METERS


def default_meter(default='default_english'):
	meters=get_meters()
	md=meters[default].config
	md['constraints'].sort()
	return md

def json2meter(data,non_constraints={'maxS','maxW','splitheavies'},name='web',id='web'):
	dd={}
	data.sort(key=lambda d: d['name'])
	for row in data:
		name,val = row['name'],row['value']
		#print name,val
		dd[name]=val

	for name,val in list(dd.items()):
		if name.endswith('_weight') and not name[:-len('_weight')] in dd:
			dd[name[:-len('_weight')]]=name[:-len('_weight')]

	config={'constraints':[]}
	config['splitheavies']=0
	for name,val in list(dd.items()):
		if name.endswith('_weight') or name.endswith('_check'): continue
		if name in non_constraints:
			config[name]=int(val)
		else:
			if not dd.get(name+'_check',None): continue
			realname=val
			weight=dd.get(name+'_weight',None)
			if not weight:
				raise Exception("There should be a weight assigned to this constraint: "+name)
			#print name,realname,weight
			config['constraints']+=[realname+'/'+str(weight)]

	if not 'name' in config: config['name']=name
	if not 'id' in config: config['id']=id
	config['constraints'].sort()
	return config

def clear_sess(session):
	if 'meter' in sess: del session['meter']

def get_meter(session):
	if 'meter' in session and session['meter']:
		md=session['meter']
		from Meter import Meter
		return Meter(md)
	else:
		return None

#### PARSING

brackets='||||||||||'
brackets2=brackets + brackets
# line_hdr = brackets+'line'+brackets
# parse_hdr = brackets2+'parse'+brackets2
# meter_hdr = '||||meter||||'
line_hdr = 'line'
parse_hdr = 'parse'
meter_hdr = 'meter'

def ld2table(header,ld,html_id=None,html_class=None,widths={}):
	table="<table"
	if html_id: table+=' id="%s"' % html_id
	if html_class: table+=' class="%s"' % html_class
	table+=">\n\t<thead>\n\t\t<tr>"
	for h in header:
		if not h in widths:
			table+='\n\t\t\t<th>'+h+'</th>'
		else:
			table+='\n\t\t\t<th style="width: %spx">' % widths[h] + h + '</th>'
	table+='\n\t\t</tr>\n\t</thead>\n\t<tbody>'
	for d in ld:
		table+='\n\t\t<tr>'
		for h in header:
			table+='\n\t\t\t<td>'+str(d.get(h,''))+'</td>'
		table+='\n\t\t</tr>'
	table+='\n\t</tbody>\n</table>'
	return table

def html_parse(parse,viols=False,use_caps=False,use_html=True,between_words=' ',between_sylls='.',line_id='ID'):
	last_word = None
	output=''
	for pos in parse.positions:
		violated=pos.violated
		if viols and violated:
			viol_str=' '.join([rename_constraint(c) for c in violated])
			viol_title = 'Violated %s constraints: %s' % (len(violated), viol_str)
			output+='<span class="violation" title="%s" id="viol__line_%s">' % (viol_title,line_id)

		for slot in pos.slots:
			slotstr=slot.token
			if use_caps: slotstr=slotstr.upper() if pos.meterVal=='s' else slotstr.lower()
			if use_html: slotstr='<span class="meter_strong">'+slotstr+'</span>' if pos.meterVal=='s' else '<span class="meter_weak">'+slotstr+'</span>'
			if last_word != slot.wordtoken:
				output+=between_words+slotstr
				last_word=slot.wordtoken
			else:
				output+=between_sylls+slotstr

		if viols and violated:
			output+='</span><script type="text/javascript">tippy("#viol__line_%s")</script>' % line_id

	return output.strip()

def rename_constraint(c):
	x=c.name_weight
	x=x.replace('_',' ')
	x=x.replace('.',' ')
	x=x.replace('=>','→')
	return x


class WebText(Text):
	"""
	A class extending Prosodc's Text class designed to output useful html.

	What we want:
	- Sortable line by line table html including:
		- line
		- parse
		- meter?
		- num viols and other stats
		- grid?
	- that can then be exported
	"""


	def meter2columns(self,meter=None):
		meter=self.get_meter(meter)
		constraint_names = [rename_constraint(c) for c in sorted(meter.constraints,key=lambda _c: _c.name)]
		header = ['#',line_hdr, parse_hdr, meter_hdr, '# syll', '# parse', '# viol'] + constraint_names
		return header

	def iparse_rows(self,meter=None,all_parses=True,viols=True):
		meter=self.get_meter(meter)
		for line_i,line in enumerate(self.iparse(meter=meter)):
			dx={'#':line_i+1, line_hdr:str(line)}
			bp=line.bestParse(meter)
			ap=line.allParses(meter)
			dx['# parse']='<a class="numparses" href="#" id="numparse__line_%s" onclick="show_alternate_parses(%s)">%s</a>' % (line_i+1,line_i+1,len(ap))
			for k,v in list(parse2dict(bp,meter,line_id=line_i+1).items()): dx[k]=v

			dx['all_parses'] = parses = []
			if all_parses:
				for api,parse in enumerate(ap):
					dx2={'#':api+1, line_hdr:str(line), '# parse':''}
					for k,v in list(parse2dict(parse,meter,line_id=str(line_i+1)+'_'+str(api+1)).items()): dx2[k]=v
					parses+=[dx2]
			yield dx


def parse2dict(bp,meter,line_id='ID'):
	dx={}
	dx[parse_hdr]=html_parse(bp,use_caps=True,use_html=True,between_sylls='.',between_words=' ',viols=True,line_id=line_id)
	dx[meter_hdr]=bp.str_meter() if bp else ''
	dx['# viol'] = bp.totalCount if bp else ''
	#dx['score_viols'] = bp.score() if bp else ''
	dx['# syll']=bp.num_sylls if bp else ''
	for c in sorted(meter.constraints,key=lambda _c: _c.name):
		if bp and c in bp.constraintScores:
			val=bp.constraintScores[c]
			if int(val)==val: val=int(val)
		else:
			val=''
		dx[rename_constraint(c)]=val
	return dx




def check_constraint(meterd,name,ctype='option'):
	constraints = meterd['constraints']
	toreturn = None
	if ctype=='option': toreturn = 'selected'
	if ctype=='checkbox': toreturn = 'checked'

	for c in constraints:
		if type(name) in [str,str]:
			if c.startswith(name):
				if ctype=='weight': toreturn = c.split('/')[1]
				return toreturn
		elif type(name) in [list,tuple,set]:
			for nm in name:
				if c.startswith(nm):
					if ctype=='weight': toreturn = c.split('/')[1]
					return toreturn

	return '1' if ctype=='weight' else ''
