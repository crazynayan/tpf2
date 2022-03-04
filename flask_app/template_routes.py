from urllib.parse import unquote

from flask import url_for, render_template, request, flash
from flask_login import current_user
from werkzeug.utils import redirect

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.template_forms import TemplateRenameForm, PnrCreateForm, PnrAddForm, PnrUpdateForm, \
    TemplateLinkMergeForm, TemplateLinkUpdateForm
from flask_app.test_data_forms import DeleteForm
from flask_app.test_data_routes import test_data_required
from flask_app.user import cookie_login_required


@tpf2_app.route("/templates/pnr")
@cookie_login_required
def view_pnr_templates():
    templates = Server.get_pnr_templates()
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    return render_template("template_list.html", title="PNR templates", templates=templates)


@tpf2_app.route("/templates/name", methods=["GET", "POST"])
@cookie_login_required
def view_template():
    name = unquote(request.args.get("name", str()))
    templates = Server.get_template_by_name(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    form = DeleteForm()
    if not form.validate_on_submit():
        return render_template("template_view.html", title="Template", templates=templates, form=form, name=name)
    response = Server.delete_template_by_name({"name": name})
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if "error" in response and response["error"]:
        flash(response["message"])
    return redirect(url_for("view_pnr_templates"))


@tpf2_app.route("/templates/rename", methods=["GET", "POST"])
@cookie_login_required
def rename_template():
    name = unquote(request.args.get("name", str()))
    templates = Server.get_template_by_name(name)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not templates:
        return redirect(url_for("view_template", name=name))
    form = TemplateRenameForm(templates[0])
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Rename Template", form=form, name=name)
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
def update_pnr_template(template_id: str):
    template: dict = Server.get_template_by_id(template_id)
    if not template:
        flash("Error in updating. Template not found")
        return redirect(url_for("view_pnr_templates"))
    form = PnrUpdateForm(template)
    name = template["name"]
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("template_form.html", title="Update PNR Template", form=form, name=name)
    if "message" in form.response:
        flash(form.response["message"])
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/templates/delete/<string:template_id>", methods=["GET"])
@cookie_login_required
def delete_template_by_id(template_id: str):
    response: dict = Server.delete_template_by_id(template_id)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if "message" in response:
        flash(response["message"])
    name = unquote(request.args.get("name", str()))
    if not name:
        return redirect(url_for("view_pnr_templates"))
    return redirect(url_for("view_template", name=name))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/pnr/merge", methods=["GET", "POST"])
@cookie_login_required
def merge_pnr_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type="pnr", action_type="merge")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Merge PNR Template", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<string:test_data_id>/templates/pnr/link/create", methods=["GET", "POST"])
@cookie_login_required
def create_link_pnr_template(test_data_id: str):
    form = TemplateLinkMergeForm(test_data_id, template_type="pnr", action_type="link")
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Link PNR Template", form=form, test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/update", methods=["GET", "POST"])
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
    form = TemplateLinkUpdateForm(test_data_id, td_pnr)
    if not current_user.is_authenticated:
        return redirect(url_for("logout"))
    if not form.validate_on_submit():
        return render_template("test_data_form.html", title="Update Link to PNR Template", form=form,
                               test_data_id=test_data_id)
    flash(form.response["message"])
    return redirect(url_for("confirm_test_data", test_data_id=test_data_id, _anchor="input-pnr"))


@tpf2_app.route("/test_data/<test_data_id>/templates/<name>/variations/<int:variation>/delete", methods=["GET"])
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
