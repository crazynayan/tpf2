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
from flask_app import routes
from flask_app.user import login, logout
from flask_app import test_data_routes
