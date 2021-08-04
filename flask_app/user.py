from functools import wraps
from typing import Optional

from flask import flash, redirect, url_for, render_template, request, Response, make_response, current_app
from flask_login import UserMixin, current_user, login_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.urls import url_parse
from wtforms import PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from config import Config
from flask_app import tpf2_app, login
from flask_app.server import Server


def cookie_login_required(route_function):
    @wraps(route_function)
    def decorated_route(*args, **kwargs):
        token = request.cookies.get("token")
        if not token:
            return current_app.login_manager.unauthorized()
        if current_user.is_authenticated:
            return route_function(*args, **kwargs)
        email = request.cookies.get("email")
        user = User(email, token)
        login_user(user=user)
        return route_function(*args, **kwargs)

    return decorated_route


class User(UserMixin):
    SEPARATOR: str = "|"

    def __init__(self, email: str = None, api_key: str = None):
        super().__init__()
        self.email: str = email.replace(self.SEPARATOR, "") if email else str()
        self.api_key: str = api_key if api_key else str()

    def __repr__(self):
        return f"{self.email}{self.SEPARATOR}{self.api_key}"

    def check_password(self, password: str) -> bool:
        self.api_key = Server().authenticate(self.email, password)
        return True if self.api_key else False

    def get_id(self) -> str:
        return str(self)


@login.user_loader
def load_user(user_key: str) -> Optional[User]:
    if User.SEPARATOR not in user_key:
        return None
    email, token = user_key.split(User.SEPARATOR)
    return User(email, token)


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


@tpf2_app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("login.html", title="TPF Analyzer", form=form)
    user = User(form.email.data.lower())
    if not user.check_password(form.password.data):
        flash(f"Invalid email or password.")
        return redirect(url_for("login"))
    login_user(user=user)
    next_page = request.args.get("next")
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for("home")
    response: Response = make_response(redirect(next_page))
    response.set_cookie("token", user.api_key, max_age=Config.TOKEN_EXPIRY, secure=Config.CI_SECURITY, httponly=True,
                        samesite="Strict")
    response.set_cookie("email", user.email, max_age=Config.TOKEN_EXPIRY, secure=Config.CI_SECURITY, httponly=True,
                        samesite="Strict")
    return response


@tpf2_app.route("/logout")
def logout() -> Response:
    if current_user.is_authenticated:
        logout_user()
    response: Response = make_response(redirect(url_for("home")))
    response.set_cookie("token", str(), max_age=Config.TOKEN_EXPIRY, secure=Config.CI_SECURITY, httponly=True,
                        samesite="Strict")
    return response
