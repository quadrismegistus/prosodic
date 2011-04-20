import sys,sqlite3
sys.path.append('./')
from tools import *

filepath = sys.argv[1]
conn = sqlite3.connect(filepath[:-4]+'.sqlite3')
c = conn.cursor()
c.execute("drop table dict")
c.execute("CREATE TABLE dict (word text, entry text)")
for k,v in loadDict(filepath).items():
	if k.strip() == "": continue
	k = k.replace('"',"''")
	for vv in v:
		vv = vv.replace('"',"''")
		q="INSERT INTO dict VALUES (\"" + str(k) + "\", \"" + str(vv) + "\")"
		c.execute(q)
conn.commit()
c.close()
