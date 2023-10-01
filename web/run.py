import sys,os
sys.path.insert(0,os.path.abspath('..'))
import prosodic
from app import app,socketio
socketio.run(app,host='0.0.0.0',port=5002,debug=True)
