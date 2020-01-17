from base64 import b64encode
from functools import wraps
from urllib.parse import unquote

from flask import render_template, url_for, redirect, flash, request, Response
from flask_login import login_required
from werkzeug.datastructures import MultiDict
from wtforms import BooleanField

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.test_data_forms import DeleteForm, TestDataForm, ConfirmForm, FieldSearchForm, FieldLengthForm, \
    FieldDataForm, RegisterForm, RegisterFieldDataForm, PnrForm, MultipleFieldDataForm, TpfdfForm, DebugForm


def test_data_required(func):
    @wraps(func)
    def test_data_wrapper(test_data_id, *args, **kwargs):
        test_data: dict = Server.get_test_data(test_data_id)
        if not test_data:
            flash('Error in retrieving the test data')
            return redirect(url_for('get_all_test_data'))
        kwargs[test_data_id] = test_data
        return func(test_data_id, *args, **kwargs)

    return test_data_wrapper


def _search_field(redirect_route: str, test_data_id: str) -> Response:
    form = FieldSearchForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Search Fields', form=form)
    label_ref = form.field.data
    return redirect(url_for(redirect_route, test_data_id=test_data_id, field_name=label_ref['label'],
                            macro_name=label_ref['name'], length=label_ref['length']))


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
        flash('Error in retrieving the test data')
        return redirect(url_for('get_all_test_data'))
    form = DeleteForm()
    if not form.validate_on_submit():
        return render_template('test_data_view.html', title='Test Data', test_data=test_data, form=form)
    response = Server.delete_test_data(test_data_id)
    if not response:
        flash('Error in deleting test data')
    return redirect(url_for('get_all_test_data'))


@tpf2_app.route('/test_data/<string:test_data_id>/run')
@login_required
def run_test_data(test_data_id: str):
    test_data = Server.run_test_data(test_data_id)
    if len(test_data['outputs']) > 1:
        return render_template('test_data_variation.html', title='Results', test_data=test_data)
    return render_template('test_data_result.html', title='Results', test_data=test_data,
                           output=test_data['outputs'][0])


@tpf2_app.route('/test_data/create', methods=['GET', 'POST'])
@login_required
def create_test_data():
    form = TestDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Create Test Data', form=form)
    response: dict = Server.create_test_data({'name': form.name.data, 'seg_name': form.seg_name.data})
    if not response:
        flash('Error in creating test data')
        return redirect(url_for('create_test_data'))
    return redirect(url_for('confirm_test_data', test_data_id=response['id']))


@tpf2_app.route('/test_data/<string:test_data_id>/copy')
@login_required
def copy_test_data(test_data_id):
    response = Server.copy_test_data(test_data_id)
    if not response:
        flash('Error in copying the test data')
        return redirect(url_for('get_test_data', test_data_id=test_data_id))
    return redirect(url_for('rename_test_data', test_data_id=response['id']))


@tpf2_app.route('/test_data/<string:test_data_id>/rename', methods=['GET', 'POST'])
@login_required
@test_data_required
def rename_test_data(test_data_id, **kwargs):
    form_data = TestDataForm().data
    form_data['name'] = kwargs[test_data_id]['name']
    form_data['seg_name'] = kwargs[test_data_id]['seg_name']
    form = TestDataForm(formdata=MultiDict(form_data)) if request.method == 'GET' else TestDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Rename Test Data', form=form)
    response: dict = Server.rename_test_data(test_data_id, {'name': form.name.data, 'seg_name': form.seg_name.data})
    if not response:
        flash('Error in renaming test data')
        return redirect(url_for('rename_test_data', test_data_id=test_data_id))
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/confirm', methods=['GET', 'POST'])
@login_required
@test_data_required
def confirm_test_data(test_data_id: str, **kwargs):
    test_data: dict = kwargs[test_data_id]
    form = ConfirmForm()
    if not form.validate_on_submit():
        return render_template('test_data_confirm.html', title='Confirm Test Data', test_data=test_data, form=form)
    if not test_data['outputs']['regs'] and not test_data['outputs']['cores']:
        flash('You need to add at least one output')
        return redirect(url_for('confirm_test_data', test_data_id=test_data_id))
    return redirect(url_for('get_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/output/regs', methods=['GET', 'POST'])
@login_required
def add_output_regs(test_data_id: str):
    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Registers', form=form)
    reg_list = [value.label.text for reg, value in vars(form).items()
                if reg.startswith('r') and isinstance(value, BooleanField) and value.data]
    response: dict = Server.add_output_regs(test_data_id, {'regs': reg_list})
    if not response:
        flash('Error in updating output registers')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/output/fields', methods=['GET', 'POST'])
@login_required
def search_output_fields(test_data_id: str) -> Response:
    return _search_field('add_output_field', test_data_id)


@tpf2_app.route('/test_data/<string:test_data_id>/output/cores/<string:macro_name>/fields/<string:field_name>',
                methods=['GET', 'POST'])
@login_required
@test_data_required
def add_output_field(test_data_id: str, macro_name: str, field_name: str, **kwargs) -> Response:
    field_name = unquote(field_name)
    form = FieldLengthForm(macro_name)
    form_data = form.data
    form_data['length'] = request.args.get('length', 1, type=int)
    core = next((core for core in kwargs[test_data_id]['outputs']['cores'] if core['macro_name'] == macro_name), None)
    if core:
        form_data['base_reg'] = core['base_reg']
    form = FieldLengthForm(macro_name, formdata=MultiDict(form_data)) if request.method == 'GET' \
        else FieldLengthForm(macro_name)
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title=f"{field_name} ({macro_name})", form=form)
    field_dict = {'field': field_name, 'length': form.length.data, 'base_reg': form.base_reg.data}
    response = Server.add_output_field(test_data_id, macro_name, field_dict)
    if not response:
        flash('Error in creating field_byte')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/output/cores/<string:macro_name>/fields/<string:field_name>/delete')
@login_required
def delete_output_field(test_data_id: str, macro_name: str, field_name: str):
    response = Server.delete_output_field(test_data_id, macro_name, field_name)
    if not response:
        flash('Error in deleting field')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/fields', methods=['GET', 'POST'])
@login_required
def search_input_fields(test_data_id: str) -> Response:
    return _search_field('add_input_field', test_data_id)


@tpf2_app.route('/test_data/<string:test_data_id>/input/cores/<string:macro_name>/fields/<string:field_name>',
                methods=['GET', 'POST'])
@login_required
def add_input_field(test_data_id: str, macro_name: str, field_name: str):
    field_name = unquote(field_name)
    form = FieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title=f"{field_name} ({macro_name})", form=form)
    field_dict = {'field': field_name, 'data': form.field_data.data, 'variation': form.variation.data}
    response = Server.add_input_field(test_data_id, macro_name, field_dict)
    if not response:
        flash('Error in creating fields')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/cores/<string:macro_name>/fields/<string:field_name>/delete')
@login_required
def delete_input_field(test_data_id: str, macro_name: str, field_name: str):
    response = Server.delete_input_field(test_data_id, macro_name, field_name)
    if not response:
        flash('Error in deleting field')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/regs', methods=['GET', 'POST'])
@login_required
def add_input_regs(test_data_id: str):
    form = RegisterFieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Provide Register Values', form=form)
    if not Server.add_input_regs(test_data_id, {'reg': form.reg.data, 'value': form.field_data.data}):
        flash("Error in adding Registers")
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/regs/<string:reg>')
@login_required
def delete_input_regs(test_data_id: str, reg: str):
    if not Server.delete_input_regs(test_data_id, reg):
        flash("Error in deleting Registers")
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/pnr', methods=['GET', 'POST'])
@login_required
def add_input_pnr(test_data_id: str):
    form = PnrForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add PNR element', form=form)
    pnr_dict = {'key': form.key.data, 'locator': form.locator.data, 'data': form.text_data.data,
                'variation': form.variation.data}
    response = Server.create_pnr(test_data_id, pnr_dict)
    if not response:
        flash("Error in creating PNR")
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/pnr/<string:pnr_id>/fields', methods=['GET', 'POST'])
@login_required
def add_pnr_fields(test_data_id: str, pnr_id: str) -> Response:
    form = MultipleFieldDataForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Multiple Fields', form=form)
    core_dict = form.field_data.data
    if not Server.add_pnr_fields(test_data_id, pnr_id, core_dict):
        flash('Error in adding PNR fields')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/pnr/<string:pnr_id>')
@login_required
def delete_pnr(test_data_id: str, pnr_id: str):
    response = Server.delete_pnr(test_data_id, pnr_id)
    if not response:
        flash('Error in deleting PNR element')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/tpfdf/', methods=['GET', 'POST'])
@login_required
def add_tpfdf_lrec(test_data_id: str) -> Response:
    form = TpfdfForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Tpfdf lrec', form=form)
    field_data = {field_data.split(':')[0]: b64encode(bytes.fromhex(field_data.split(':')[1])).decode()
                  for field_data in form.field_data.data.split(',')}
    tpfdf = {'field_data': field_data, 'key': form.key.data, 'variation': form.variation.data,
             'macro_name': form.macro_name.data}
    if not Server.add_tpfdf_lrec(test_data_id, tpfdf):
        flash('Error in adding Tpfdf lrec')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/input/tpfdf/<string:df_id>')
@login_required
def delete_tpfdf_lrec(test_data_id: str, df_id: str):
    response = Server.delete_tpfdf_lrec(test_data_id, df_id)
    if not response:
        flash('Error in deleting Tpfdf lrec')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/output/debug/', methods=['GET', 'POST'])
@login_required
def add_debug(test_data_id: str) -> Response:
    form = DebugForm()
    if not form.validate_on_submit():
        return render_template('test_data_form.html', title='Add Segments to Debug', form=form)
    if not Server.add_debug(test_data_id, {'traces': form.seg_list.data.split(',')}):
        flash('Error in adding debug segments')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))


@tpf2_app.route('/test_data/<string:test_data_id>/output/debug/<string:seg_name>/delete')
@login_required
def delete_debug(test_data_id: str, seg_name: str) -> Response:
    if not Server.delete_debug(test_data_id, seg_name):
        flash('Error in delete debug segment')
    return redirect(url_for('confirm_test_data', test_data_id=test_data_id))
