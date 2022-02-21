from urllib.parse import unquote

from flask import url_for, render_template, request, flash
from flask_login import current_user
from werkzeug.utils import redirect

from flask_app import tpf2_app
from flask_app.server import Server
from flask_app.template_forms import TemplateRenameForm, PnrCreateForm, PnrAddForm, PnrUpdateForm
from flask_app.test_data_forms import DeleteForm
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
