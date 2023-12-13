from .imports import *

def from_json(json_d):
    classname=json_d['_class']
    classx = INITCLASSES[classname]
    return classx.from_json(json_d)

def to_json(obj, fn=None):
    data = obj.to_json()
    if fn:
        os.makedirs(os.path.dirname(fn), exist_ok=True)
        with open(fn,'wb') as of:
            of.write(orjson.dumps(data, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_NUMPY))