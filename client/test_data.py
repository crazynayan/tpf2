from urllib.parse import quote, unquote

from flask import render_template, url_for, redirect, flash, session, request
from flask_login import login_required
from flask_wtf import FlaskForm
from werkzeug.datastructures import MultiDict
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, ValidationError, NumberRange

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


class DeleteForm(FlaskForm):
    delete = SubmitField('Delete - This Test Data (Permanently)')


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


class FieldSearchForm(FlaskForm):
    field = StringField('Field name', validators=[DataRequired()])
    search = SubmitField('Search')

    @staticmethod
    def validate_field(_, field):
        field.data = field.data.upper()


class FieldLengthForm(FlaskForm):
    length = IntegerField('Length', validators=[NumberRange(1, 4095, "Length can be from 1 to 4095")])
    base_reg = StringField('Base Register - Keep it R0 for default macros like AAA, ECB, GLOBAL, IMG etc.',
                           default='R0', validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_base_reg(_, base_reg):
        base_reg.data = base_reg.data.upper()
        if base_reg.data and base_reg.data not in tpf2_app.config['REGISTERS']:
            flash('Use a valid Base Register')
            raise ValidationError('Invalid Base Register')


@tpf2_app.route('/test_data')
@login_required
def get_all_test_data():
    test_data_list = server.get_all_test_data()
    return render_template('test_data_list.html', title='Test Data', test_data_list=test_data_list)


@tpf2_app.route('/test_data/<string:test_data_id>', methods=['GET', 'POST'])
@login_required
def get_test_data(test_data_id):
    test_data = server.get_test_data(test_data_id)
    if not test_data:
        flash('There was some error in retrieving the test data')
        return redirect(url_for('get_all_test_data'))
    form = DeleteForm()
    if not form.validate_on_submit():
        return render_template('test_data_view.html', title='Test Data', test_data=test_data, form=form)
    response = server.delete_test_data(test_data_id)
    if not response:
        flash('There was some error in deleting test data')
    return redirect(url_for('get_all_test_data'))


@tpf2_app.route('/test_data/<string:test_data_id>/run')
@login_required
def test_data_run(test_data_id: str):
    test_data = server.run_test_data(test_data_id)
    return render_template('test_data_result.html', title='Results', test_data=test_data)


@tpf2_app.route('/test_data/create', methods=['GET', 'POST'])
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


@tpf2_app.route('/test_data/cancel')
@login_required
def cancel_test_data():
    session.pop('test_data')
    return redirect(url_for('get_all_test_data'))


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
    response: dict = server.create_test_data(session['test_data'])
    if not response:
        flash('There was some error in creating test data')
    session.pop('test_data')
    return redirect(url_for('get_all_test_data'))


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


@tpf2_app.route('/test_data/outputs/fields', methods=['GET', 'POST'])
@login_required
def search_output_fields():
    test_data = session.get('test_data', None)
    if not test_data:
        flash('Create Test Data')
        return redirect(url_for('create_test_data'))
    form = FieldSearchForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Search Fields', form=form)
    field_name = form.field.data
    label_ref = server.search_field(field_name)
    if not label_ref:
        flash('Field name not found')
        return redirect(url_for('search_fields'))
    field_name = quote(label_ref['label'])
    macro_name = label_ref['name']
    length = label_ref['length']
    return redirect(url_for('add_output_field', field_name=field_name, macro_name=macro_name, length=length))


@tpf2_app.route('/test_data/outputs/fields/add', methods=['GET', 'POST'])
@login_required
def add_output_field():
    test_data = session.get('test_data', None)
    if not test_data:
        flash('Create Test Data')
        return redirect(url_for('create_test_data'))
    field_name = unquote(request.args.get('field_name', str()))
    macro_name = request.args.get('macro_name', str())
    if 'cores' not in test_data['outputs']:
        test_data['outputs']['cores'] = list()
    cores = test_data['outputs']['cores']
    core = next((core for core in cores if core['macro_name'] == macro_name), None)
    form = FieldLengthForm()
    form_data = form.data
    form_data['length'] = request.args.get('length', 1, type=int)
    if core:
        form_data['base_reg'] = core['base_reg']
    form = FieldLengthForm(formdata=MultiDict(form_data)) if request.method == 'GET' else FieldLengthForm()
    if not form.validate_on_submit():
        for error in form.length.errors:
            flash(error)
        return render_template('test_data_field_form.html', title='Add Field', field_name=field_name,
                               macro_name=macro_name, form=form)
    if form.base_reg.data == 'R0' and macro_name not in tpf2_app.config['DEFAULT_MACROS']:
        flash(f'Base Register cannot be R0 for macro {macro_name}')
    if not core:
        core = {'macro_name': macro_name, 'base_reg': form.base_reg.data, 'field_bytes': list()}
        cores.append(core)
    field_byte = next((field_byte for field_byte in core['field_bytes']
                       if field_byte['field'] == field_name), None)
    if not field_byte:
        field_byte = {'field': field_name}
        core['field_bytes'].append(field_byte)
    field_byte['length'] = form.length.data
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))
