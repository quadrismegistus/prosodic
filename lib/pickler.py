import sys,pickle
sys.path.append('./')
from tools import *

filepath = sys.argv[1]
fileNew = open(filepath+'.pickle','w')
pickle.dump(loadDict(filepath), fileNew)
