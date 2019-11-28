from flask import flash, redirect, url_for, render_template, request, session
from flask_login import UserMixin, current_user, login_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.urls import url_parse
from wtforms import PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from client import tpf2_app, login
from server.server import Server


class User(UserMixin):

    def __init__(self, email: str):
        self.email: str = email
        self.id: str = email
        self.server: Server = Server(email)

    def check_password(self, password: str) -> bool:
        return self.server.authenticate(password)


@login.user_loader
def load_user(user_email: str) -> User:
    user = User(user_email)
    user.server.auth_header = session.get('tpf_user', dict())
    return user


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


@tpf2_app.route('/login', methods=['GET', 'POST'])
def login() -> str:
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template('login.html', title='Sign In', form=form)
    user = User(form.email.data)
    if not user.check_password(form.password.data):
        flash(f"Invalid email or password.")
        return redirect(url_for('login'))
    session['tpf_user'] = user.server.auth_header
    login_user(user=user)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('home')
    return redirect(next_page)


@tpf2_app.route('/logout')
def logout():
    session.pop('test_data', None)
    session.pop('pnr', None)
    session.pop('tpf_user', None)
    logout_user()
    return redirect(url_for('home'))
