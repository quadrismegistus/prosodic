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

def get_attr_str(attrs):
    strs=[f'{k}={v.strip() if type(v)==str else v}' for k,v in attrs.items()]
    attrstr=' '.join(f'{x}' for x in strs)
    attrstr=f' [{attrstr}]' if attrstr else ''
    return attrstr

def safesum(l):
    o=pd.Series(pd.to_numeric(l,errors='coerce')).sum()
    o_int=int(o)
    o_float = float(o)
    return o_int if o_int==o_float else o_float