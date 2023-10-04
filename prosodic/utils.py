from .imports import *

# loading txt/strings
def get_fn_txt(txt_or_fn):
    # load txt
    if type(txt_or_fn)==str and not '\n' in txt_or_fn and os.path.exists(txt_or_fn):
        fn=txt_or_fn
        with open(fn,encoding='utf-8',errors='replace') as f:
            txt=f.read()
    else:
        fn=''
        txt=txt_or_fn
    return (fn,txt)

def get_txt(txt,fn):
    if txt: return txt
    if fn and os.path.exists(fn):
        with open(fn) as f:
            return f.read()
    return ''


def clean_text(txt):
    txt=txt.replace('\r\n','\n').replace('\r','\n')
    txt=ftfy.fix_text(txt)
    return txt

def get_name(txt):
    return txt.strip().split('\n')[0].strip()

def get_attr_str(attrs, sep=', '):
    strs=[f'{k}={repr(v)}' for k,v in attrs.items() if v is not None]
    attrstr=sep.join(strs)
    return attrstr

# @profile
def safesum(l):
    # o=pd.Series(pd.to_numeric(l,errors='coerce')).sum()
    # o_int=int(o)
    # o_float = float(o)
    # return o_int if o_int==o_float else o_float
    l = [x for x in l if type(x) in {int,float,np.float64,np.float32}]
    return sum(l)


def supermap(func, objs, progress=True, desc=None):
    if progress and not desc: desc=f'Mapping {func.__name__} across {len(objs)} objects'
    return [func(obj) for obj in tqdm(objs,desc=desc,disable=not progress)]

def setindex(df, cols=[]):
    if not cols: return df
    cols=[c for c in cols if c in set(df.columns)]
    return df.set_index(cols) if cols else df

def split_scansion(wsws:str) -> list:
    positions=[]
    position=[]
    last_x=None
    for x in wsws:
        if last_x and last_x!=x and position:
            positions.append(position)
            position=[]
        position.append(x)
        last_x=x
    if position: positions.append(position)
    return [''.join(pos) for pos in positions]


@cache
def get_possible_scansions(nsyll, max_s=METER_MAX_S, max_w=METER_MAX_W):
    if max_s is None: max_s = nsyll
    if max_w is None: max_w = nsyll
    return [l for l in iter_mpos(nsyll,max_s=max_s,max_w=max_w) if getlenparse(l)==nsyll]



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

