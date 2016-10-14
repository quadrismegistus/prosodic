import os,imp
meter_dir=os.path.dirname(__file__)
d={}
for fn in os.listdir(meter_dir):
	if not fn.endswith('.py') or fn.startswith('_'): continue
	idx=fn.replace('.py','').replace('-','_')
	d[idx]=imp.load_source(idx, os.path.join(meter_dir,fn))
