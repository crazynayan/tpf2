from flask import render_template, url_for, redirect, flash, session, request
from flask_login import login_required
from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import StringField, SubmitField, BooleanField
from wtforms.validators import DataRequired, ValidationError

from client import tpf2_app
from server.server import server


class TestDataForm(FlaskForm):
    name = StringField('Name of Test Data (Must be unique in the system)', validators=[DataRequired()])
    seg_name = StringField('Segment Name (Must exists in the system)', validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_seg_name(_, seg_name):
        seg_name.data = seg_name.data.upper()
        seg_name = seg_name.data
        if seg_name not in server.segments():
            message = f"{seg_name} not found."
            flash(message)
            raise ValidationError(message)


class ConfirmForm(FlaskForm):
    confirm = SubmitField('Confirm - Create Test Data')


class RegisterForm(FlaskForm):
    r0 = BooleanField('R0')
    r1 = BooleanField('R1')
    r2 = BooleanField('R2')
    r3 = BooleanField('R3')
    r4 = BooleanField('R4')
    r5 = BooleanField('R5')
    r6 = BooleanField('R6')
    r7 = BooleanField('R7')
    r8 = BooleanField('R8')
    r9 = BooleanField('R9')
    r10 = BooleanField('R10')
    r11 = BooleanField('R11')
    r12 = BooleanField('R12')
    r13 = BooleanField('R13')
    r14 = BooleanField('R14')
    r15 = BooleanField('R15')
    save = SubmitField('Save & Continue - Add Further Data')


@tpf2_app.route('/test_data')
@login_required
def get_all_test_data():
    test_data_list = server.get_all_test_data()
    return render_template('test_data_list.html', title='Test Data', test_data_list=test_data_list)


@tpf2_app.route('/test_data/<string:test_data_id>')
@login_required
def get_test_data(test_data_id):
    test_data = server.get_test_data(test_data_id)
    return render_template('test_data_view.html', title='Test Data', test_data=test_data)


@tpf2_app.route('/test_data/<string:test_data_id>/run')
@login_required
def test_data_run(test_data_id: str):
    test_data = server.run_test_data(test_data_id)
    return render_template('test_data_result.html', title='Results', test_data=test_data)


@tpf2_app.route('/test_data/main', methods=['GET', 'POST'])
@login_required
def create_test_data():
    test_data_form: dict = session.get('test_data', None) if request.method == 'GET' else None
    form = TestDataForm(formdata=MultiDict(test_data_form)) if test_data_form else TestDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Create Test Data', form=form)
    test_data = session.get('test_data', None)
    if test_data:
        test_data['name'] = form.name.data
        test_data['seg_name'] = form.seg_name.data
    else:
        test_data = form.data
        test_data['outputs'] = dict()
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))


@tpf2_app.route('/test_data/confirm', methods=['GET', 'POST'])
@login_required
def confirm_test_data():
    test_data = session.get('test_data', None)
    if not test_data:
        flash('Create Test Data')
        return redirect(url_for('create_test_data'))
    form = ConfirmForm()
    if not form.validate_on_submit():
        return render_template('test_data_confirm.html', title='Confirm Test Data', test_data=test_data, form=form)
    if not test_data['outputs']:
        flash('You need to add at least one output')
        return redirect(url_for('confirm_test_data'))
    flash('Test Data Created')
    session.pop('test_data')
    return redirect(url_for('home'))


@tpf2_app.route('/test_data/outputs/registers', methods=['GET', 'POST'])
@login_required
def add_output_registers():
    test_data = session.get('test_data', None)
    if not test_data:
        flash('Create Test Data')
        return redirect(url_for('create_test_data'))
    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Registers', form=form)
    registers = [value for reg, value in vars(form).items()
                 if reg.startswith('r') and isinstance(value, BooleanField)]
    test_data['outputs']['regs'] = {reg.label.text: 0 for reg in registers if reg.data}
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))
