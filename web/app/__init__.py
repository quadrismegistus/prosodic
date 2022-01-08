from flask import Flask
from flask_socketio import SocketIO
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
#from flask_login import LoginManager
from flask_basicauth import BasicAuth


app = Flask(__name__)
app.config.from_object('webconfig.Config')
#basic_auth = BasicAuth(app)
#login_manager = LoginManager()
#login_manager.init_app(app)
csrf = CSRFProtect(app)
sess = Session(app)
socketio = SocketIO(app, ping_timeout=3600, async_mode='gevent', manage_session=False)
from app import views