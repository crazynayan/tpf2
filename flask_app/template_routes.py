from urllib.parse import unquote

from flask import url_for, render_template, request, flash
from flask_login import current_user
from munch import Munch
from werkzeug.utils import redirect

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.template_constants import TemplateConstant, PNR, GLOBAL, AAA
from flask_app.template_forms import TemplateRenameCopyForm, PnrCreateForm, PnrAddForm, PnrUpdateForm, \
    TemplateLinkMergeForm, TemplateLinkUpdateForm, TemplateDeleteForm, GlobalCreateForm, GlobalAddForm, \
    GlobalUpdateForm, AaaCreateForm, AaaUpdateForm
from flask_app.test_data_routes import test_data_required
from flask_app.user import cookie_login_required, error_check


def flash_message(response: dict) -> None:
    msg = response.get("message")
    if msg:
        flash(msg)
        return
    if response.get("error", True):
        flash("System Error. No changes made.")
    return


@tpf2_app.route("/templates/<string:template_type>")
@cookie_login_required
def view_templates(template_type: str):
    tc = TemplateConstant(template_type)
    if not tc.is_type_valid:
        flash("Invalid Template Type")
        return redirect(url_for("home"))
    templates = Server.get_templates(tc.type.lower())
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("template_list.html", title=f"{tc.type} templates", templates=templates, tc=tc)


@tpf2_app.route("/templates/name", methods=["GET", "POST"])
@cookie_login_required
def view_template():
    name = unquote(request.args.get("name", str()))
    templates = Server.get_template_by_name(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not templates:
        flash("Template not found.")
        return redirect(url_for("home"))
    tc = TemplateConstant(templates[0]["type"])
    if not tc.is_type_valid:
        flash("Invalid Template Type")
        return redirect(url_for("home"))
    form = TemplateDeleteForm(name)
    if not form.validate_on_submit():
        return render_template("template_view.html", title="Template", templates=templates, form=form, name=name,
                               tc=tc)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name)) if form.template_id.data \
        else redirect(url_for("view_templates", template_type=tc.type))


@tpf2_app.route("/templates/rename", methods=["GET", "POST"])
@cookie_login_required
def rename_template():
    name = unquote(request.args.get("name", str()))
    templates = Server.get_template_by_name(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not templates:
        return redirect(url_for("view_template", name=name))
    form = TemplateRenameCopyForm(templates[0], action="rename")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Rename Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=form.name.data))


@tpf2_app.route("/templates/copy", methods=["GET", "POST"])
@cookie_login_required
def copy_template():
    name = unquote(request.args.get("name", str()))
    templates = Server.get_template_by_name(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not templates:
        return redirect(url_for("view_template", name=name))
    form = TemplateRenameCopyForm(templates[0], action="copy")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Copy Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=form.name.data))


@tpf2_app.route("/templates/pnr/create", methods=["GET", "POST"])
@cookie_login_required
def create_pnr_template():
    form = PnrCreateForm()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Create PNR Template", form=form, name=str())
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=form.name.data))


@tpf2_app.route("/templates/pnr/add", methods=["GET", "POST"])
@cookie_login_required
def add_pnr_template():
    name = unquote(request.args.get("name", str()))
    form = PnrAddForm(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Add to PNR Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/templates/pnr/update/<string:template_id>", methods=["GET", "POST"])
@cookie_login_required
@error_check
def update_pnr_template(template_id: str):
    template: Munch = Server.get_template_by_id_orm(template_id)
    if not template:
        flash("Error in updating. Template not found")
        return redirect(url_for("view_pnr_templates"))
    form = PnrUpdateForm(template)
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Update PNR Template", form=form, name=template.name)
    flash_message(form.response)
    return redirect(url_for("view_template", name=template.name))


@tpf2_app.route("/templates/global/create", methods=["GET", "POST"])
@cookie_login_required
def create_global_template():
    form = GlobalCreateForm()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Create Global Template", form=form, name=str())
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=form.name.data))


@tpf2_app.route("/templates/global/add", methods=["GET", "POST"])
@cookie_login_required
def add_global_template():
    name = unquote(request.args.get("name", str()))
    form = GlobalAddForm(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Add to Global Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/templates/global/update/<string:template_id>", methods=["GET", "POST"])
@cookie_login_required
def update_global_template(template_id: str):
    template: dict = Server.get_template_by_id(template_id)
    if not template:
        flash("Error in updating. Template not found")
        return redirect(url_for("view_pnr_templates"))
    form = GlobalUpdateForm(template)
    name = template["name"]
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Update Global Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/templates/aaa/create", methods=["GET", "POST"])
@cookie_login_required
def create_aaa_template():
    form = AaaCreateForm()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Create AAA Template", form=form, name=str())
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=form.name.data))


@tpf2_app.route("/templates/aaa/update/<string:template_id>", methods=["GET", "POST"])
@cookie_login_required
def update_aaa_template(template_id: str):
    template: dict = Server.get_template_by_id(template_id)
    if not template:
        flash("Error in updating. Template not found")
        return redirect(url_for("view_pnr_templates"))
    form = AaaUpdateForm(template)
    name = template["name"]
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Update AAA Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/pnr/merge", methods=["GET", "POST"])
@cookie_login_required
def merge_pnr_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=PNR, action_type="merge")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Merge PNR Template", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/pnr/link/create", methods=["GET", "POST"])
@cookie_login_required
def create_link_pnr_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=PNR, action_type="link")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Link PNR Template", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/pnr/update",
                methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def update_link_pnr_template(test_data_id: str, name: str, variation: int, **kwargs):
    test_data: dict = kwargs[test_data_id]
    template_name: str = unquote(name)
    td_pnr: dict = next((pnr for pnr in test_data["pnr"] if pnr["link"] == template_name
                         and pnr["variation"] == variation), dict())
    if not td_pnr:
        flash("No PNR element found with this template name.")
        return redirect(url_for("confirm_test_data", test_data_id=test_data_id))
    form = TemplateLinkUpdateForm(test_data_id, td_pnr, PNR)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Update Link to PNR Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/pnr/delete", methods=["GET"])
@cookie_login_required
def delete_link_pnr_template(test_data_id: str, name: str, variation: int):
    template_name: str = unquote(name)
    body = {"template_name": template_name, "variation": variation, "variation_name": str()}
    response = Server.delete_link_pnr_template(test_data_id, body)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if response["message"]:
        flash(response["message"])
    for error_label in response["error_fields"]:
        flash(response["error_fields"][error_label])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/global/merge", methods=["GET", "POST"])
@cookie_login_required
def merge_global_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=GLOBAL, action_type="merge")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Merge Global Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/global/link/create", methods=["GET", "POST"])
@cookie_login_required
def create_link_global_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=GLOBAL, action_type="link")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Link Global Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/global/update",
                methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def update_link_global_template(test_data_id: str, name: str, variation: int, **kwargs):
    test_data: dict = kwargs[test_data_id]
    template_name: str = unquote(name)
    td_core: dict = next((core for core in test_data["cores"] if core["link"] == template_name
                          and core["variation"] == variation), dict())
    if not td_core:
        flash("No Global link found with this template name.")
        return redirect(url_for("confirm_test_data", test_data_id=test_data_id))
    form = TemplateLinkUpdateForm(test_data_id, td_core, GLOBAL)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Update Link to Global Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/global/delete", methods=["GET"])
@cookie_login_required
def delete_link_global_template(test_data_id: str, name: str, variation: int):
    template_name: str = unquote(name)
    body = {"template_name": template_name, "variation": variation, "variation_name": str()}
    response = Server.delete_link_global_template(test_data_id, body)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if response["message"]:
        flash(response["message"])
    for error_label in response["error_fields"]:
        flash(response["error_fields"][error_label])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/aaa/merge", methods=["GET", "POST"])
@cookie_login_required
def merge_aaa_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=AAA, action_type="merge")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Merge AAA Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/aaa/link/create", methods=["GET", "POST"])
@cookie_login_required
def create_link_aaa_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type=AAA, action_type="link")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Link AAA Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/aaa/update",
                methods=["GET", "POST"])
@cookie_login_required
@test_data_required
def update_link_aaa_template(test_data_id: str, name: str, variation: int, **kwargs):
    test_data: dict = kwargs[test_data_id]
    template_name: str = unquote(name)
    td_core: dict = next((core for core in test_data["cores"] if core["link"] == template_name
                          and core["variation"] == variation), dict())
    if not td_core:
        flash("No AAA link found with this template name.")
        return redirect(url_for("confirm_test_data", test_data_id=test_data_id))
    form = TemplateLinkUpdateForm(test_data_id, td_core, AAA)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Update Link to AAA Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/aaa/delete", methods=["GET"])
@cookie_login_required
def delete_link_aaa_template(test_data_id: str, name: str, variation: int):
    template_name: str = unquote(name)
    body = {"template_name": template_name, "variation": variation, "variation_name": str()}
    response = Server.delete_link_aaa_template(test_data_id, body)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if response["message"]:
        flash(response["message"])
    for error_label in response["error_fields"]:
        flash(response["error_fields"][error_label])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-core"))
