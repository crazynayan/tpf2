import datetime as dt
import os
from base64 import b64encode
from functools import wraps
from typing import Optional

import pytz
from firestore_ci import FirestoreDocument
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
        if current_user.is_authenticated:
            return route_function(*args, **kwargs)
        user = User.check_token(request.cookies.get("token"))
        if user:
            login_user(user=user)
            return route_function(*args, **kwargs)
        return current_app.login_manager.unauthorized()

    return decorated_route


class User(FirestoreDocument, UserMixin):

    def __init__(self, email: str = None):
        super().__init__()
        self.email: str = email if email else str()
        self.api_key: str = str()
        self.token: str = str()
        self.token_expiration: dt.datetime = dt.datetime.utcnow().replace(tzinfo=pytz.UTC)

    def check_password(self, password: str) -> bool:
        self.api_key = Server().authenticate(self.email, password)
        return True if self.api_key else False

    @classmethod
    def check_token(cls, token) -> Optional["User"]:
        if not token:
            return None
        user = cls.objects.filter_by(token=token).first()
        if user is None or user.token_expiration < dt.datetime.utcnow().replace(tzinfo=pytz.UTC):
            return None
        return user

    def get_token(self, expires_in=Config.TOKEN_EXPIRY) -> str:
        now = dt.datetime.utcnow().replace(tzinfo=pytz.UTC)
        if self.token and self.token_expiration > now + dt.timedelta(seconds=60):
            return self.token
        self.token = b64encode(os.urandom(24)).decode()
        self.token_expiration = now + dt.timedelta(seconds=expires_in)
        return self.token

    def get_id(self) -> str:
        return self.email


User.init("session_users")


@login.user_loader
def load_user(email: str) -> Optional[User]:
    user = User.objects.filter_by(email=email.lower()).first()
    return user


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")


@tpf2_app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template("login.html", title="TPF Analyzer", form=form)
    user = User(form.email.data.lower())
    if not user.check_password(form.password.data):
        flash(f"Invalid email or password.")
        return redirect(url_for("login"))
    User.objects.filter_by(email=user.email).delete()
    token = user.get_token()
    user.set_id(user.create())
    login_user(user=user)
    next_page = request.args.get("next")
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for("home")
    response: Response = make_response(redirect(next_page))
    response.set_cookie("token", token, max_age=Config.TOKEN_EXPIRY, secure=Config.CI_SECURITY, httponly=True,
                        samesite="Strict")
    return response


@tpf2_app.route("/logout")
def logout():
    User.objects.filter_by(email=current_user.email).delete()
    logout_user()
    return redirect(url_for("home"))
