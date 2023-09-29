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
