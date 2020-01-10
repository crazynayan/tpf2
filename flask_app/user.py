from typing import Optional

from firestore_ci import FirestoreDocument
from flask import flash, redirect, url_for, render_template, request, session
from flask_login import UserMixin, current_user, login_user, logout_user
from flask_wtf import FlaskForm
from werkzeug.urls import url_parse
from wtforms import PasswordField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired

from flask_app import tpf2_app, login
from flask_app.server import Server


class User(FirestoreDocument, UserMixin):

    def __init__(self, email: str = None):
        super().__init__()
        self.email: str = email if email else str()
        self.token: str = str()

    def check_password(self, password: str) -> bool:
        self.token = Server().authenticate(self.email, password)
        return True if self.token else False


User.init('session_users')


@login.user_loader
def load_user(user_id: str) -> Optional[User]:
    user = User.get_by_id(user_id)
    return user if user and user.token else None


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')


@tpf2_app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template('login.html', title='Sign In', form=form)
    user = User(form.email.data)
    if not user.check_password(form.password.data):
        flash(f"Invalid email or password.")
        return redirect(url_for('login'))
    User.objects.filter_by(email=user.email).delete()
    user.set_id(user.create())
    login_user(user=user)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('home')
    return redirect(next_page)


@tpf2_app.route('/logout')
def logout():
    session.pop('test_data', None)
    session.pop('pnr', None)
    User.objects.filter_by(email=current_user.email).delete()
    logout_user()
    return redirect(url_for('home'))
