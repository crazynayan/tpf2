from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

from config import Config

tpf2_app: Flask = Flask(__name__)
tpf2_app.config.from_object(Config)
bootstrap = Bootstrap(tpf2_app)
login = LoginManager(tpf2_app)
login.login_view = 'login'

# noinspection PyPep8
from client import routes
from client.user import login, logout
from client import test_data_routes
