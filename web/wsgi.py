import sys,os
sys.path.insert(0,os.path.abspath('..'))
import prosodic
print(prosodic.__file__)

from app import app,socketio
if __name__ == "__main__":
    # socketio.run(app,host='0.0.0.0',port=5002,debug=True)
    socketio.run(app,host='0.0.0.0',port=80,debug=False)

