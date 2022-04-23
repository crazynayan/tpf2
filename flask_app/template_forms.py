from types import SimpleNamespace
from typing import Union

from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from munch import Munch
from wtforms import SelectField, StringField, TextAreaField, SubmitField, ValidationError, HiddenField, BooleanField

from config import Config
from flask_app.form_prompts import PNR_KEY_PROMPT, PNR_LOCATOR_PROMPT, PNR_TEXT_PROMPT, PNR_INPUT_FIELD_DATA_PROMPT, \
    TEMPLATE_NAME_PROMPT, TEMPLATE_DESCRIPTION_PROMPT, VARIATION_PROMPT, VARIATION_NAME_PROMPT, GLOBAL_NAME_PROMPT, \
    IS_GLOBAL_RECORD_PROMPT, GLOBAL_HEX_DATA_PROMPT, GLOBAL_SEG_NAME_PROMPT, GLOBAL_FIELD_DATA_PROMPT, \
    MACRO_FIELD_DATA_PROMPT
from flask_app.server import Server, RequestType
from flask_app.template_constants import PNR, GLOBAL, AAA
from flask_app.test_data_forms import init_variation


def evaluate_error(response: Munch, field: Union[list, str], message: bool = False) -> None:
    if response.get("error", True) is False:
        return
    if message and response.message:
        raise ValidationError(response.message)
    fields = field if isinstance(field, list) else [field]
    for field_name in fields:
        msg = response.error_fields.get(field_name, str())
        if msg:
            raise ValidationError(msg)
    return


def init_body(form_data: dict, request_type: SimpleNamespace) -> dict:
    body = dict()
    for field_name in request_type.__dict__:
        body[field_name] = form_data.get(field_name)
    return body


class PnrCreateForm(FlaskForm):
    template_type = PNR
    name = StringField(TEMPLATE_NAME_PROMPT)
    description = TextAreaField(TEMPLATE_DESCRIPTION_PROMPT, render_kw={"rows": "5"})
    key = SelectField(PNR_KEY_PROMPT, choices=Config.PNR_KEYS, default="header")
    locator = StringField(PNR_LOCATOR_PROMPT)
    text = StringField(PNR_TEXT_PROMPT)
    field_data = TextAreaField(PNR_INPUT_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Create New PNR Template")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        if request.method == "POST":
            body = {"key": self.key.data, "locator": self.locator.data, "field_data": self.field_data.data,
                    "text": self.text.data, "name": self.name.data, "description": self.description.data}
            self.response = Server.create_new_pnr_template(body)

    def validate_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "name" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["name"])

    def validate_description(self, _):
        if "error_fields" in self.response and "description" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["description"])

    def validate_key(self, _):
        if "error_fields" in self.response and "key" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["key"])

    def validate_locator(self, _):
        if "error_fields" in self.response and "locator" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["locator"])

    def validate_text(self, _):
        if "error_fields" in self.response and "text" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["text"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])


class GlobalCreateForm(FlaskForm):
    template_type = GLOBAL
    name = StringField(TEMPLATE_NAME_PROMPT)
    description = TextAreaField(TEMPLATE_DESCRIPTION_PROMPT, render_kw={"rows": "5"})
    global_name = StringField(GLOBAL_NAME_PROMPT)
    is_global_record = BooleanField(IS_GLOBAL_RECORD_PROMPT)
    hex_data = StringField(GLOBAL_HEX_DATA_PROMPT)
    seg_name = StringField(GLOBAL_SEG_NAME_PROMPT)
    field_data = TextAreaField(GLOBAL_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Create New Global Template")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        if request.method == "POST":
            body = {"global_name": self.global_name.data, "is_global_record": self.is_global_record.data,
                    "field_data": self.field_data.data, "hex_data": self.hex_data.data,
                    "seg_name": self.seg_name.data.upper(), "name": self.name.data,
                    "description": self.description.data}
            self.response = Server.create_new_global_template(body)

    def validate_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "name" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["name"])

    def validate_description(self, _):
        if "error_fields" in self.response and "description" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["description"])

    def validate_global_name(self, _):
        if "error_fields" in self.response and "global_name" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["global_name"])

    def validate_is_global_record(self, _):
        if "error_fields" in self.response and "is_global_record" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["is_global_record"])

    def validate_hex_data(self, _):
        if "error_fields" in self.response and "hex_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["hex_data"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])

    def validate_seg_name(self, _):
        if "error_fields" in self.response and "seg_name" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["seg_name"])


class AaaCreateForm(FlaskForm):
    template_type = AAA
    name = StringField(TEMPLATE_NAME_PROMPT)
    description = TextAreaField(TEMPLATE_DESCRIPTION_PROMPT, render_kw={"rows": "5"})
    field_data = TextAreaField(MACRO_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Create New AAA Template")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        if request.method == "POST":
            body = {"field_data": self.field_data.data, "name": self.name.data, "description": self.description.data}
            self.response = Server.create_new_aaa_template(body)

    def validate_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "name" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["name"])

    def validate_description(self, _):
        if "error_fields" in self.response and "description" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["description"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])


class PnrAddForm(FlaskForm):
    key = SelectField(f"{PNR_KEY_PROMPT} (Only select a key that is not already added)", choices=Config.PNR_KEYS,
                      default="header")
    text = StringField(PNR_TEXT_PROMPT)
    field_data = TextAreaField(PNR_INPUT_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Add Key To PNR Template")

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        self.display_fields = [("Name", name)]
        if request.method == "POST":
            body = {"key": self.key.data, "field_data": self.field_data.data, "text": self.text.data, "name": name}
            self.response = Server.add_to_existing_pnr_template(body)

    def validate_key(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "key" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["key"])

    def validate_text(self, _):
        if "error_fields" in self.response and "text" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["text"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])


class GlobalAddForm(FlaskForm):
    global_name = StringField(GLOBAL_NAME_PROMPT)
    is_global_record = BooleanField(IS_GLOBAL_RECORD_PROMPT)
    hex_data = StringField(GLOBAL_HEX_DATA_PROMPT)
    seg_name = StringField(GLOBAL_SEG_NAME_PROMPT)
    field_data = TextAreaField(GLOBAL_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Add Global To Template")

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        self.display_fields = [("Name", name)]
        if request.method == "POST":
            body = {"name": name, "is_global_record": self.is_global_record.data,
                    "seg_name": self.seg_name.data.upper(), "field_data": self.field_data.data,
                    "hex_data": self.hex_data.data, "global_name": self.global_name.data}
            self.response = Server.add_to_existing_global_template(body)

    def validate_global_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "global_name" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["global_name"])

    def validate_is_global_record(self, _):
        if "error_fields" in self.response and "is_global_record" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["is_global_record"])

    def validate_hex_data(self, _):
        if "error_fields" in self.response and "hex_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["hex_data"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])

    def validate_seg_name(self, _):
        if "error_fields" in self.response and "seg_name" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["seg_name"])


class PnrUpdateForm(FlaskForm):
    text = StringField(PNR_TEXT_PROMPT)
    field_data = TextAreaField(PNR_INPUT_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Update PNR")

    def __init__(self, template: Munch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = list()
        self.display_fields.append(("Name", template.name))
        pwc = f"{' (PNR Working copy)' if template.locator == Config.AAAPNR else str()}"
        self.display_fields.append(("PNR Locator", f"{template.locator}{pwc}"))
        self.display_fields.append(("Key", template.key.upper()))
        self.response: Munch = Munch()
        if request.method == "GET":
            self.text.data = template.text
            self.field_data.data = template.field_data
        if request.method == "POST":
            body: dict = init_body(self.data, RequestType.TEMPLATE_PNR_UPDATE)
            self.response = Server.update_pnr_template(template.id, body)
        return

    def validate_text(self, _):
        evaluate_error(self.response, "text", message=True)

    def validate_field_data(self, _):
        evaluate_error(self.response, "field_data")


class GlobalUpdateForm(FlaskForm):
    is_global_record = BooleanField(IS_GLOBAL_RECORD_PROMPT)
    hex_data = StringField(GLOBAL_HEX_DATA_PROMPT)
    seg_name = StringField(GLOBAL_SEG_NAME_PROMPT)
    field_data = TextAreaField(GLOBAL_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Update Global")

    def __init__(self, template: Munch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = list()
        self.display_fields.append(("Template Name", template.name))
        self.display_fields.append(("Global Name", template.global_name))
        self.response: Munch = Munch()
        if request.method == "GET":
            self.is_global_record.data = template.is_global_record
            self.hex_data.data = template.hex_data
            self.field_data.data = template.field_data
            self.seg_name.data = template.seg_name
        if request.method == "POST":
            body = init_body(self.data, RequestType.TEMPLATE_GLOBAL_UPDATE)
            self.response = Server.update_global_template(template.id, body)

    def validate_is_global_record(self, _):
        evaluate_error(self.response, "is_global_record", message=True)

    def validate_hex_data(self, _):
        evaluate_error(self.response, "hex_data")

    def validate_field_data(self, _):
        evaluate_error(self.response, "field_data")

    def validate_seg_name(self, _):
        evaluate_error(self.response, "seg_name")


class AaaUpdateForm(FlaskForm):
    field_data = TextAreaField(MACRO_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Update AAA")

    def __init__(self, template: Munch, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = list()
        self.display_fields.append(("Template Name", template.name))
        self.response: Munch = Munch()
        if request.method == "GET":
            self.field_data.data = template.field_data
        if request.method == "POST":
            body = init_body(self.data, RequestType.TEMPLATE_AAA_UPDATE)
            self.response = Server.update_aaa_template(template.id, body)

    def validate_field_data(self, _):
        evaluate_error(self.response, "field_data", message=True)


class TemplateRenameCopyForm(FlaskForm):
    name = StringField(TEMPLATE_NAME_PROMPT)
    description = TextAreaField(TEMPLATE_DESCRIPTION_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Template")

    def __init__(self, template: dict, action: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = [("Existing Name", template["name"])]
        self.response: dict = dict()
        self.save.label.text = "Rename Template" if action == "rename" else "Copy Template"
        if request.method == "GET" and action == "rename":
            self.name.data = template["name"]
            self.description.data = template["description"]
        if request.method == "POST":
            body = {"old_name": template["name"], "new_name": self.name.data, "description": self.description.data}
            self.response = Server.rename_template(body) if action == "rename" else Server.copy_template(body)

    def validate_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response:
                if "old_name" in self.response["error_fields"]:
                    raise ValidationError(self.response["error_fields"]["old_name"])
                if "new_name" in self.response["error_fields"]:
                    raise ValidationError(self.response["error_fields"]["new_name"])
        return

    def validate_description(self, _):
        if "error_fields" in self.response and "description" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["description"])


class TemplateDeleteForm(FlaskForm):
    template_id = HiddenField()
    submit = SubmitField("Yes - Delete")

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response: dict = dict()
        if request.method == "POST":
            if self.template_id.data:
                self.response = Server.delete_template_by_id(self.template_id.data)
            else:
                self.response = Server.delete_template_by_name({"name": name})


class TemplateLinkMergeForm(FlaskForm):
    variation = SelectField(VARIATION_PROMPT, coerce=int)
    variation_name = StringField(VARIATION_NAME_PROMPT)
    template_name = SelectField("Select a template")
    save = SubmitField("Template with Test Data")

    def __init__(self, test_data_id: str, template_type: str, action_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        v_type = "pnr" if template_type == PNR else "core"
        body: dict = init_variation(self.variation, self.variation_name, test_data_id, v_type)
        if not current_user.is_authenticated:
            return
        templates: dict = Server.get_templates(template_type=template_type)
        if not current_user.is_authenticated:
            return
        self.template_name.choices = [(template["name"], template["name"]) for template in templates]
        self.response = dict()
        self.save.label.text = f"{action_type.title()} {self.save.label.text}"
        if request.method == "POST":
            body["template_name"] = self.template_name.data
            if action_type == "merge":
                if template_type == PNR:
                    self.response = Server.merge_pnr_template(test_data_id, body)
                elif template_type == GLOBAL:
                    self.response = Server.merge_global_template(test_data_id, body)
                elif template_type == AAA:
                    self.response = Server.merge_aaa_template(test_data_id, body)
            else:
                if template_type == PNR:
                    self.response = Server.create_link_pnr_template(test_data_id, body)
                elif template_type == GLOBAL:
                    self.response = Server.create_link_global_template(test_data_id, body)
                elif template_type == AAA:
                    self.response = Server.create_link_aaa_template(test_data_id, body)

    def validate_variation(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "variation" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["variation"])

    def validate_variation_name(self, _):
        if "error_fields" in self.response and "variation_name" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["variation_name"])

    def validate_template_name(self, _):
        if "error_fields" in self.response and "template_name" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["template_name"])


class TemplateLinkUpdateForm(FlaskForm):
    template_name = SelectField("Select a template")
    save = SubmitField("Update links")

    def __init__(self, test_data_id: str, td_element: dict, template_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = list()
        variation_name = f" ({td_element['variation_name']})" if td_element["variation_name"] else str()
        self.display_fields.append(("Variation", f"{td_element['variation']}{variation_name}"))
        self.display_fields.append(("Template Name", td_element["link"]))
        templates: dict = Server.get_templates(template_type=template_type)
        if not current_user.is_authenticated:
            return
        self.template_name.choices = [(template["name"], template["name"]) for template in templates]
        self.response = dict()
        if request.method == "POST":
            body = {"variation_name": self.template_name.data, "template_name": td_element["link"],
                    "variation": td_element["variation"]}
            if template_type == PNR:
                self.response = Server.update_link_pnr_template(test_data_id, body)
            elif template_type == GLOBAL:
                self.response = Server.update_link_global_template(test_data_id, body)
            elif template_type == AAA:
                self.response = Server.update_link_aaa_template(test_data_id, body)
        else:
            self.template_name.data = td_element["link"]

    def validate_template_name(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response:
                for error_label in self.response["error_fields"]:
                    raise ValidationError(self.response["error_fields"][error_label])
