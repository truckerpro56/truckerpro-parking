from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

db = SQLAlchemy()
socketio = SocketIO()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='memory://',  # overridden by RATELIMIT_STORAGE_URI in init_app
)
csrf = CSRFProtect()
login_manager = LoginManager()
