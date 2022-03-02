from flask import request
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, SubmitField, ValidationError

from config import Config
from flask_app.form_prompts import PNR_KEY_PROMPT, PNR_LOCATOR_PROMPT, PNR_TEXT_PROMPT, PNR_INPUT_FIELD_DATA_PROMPT, \
    TEMPLATE_NAME_PROMPT, TEMPLATE_DESCRIPTION_PROMPT, VARIATION_PROMPT, VARIATION_NAME_PROMPT
from flask_app.server import Server
from flask_app.test_data_forms import init_variation


class PnrCreateForm(FlaskForm):
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


class PnrUpdateForm(FlaskForm):
    text = StringField(PNR_TEXT_PROMPT)
    field_data = TextAreaField(PNR_INPUT_FIELD_DATA_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Update PNR Key")

    def __init__(self, pnr_template: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = list()
        self.display_fields.append(("Name", pnr_template["name"]))
        pwc = f"{' (PNR Working copy)' if pnr_template['locator'] == Config.AAAPNR else str()}"
        self.display_fields.append(("PNR Locator", f"{pnr_template['locator']}{pwc}"))
        self.display_fields.append(("Key", pnr_template["key"].upper()))
        self.response: dict = dict()
        if request.method == "GET":
            self.text.data = pnr_template["text"]
            self.field_data.data = pnr_template["field_data"]
        if request.method == "POST":
            body: dict = {"text": self.text.data, "field_data": self.field_data.data, "id": pnr_template["id"]}
            self.response = Server.update_pnr_template(body)

    def validate_text(self, _):
        if "error" in self.response and self.response["error"]:
            if "message" in self.response and self.response["message"]:
                raise ValidationError(self.response["message"])
            if "error_fields" in self.response and "text" in self.response["error_fields"]:
                raise ValidationError(self.response["error_fields"]["text"])

    def validate_field_data(self, _):
        if "error_fields" in self.response and "field_data" in self.response["error_fields"]:
            raise ValidationError(self.response["error_fields"]["field_data"])


class TemplateRenameForm(FlaskForm):
    name = StringField(TEMPLATE_NAME_PROMPT)
    description = TextAreaField(TEMPLATE_DESCRIPTION_PROMPT, render_kw={"rows": "5"})
    save = SubmitField("Rename Template")

    def __init__(self, template: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.display_fields = [("Existing Name", template["name"])]
        self.response: dict = dict()
        if request.method == "GET":
            self.name.data = template["name"]
            self.description.data = template["description"]
        if request.method == "POST":
            body = {"old_name": template["name"], "new_name": self.name.data, "description": self.description.data}
            self.response = Server.rename_template(body)

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


class TemplateMergeForm(FlaskForm):
    variation = SelectField(VARIATION_PROMPT, coerce=int)
    variation_name = StringField(VARIATION_NAME_PROMPT)
    template_name = SelectField("Select a template")
    save = SubmitField("Merge Template with Test Data")

    def __init__(self, test_data_id: str, template_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        body: dict = init_variation(self.variation, self.variation_name, test_data_id, template_type)
        if not current_user.is_authenticated:
            return
        if request.method == "GET":
            templates: dict = Server.get_pnr_templates()
            if not current_user.is_authenticated:
                return
            self.template_name.choices = [(template["name"], template["name"]) for template in templates]
            self.response = dict()
        elif request.method == "POST":
            self.template_name.choices = [(self.template_name.data, self.template_name.data)]
            body["template_name"] = self.template_name.data
            self.response = Server.merge_pnr_template(test_data_id, body)

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
