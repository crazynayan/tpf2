from base64 import b64encode
from functools import wraps
from urllib.parse import unquote

from flask import render_template, url_for, redirect, flash, request, Response
from flask_login import current_user
from werkzeug.datastructures import MultiDict
from wtforms import BooleanField

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.test_data_forms import DeleteForm, TestDataForm, FieldSearchForm, FieldLengthForm, \
    FieldDataForm, RegisterForm, RegisterFieldDataForm, PnrForm, MultipleFieldDataForm, TpfdfForm, DebugForm, \
    FixedFileForm, PnrOutputForm, HeapForm, EcbLevelForm, UpdateEcbLevelForm
from flask_app.user import cookie_login_required


def test_data_required(func):
    @wraps(func)
    def test_data_wrapper(test_data_id, *args, **kwargs):
        test_data: dict = Server.get_test_data(test_data_id)
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        if not test_data:
            flash("Error in retrieving the test data")
            return redirect(url_for("get_my_test_data"))
        kwargs[test_data_id] = test_data
        return func(test_data_id, *args, **kwargs)

    return test_data_wrapper


def _search_field(redirect_route: str, test_data_id: str):
    form = FieldSearchForm()
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Search Fields", form=form, test_data_id=test_data_id)
    label_ref = form.field.data
    return redirect(url_for(redirect_route, test_data_id=test_data_id, field_name=label_ref["label"],
                            macro_name=label_ref["name"], length=label_ref["length"]))


def _convert_field_data(form_data: str) -> list:
    return [{"data": b64encode(bytes.fromhex(data.split(":")[1])).decode(), "field": data.split(":")[0]}
            for data in form_data.split(",") if data]


@tpf2_app.route("/test_data")
@cookie_login_required
def get_all_test_data():
    test_data_list = Server.get_all_test_data()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("test_data_list.html", title="All Test Data", test_data_list=test_data_list, all_flag=True)


@tpf2_app.route("/my_test_data")
@cookie_login_required
def get_my_test_data():
    test_data_list = Server.get_all_test_data()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    my_list = [test_data for test_data in test_data_list if test_data["owner"] == current_user.email]
    return render_template("test_data_list.html", title="My Test Data", test_data_list=my_list, all_flag=False)


@tpf2_app.route("/test_data/<string:test_data_id>", methods=["GET", "POST"])
@cookie_login_required
def get_test_data(test_data_id):
    test_data = Server.get_test_data(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not test_data:
        flash("Error in retrieving the test data")
        return redirect(url_for("get_my_test_data"))
    form = DeleteForm()
    if not form.validate_on_submit():
        return render_template("test_data_view.html", title="Test Data", test_data=test_data, form=form)
    response = Server.delete_test_data(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting test data")
    return redirect(url_for("get_my_test_data"))


@tpf2_app.route("/test_data/<string:test_data_id>/run")
@cookie_login_required
def run_test_data(test_data_id: str):
    test_data = Server.run_test_data(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not test_data:
        flash("Error in running test data")
        return redirect(url_for("get_test_data", test_data_id=test_data_id))
    if len(test_data["outputs"]) > 1:
        test_data_variation = {"core": False, "pnr": False, "tpfdf": False, "file": False}
        for variation_type in test_data_variation:
            if any(output["variation"][variation_type] != test_data["outputs"][0]["variation"][variation_type]
                   for output in test_data["outputs"]):
                test_data_variation[variation_type] = True
        return render_template("test_data_variation.html", title="Results", test_data=test_data,
                               test_data_variation=test_data_variation)
    return render_template("test_data_result.html", title="Results", test_data=test_data,
                           output=test_data["outputs"][0])


@tpf2_app.route("/test_data/create", methods=["GET", "POST"])
@cookie_login_required
def create_test_data():
    form = TestDataForm()
    form_validation_successful = form.validate_on_submit()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form_validation_successful:
        return render_template("test_data_form.html", title="Create Test Data", form=form)
    test_data: dict = {
        "name": form.name.data,
        "seg_name": form.seg_name.data,
        "owner": current_user.email,
        "stop_segments": form.stop_segment_list,
    }
    response: dict = Server.create_test_data(test_data)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in creating test data")
        return redirect(url_for("create_test_data"))
    return redirect(url_for("confirm_test_data", test_data_id=response["id"]))


@tpf2_app.route("/test_data/<string:test_data_id>/copy")
@cookie_login_required
def copy_test_data(test_data_id):
    response = Server.copy_test_data(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in copying the test data")
        return redirect(url_for("get_test_data", test_data_id=test_data_id))
    return redirect(url_for("rename_test_data", test_data_id=response["id"]))


@tpf2_app.route("/test_data/<string:test_data_id>/rename", methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def rename_test_data(test_data_id, **kwargs):
    form = TestDataForm(kwargs[test_data_id])
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Edit Test Data Header", form=form,
                               test_data_id=test_data_id)
    response: dict = Server.rename_test_data(test_data_id, {"name": form.name.data, "seg_name": form.seg_name.data,
                                                            "stop_segments": form.stop_segment_list})
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in renaming test data")
        return redirect(url_for("rename_test_data", test_data_id=test_data_id))
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/confirm", methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def confirm_test_data(test_data_id: str, **kwargs):
    test_data: dict = kwargs[test_data_id]
    return render_template("test_data_confirm.html", title="Confirm Test Data", test_data=test_data)


@tpf2_app.route("/test_data/<string:test_data_id>/output/regs", methods=["GET", "POST"])
@cookie_login_required
def add_output_regs(test_data_id: str):
    form = RegisterForm()
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add Registers", form=form, test_data_id=test_data_id)
    reg_list = [value.label.text for reg, value in vars(form).items()
                if reg.startswith("r") and isinstance(value, BooleanField) and value.data]
    response: dict = Server.add_output_regs(test_data_id, {"regs": reg_list})
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in updating output registers")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/fields", methods=["GET", "POST"])
@cookie_login_required
def search_output_fields(test_data_id: str) -> Response:
    return _search_field("add_output_field", test_data_id)


@tpf2_app.route("/test_data/<string:test_data_id>/output/cores/<string:macro_name>/fields/<string:field_name>",
                methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def add_output_field(test_data_id: str, macro_name: str, field_name: str, **kwargs):
    field_name = unquote(field_name)
    form = FieldLengthForm(macro_name)
    form_data = form.data
    form_data["length"] = request.args.get("length", 1, type=int)
    core = next((core for core in kwargs[test_data_id]["outputs"]["cores"] if core["macro_name"] == macro_name), None)
    if core:
        form_data["base_reg"] = core["base_reg"]
    form = FieldLengthForm(macro_name, formdata=MultiDict(form_data)) if request.method == "GET" \
        else FieldLengthForm(macro_name)
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title=f"{field_name} ({macro_name})", form=form,
                               test_data_id=test_data_id)
    field_dict = {"field": field_name, "length": form.length.data, "base_reg": form.base_reg.data}
    response = Server.add_output_field(test_data_id, macro_name, field_dict)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in creating field_byte")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/cores/<string:macro_name>/fields/<string:field_name>/delete")
@cookie_login_required
def delete_output_field(test_data_id: str, macro_name: str, field_name: str):
    response = Server.delete_output_field(test_data_id, macro_name, field_name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting field")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/fields", methods=["GET", "POST"])
@cookie_login_required
def search_input_fields(test_data_id: str) -> Response:
    return _search_field("add_input_field", test_data_id)


@tpf2_app.route("/test_data/<string:test_data_id>/input/cores/<string:macro_name>/fields/<string:field_name>",
                methods=["GET", "POST"])
@cookie_login_required
def add_input_field(test_data_id: str, macro_name: str, field_name: str):
    field_name = unquote(field_name)
    form = FieldDataForm()
    variations = Server.get_variations(test_data_id, "core")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    form.variation.choices = [(item["variation"], f"{item['variation_name']} ({item['variation']})")
                              for item in variations]
    form.variation.choices.append((-1, "New Variation"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title=f"{field_name} ({macro_name})", form=form,
                               test_data_id=test_data_id)
    field_dict = {"field": field_name, "data": form.field_data.data}
    if form.variation.data == -1:
        field_dict["variation"] = variations[-1]["variation"] + 1 if variations else 0
        field_dict["variation_name"] = form.variation_name.data
    else:
        field_dict["variation"] = form.variation.data
        field_dict["variation_name"] = str()
    response = Server.add_input_field(test_data_id, macro_name, field_dict)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in creating fields")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/cores/<string:macro_name>/fields/<string:field_name>/delete")
@cookie_login_required
def delete_input_field(test_data_id: str, macro_name: str, field_name: str):
    response = Server.delete_input_field(test_data_id, macro_name, field_name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting field")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/heap", methods=["GET", "POST"])
@cookie_login_required
def add_heap(test_data_id: str):
    form = HeapForm(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add Heap", form=form, test_data_id=test_data_id)
    response = Server.add_input_heap(test_data_id, form.body)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response or response["error"]:
        flash(response["message"]) if response else flash("Error in adding heap")
        return render_template("test_data_form.html", title="Add Heap", form=form, test_data_id=test_data_id)
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/heap/<string:heap_name>/variations/<int:variation>")
@cookie_login_required
def delete_heap(test_data_id: str, heap_name: str, variation: int):
    response = Server.delete_input_heap(test_data_id, heap_name, variation)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    flash(response["message"]) if response else flash("Error in deleting heap")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/ecb_level", methods=["GET", "POST"])
@cookie_login_required
def add_ecb_level(test_data_id: str):
    form = EcbLevelForm(test_data_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add ECB Level", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/ecb_level/<string:ecb_level>/variations/<int:variation>/e",
                methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def update_ecb_level(test_data_id: str, ecb_level: str, variation: int, **kwargs):
    test_data: dict = kwargs[test_data_id]
    core: dict = next((core for core in test_data["cores"] if core["ecb_level"] == ecb_level
                       and core["variation"] == variation), None)
    if not core:
        flash(f"Invalid ECB level {ecb_level} for variation {variation}.")
        return redirect(url_for("confirm_test_data", test_data_id=test_data_id))
    form = UpdateEcbLevelForm(test_data_id, core)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Update ECB Level", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/ecb_level/<string:ecb_level>/variations/<int:variation>")
@cookie_login_required
def delete_ecb_level(test_data_id: str, ecb_level: str, variation: int):
    response = Server.delete_input_ecb_level(test_data_id, ecb_level, variation)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    flash(response["message"]) if response else flash("Error in deleting ECB level")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/regs", methods=["GET", "POST"])
@cookie_login_required
def add_input_regs(test_data_id: str):
    form = RegisterFieldDataForm()
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Provide Register Values", form=form,
                               test_data_id=test_data_id)
    if not Server.add_input_regs(test_data_id, {"reg": form.reg.data, "value": form.field_data.data}):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in adding Registers")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/regs/<string:reg>")
@cookie_login_required
def delete_input_regs(test_data_id: str, reg: str):
    if not Server.delete_input_regs(test_data_id, reg):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in deleting Registers")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/pnr", methods=["GET", "POST"])
@cookie_login_required
def add_output_pnr(test_data_id: str):
    form = PnrOutputForm()
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add PNR element", form=form, test_data_id=test_data_id)
    pnr_dict = {"key": form.key.data, "locator": form.locator.data, "field_len": form.field_data.data}
    response = Server.add_output_pnr(test_data_id, pnr_dict)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in creating PNR")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/pnr/<string:pnr_id>")
@cookie_login_required
def delete_output_pnr(test_data_id: str, pnr_id: str):
    response = Server.delete_output_pnr(test_data_id, pnr_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting PNR element")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/pnr", methods=["GET", "POST"])
@cookie_login_required
def add_input_pnr(test_data_id: str):
    form = PnrForm()
    variations = Server.get_variations(test_data_id, "pnr")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    form.variation.choices = [(item["variation"], f"{item['variation_name']} ({item['variation']})")
                              for item in variations]
    form.variation.choices.append((-1, "New Variation"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add PNR element", form=form, test_data_id=test_data_id)
    pnr_dict = {"key": form.key.data, "locator": form.locator.data, "data": form.text_data.data}
    if form.variation.data == -1:
        pnr_dict["variation"] = variations[-1]["variation"] + 1 if variations else 0
        pnr_dict["variation_name"] = form.variation_name.data
    else:
        pnr_dict["variation"] = form.variation.data
        pnr_dict["variation_name"] = str()
    response = Server.create_pnr(test_data_id, pnr_dict)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in creating PNR")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/pnr/<string:pnr_id>/fields", methods=["GET", "POST"])
@cookie_login_required
def add_pnr_fields(test_data_id: str, pnr_id: str):
    form = MultipleFieldDataForm()
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add Multiple Fields", form=form, test_data_id=test_data_id)
    core_dict = form.field_data.data
    if not Server.add_pnr_fields(test_data_id, pnr_id, core_dict):
        flash("Error in adding PNR fields")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/pnr/<string:pnr_id>")
@cookie_login_required
def delete_pnr(test_data_id: str, pnr_id: str):
    response = Server.delete_pnr(test_data_id, pnr_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting PNR element")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/tpfdf/", methods=["GET", "POST"])
@cookie_login_required
def add_tpfdf_lrec(test_data_id: str):
    form = TpfdfForm()
    variations = Server.get_variations(test_data_id, "tpfdf")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    form.variation.choices = [(item["variation"], f"{item['variation_name']} ({item['variation']})")
                              for item in variations]
    form.variation.choices.append((-1, "New Variation"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add Tpfdf lrec", form=form, test_data_id=test_data_id)
    field_data = {field_data.split(":")[0]: b64encode(bytes.fromhex(field_data.split(":")[1])).decode()
                  for field_data in form.field_data.data.split(",")}
    tpfdf = {"field_data": field_data, "key": form.key.data, "macro_name": form.macro_name.data}
    if form.variation.data == -1:
        tpfdf["variation"] = variations[-1]["variation"] + 1 if variations else 0
        tpfdf["variation_name"] = form.variation_name.data
    else:
        tpfdf["variation"] = form.variation.data
        tpfdf["variation_name"] = str()
    if not Server.add_tpfdf_lrec(test_data_id, tpfdf):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in adding Tpfdf lrec")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/tpfdf/<string:df_id>")
@cookie_login_required
def delete_tpfdf_lrec(test_data_id: str, df_id: str):
    response = Server.delete_tpfdf_lrec(test_data_id, df_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting Tpfdf lrec")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


# noinspection DuplicatedCode
@tpf2_app.route("/test_data/<string:test_data_id>/input/fixed_files/", methods=["GET", "POST"])
@cookie_login_required
def add_fixed_file(test_data_id: str):
    form = FixedFileForm()
    variations = Server.get_variations(test_data_id, "file")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    form.variation.choices = [(item["variation"], f"{item['variation_name']} ({item['variation']})")
                              for item in variations]
    form.variation.choices.append((-1, "New Variation"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Add Fixed File", form=form, test_data_id=test_data_id)
    fixed_file = dict()
    if form.variation.data == -1:
        fixed_file["variation"] = variations[-1]["variation"] + 1 if variations else 0
        fixed_file["variation_name"] = form.variation_name.data
    else:
        fixed_file["variation"] = form.variation.data
        fixed_file["variation_name"] = str()
    fixed_file["macro_name"] = form.macro_name.data
    fixed_file["rec_id"] = int.from_bytes(bytes.fromhex(form.rec_id.data), byteorder="big")
    fixed_file["fixed_type"] = int(form.fixed_type.data)
    fixed_file["fixed_ordinal"] = int.from_bytes(bytes.fromhex(form.fixed_ordinal.data), byteorder="big")
    fixed_file["forward_chain_count"] = form.fixed_fch_count.data
    fixed_file["forward_chain_label"] = form.fixed_fch_label.data
    fixed_file["field_data"] = _convert_field_data(form.fixed_field_data.data)
    fixed_file["file_items"] = list()
    if form.fixed_item_field.data:
        fixed_file["file_items"].append(dict())
        fixed_file["file_items"][0]["field"] = form.fixed_item_field.data
        fixed_file["file_items"][0]["macro_name"] = form.macro_name.data
        fixed_file["file_items"][0]["field_data"] = _convert_field_data(form.fixed_item_field_data.data)
        fixed_file["file_items"][0]["count_field"] = form.fixed_item_count.data
        fixed_file["file_items"][0]["adjust"] = form.fixed_item_adjust.data
        fixed_file["file_items"][0]["repeat"] = form.fixed_item_repeat.data
    fixed_file["pool_files"] = list()
    if form.pool_macro_name.data:
        pool_file = dict()
        fixed_file["pool_files"].append(pool_file)
        pool_file["macro_name"] = form.pool_macro_name.data
        pool_file["rec_id"] = int.from_bytes(bytes.fromhex(form.pool_rec_id.data), byteorder="big")
        pool_file["index_field"] = form.pool_index_field.data
        pool_file["index_macro_name"] = form.macro_name.data
        pool_file["forward_chain_count"] = form.pool_fch_count.data
        pool_file["forward_chain_label"] = form.pool_fch_label.data
        pool_file["field_data"] = _convert_field_data(form.pool_field_data.data)
        pool_file["pool_files"] = list()
        pool_file["file_items"] = list()
        if form.pool_item_field.data:
            pool_file["file_items"].append(dict())
            pool_file["file_items"][0]["field"] = form.pool_item_field.data
            pool_file["file_items"][0]["macro_name"] = form.pool_macro_name.data
            pool_file["file_items"][0]["field_data"] = _convert_field_data(form.pool_item_field_data.data)
            pool_file["file_items"][0]["count_field"] = form.pool_item_count.data
            fixed_file["file_items"][0]["adjust"] = form.pool_item_adjust.data
            fixed_file["file_items"][0]["repeat"] = form.pool_item_repeat.data
    if not Server.add_fixed_file(test_data_id, fixed_file):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in adding Fixed File")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/input/fixed_files/<string:file_id>")
@cookie_login_required
def delete_fixed_file(test_data_id: str, file_id: str):
    response = Server.delete_fixed_file(test_data_id, file_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not response:
        flash("Error in deleting Fixed File")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/debug/", methods=["GET", "POST"])
@cookie_login_required
def add_debug(test_data_id: str):
    form = DebugForm()
    form_validation_successful = form.validate_on_submit()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form_validation_successful:
        return render_template("test_data_form.html", title="Add Segments to Debug", form=form,
                               test_data_id=test_data_id)
    if not Server.add_debug(test_data_id, {"traces": form.seg_list.data.split(",")}):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in adding debug segments")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))


@tpf2_app.route("/test_data/<string:test_data_id>/output/debug/<string:seg_name>/delete")
@cookie_login_required
def delete_debug(test_data_id: str, seg_name: str) -> Response:
    if not Server.delete_debug(test_data_id, seg_name):
        if not current_user.is_authenticated:
            return redirect(url_for("logout"))
        flash("Error in delete debug segment")
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id))
