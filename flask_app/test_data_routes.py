from functools import wraps
from typing import List
from urllib.parse import quote, unquote

from flask import render_template, url_for, redirect, flash, session, request, Response
from flask_login import login_required
from werkzeug.datastructures import MultiDict
from wtforms import BooleanField

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.test_data_forms import DeleteForm, TestDataForm, ConfirmForm, FieldSearchForm, FieldLengthForm, \
    FieldDataForm, RegisterForm, RegisterFieldDataForm, PnrForm


def test_data_required(func):
    @wraps(func)
    def test_data_wrapper(*args, **kwargs):
        if not session.get('test_data', None):
            flash('Create Test Data')
            return redirect(url_for('create_test_data'))
        return func(*args, **kwargs)

    return test_data_wrapper


@tpf2_app.route('/test_data')
@login_required
def get_all_test_data():
    test_data_list = Server.get_all_test_data()
    return render_template('test_data_list.html', title='Test Data', test_data_list=test_data_list)


@tpf2_app.route('/test_data/<string:test_data_id>', methods=['GET', 'POST'])
@login_required
def get_test_data(test_data_id):
    test_data = Server.get_test_data(test_data_id)
    if not test_data:
        flash('There was some error in retrieving the test data')
        return redirect(url_for('get_all_test_data'))
    form = DeleteForm()
    if not form.validate_on_submit():
        return render_template('test_data_view.html', title='Test Data', test_data=test_data, form=form)
    response = Server.delete_test_data(test_data_id)
    if not response:
        flash('There was some error in deleting test data')
    return redirect(url_for('get_all_test_data'))


@tpf2_app.route('/test_data/<string:test_data_id>/run')
@login_required
def test_data_run(test_data_id: str):
    test_data = Server.run_test_data(test_data_id)
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


@tpf2_app.route('/test_data/<string:test_data_id>/copy')
@login_required
def copy_test_data(test_data_id):
    test_data = Server.get_test_data(test_data_id)
    if not test_data:
        flash('There was some error in retrieving the test data')
        return redirect(url_for('get_all_test_data'))
    test_data_form = TestDataForm().data
    session['test_data'] = {**test_data_form, **test_data}
    return redirect(url_for('create_test_data'))


@tpf2_app.route('/test_data/cancel')
@login_required
def cancel_test_data():
    session.pop('test_data')
    return redirect(url_for('get_all_test_data'))


@tpf2_app.route('/test_data/confirm', methods=['GET', 'POST'])
@login_required
@test_data_required
def confirm_test_data():
    test_data = session['test_data']
    session.pop('pnr', None)
    form = ConfirmForm()
    if not form.validate_on_submit():
        return render_template('test_data_confirm.html', title='Confirm Test Data', test_data=test_data, form=form)
    if not test_data['outputs']:
        flash('You need to add at least one output')
        return redirect(url_for('confirm_test_data'))
    response: dict = Server.create_test_data(session['test_data'])
    if not response:
        flash('There was some error in creating test data')
    session.pop('test_data')
    return redirect(url_for('get_all_test_data'))


@tpf2_app.route('/test_data/outputs/registers', methods=['GET', 'POST'])
@login_required
@test_data_required
def add_output_registers():
    test_data = session['test_data']
    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Registers', form=form)
    registers = [value for reg, value in vars(form).items()
                 if reg.startswith('r') and isinstance(value, BooleanField)]
    test_data['outputs']['regs'] = {reg.label.text: 0 for reg in registers if reg.data}
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))


def _search_field(redirect_route: str) -> Response:
    form = FieldSearchForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Search Fields', form=form)
    label_ref = form.field.data
    field_name = quote(label_ref['label'])
    macro_name = label_ref['name']
    length = label_ref['length']
    return redirect(url_for(redirect_route, field_name=field_name, macro_name=macro_name, length=length))


@tpf2_app.route('/test_data/outputs/fields', methods=['GET', 'POST'])
@login_required
@test_data_required
def search_output_fields() -> Response:
    return _search_field('add_output_field')


@tpf2_app.route('/test_data/inputs/fields', methods=['GET', 'POST'])
@login_required
@test_data_required
def search_input_fields():
    return _search_field('add_input_field')


@tpf2_app.route('/test_data/outputs/fields/add', methods=['GET', 'POST'])
@login_required
@test_data_required
def add_output_field():
    test_data = session['test_data']
    field_name = unquote(request.args.get('field_name', str()))
    macro_name = request.args.get('macro_name', str())
    if 'cores' not in test_data['outputs']:
        test_data['outputs']['cores'] = list()
    cores = test_data['outputs']['cores']
    core = next((core for core in cores if core['macro_name'] == macro_name), None)
    form = FieldLengthForm(macro_name)
    form_data = form.data
    form_data['length'] = request.args.get('length', 1, type=int)
    if core:
        form_data['base_reg'] = core['base_reg']
    form = FieldLengthForm(macro_name, formdata=MultiDict(form_data)) \
        if request.method == 'GET' else FieldLengthForm(macro_name)
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title=f"{field_name} ({macro_name})", form=form)
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


def _encode_data(hex_data: str) -> List[str]:
    number_data = 'NA'
    if len(hex_data) <= 8:
        number_data = int(hex_data, 16)
        if number_data > 0x7FFFFFFF:
            number_data -= tpf2_app.config['REG_MAX'] + 1
    char_data = bytes.fromhex(hex_data).decode('cp037')
    return [hex_data, number_data, char_data]


def _add_field_byte(parent_list: list, field_name: str, hex_data: str) -> None:
    field_byte = next((field_byte for field_byte in parent_list if field_byte['field'] == field_name), None)
    if not field_byte:
        field_byte = {'field': field_name}
        parent_list.append(field_byte)
    field_byte['data'] = _encode_data(hex_data)


@tpf2_app.route('/test_data/inputs/fields/add', methods=['GET', 'POST'])
@login_required
@test_data_required
def add_input_field():
    test_data = session['test_data']
    field_name = unquote(request.args.get('field_name', str()))
    macro_name = request.args.get('macro_name', str())
    form = FieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title=f"{field_name} ({macro_name})", form=form)
    if 'cores' not in test_data:
        test_data['cores'] = list()
    cores = test_data['cores']
    core = next((core for core in cores if core['macro_name'] == macro_name), None)
    if not core:
        core = {'macro_name': macro_name, 'field_bytes': list()}
        cores.append(core)
    _add_field_byte(core['field_bytes'], field_name, form.field_data.data)
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))


@tpf2_app.route('/test_data/inputs/registers', methods=['GET', 'POST'])
@login_required
@test_data_required
def add_input_registers():
    test_data = session['test_data']
    form = RegisterFieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_field_form.html', title='Provide Register Values', form=form)
    if 'regs' not in test_data:
        test_data['regs'] = dict()
    test_data['regs'][form.reg.data] = _encode_data(form.field_data.data)[:2]
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))


@tpf2_app.route('/test_data/inputs/pnr', methods=['GET', 'POST'])
@login_required
@test_data_required
def add_input_pnr():
    pnr_form: dict = session.get('pnr', None) if request.method == 'GET' else None
    form = PnrForm(formdata=MultiDict(pnr_form)) if pnr_form else PnrForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add PNR element', form=form)
    pnr_form = {**pnr_form, **form.data} if pnr_form else form.data
    pnr_form['text_list'] = form.text_data.data.split(',')
    if 'field_bytes' not in pnr_form:
        pnr_form['field_bytes'] = list()
    session['pnr'] = pnr_form
    return redirect(url_for('confirm_pnr'))


@tpf2_app.route('/test_data/inputs/pnr/confirm', methods=['GET', 'POST'])
@login_required
@test_data_required
def confirm_pnr():
    pnr_form = session.get('pnr', None)
    if not pnr_form:
        flash("Add PNR Elements")
        return redirect(url_for('add_input_pnr'))
    form = ConfirmForm()
    if not form.validate_on_submit():
        return render_template('test_data_pnr_form.html', title='Confirm PNR', pnr=pnr_form, form=form)
    if pnr_form['field_bytes'] and pnr_form['text_data']:
        pnr_form['text_data'] = str()
        flash("Remove PNR Text to save")
        return redirect(url_for('add_input_pnr'))
    if not pnr_form['field_bytes'] and not pnr_form['text_data']:
        flash('Either PNR Text or PNR Fields is required')
        return redirect(url_for('add_input_pnr'))
    test_data = session['test_data']
    if 'pnr' not in test_data:
        test_data['pnr'] = list()
    pnr = dict()
    pnr['key'] = pnr_form['key']
    pnr['locator'] = pnr_form['locator']
    pnr['field_bytes'] = pnr_form['field_bytes']
    if pnr_form['text_list']:
        for pnr_text in pnr_form['text_list']:
            pnr['data'] = pnr_text
            test_data['pnr'].append(pnr)
            pnr = pnr.copy()
    else:
        test_data['pnr'].append(pnr)
    test_data['pnr'].sort(key=lambda pnr_element: (pnr_element['locator'], pnr_element['key']))
    session['test_data'] = test_data
    return redirect(url_for('confirm_test_data'))


@tpf2_app.route('/test_data/inputs/pnr/fields', methods=['GET', 'POST'])
@login_required
@test_data_required
def search_pnr_fields():
    return _search_field('add_pnr_field')


@tpf2_app.route('/test_data/inputs/pnr/fields/add', methods=['GET', 'POST'])
@login_required
def add_pnr_field():
    pnr = session.get('pnr', None)
    if not pnr:
        flash('Create PNR Element')
        return redirect(url_for('add_input_pnr'))
    field_name = unquote(request.args.get('field_name', str()))
    macro_name = request.args.get('macro_name', str())
    form = FieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title=f"{field_name} ({macro_name})", form=form)
    if 'field_bytes' not in pnr:
        pnr['field_bytes'] = list()
    pnr['text_data'] = str()
    pnr['text_list'] = list()
    _add_field_byte(pnr['field_bytes'], field_name, form.field_data.data)
    session['pnr'] = pnr
    return redirect(url_for('confirm_pnr'))


@tpf2_app.route('/test_data/inputs/pnr/cancel')
@login_required
@test_data_required
def cancel_pnr():
    session.pop('pnr', None)
    return redirect(url_for('confirm_test_data'))
