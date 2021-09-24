from base64 import b64encode
from typing import List

from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, SelectField, TextAreaField
from wtforms.validators import InputRequired, ValidationError, NumberRange, Length
from wtforms.widgets import Input

from flask_app import tpf2_app
from flask_app.server import Server

FIELD_DATA_TEXT: str = """
Enter multiple fields and data separated by comma. The field and data should be separated by colon. All fields should be 
 from a single macro mentioned above. Data by default is in hex characters. Odd number of digit will be considered a 
 4 byte number. Prefix with 0 to make it odd for enforcing a number. Non hex characters are considered as text. Prefix 
 with quote to enforce text.
"""

PNR_OUTPUT_FIELD_DATA_TEXT: str = """
Enter multiple fields and length separated by comma. The field and length should be separated by colon. All
 fields should be from PR001W macro. Length is an integer number which indicates the length of the field. If you don't 
 know the length then put the length as 0 and the length from the data macro will be automatically determined.
"""


def form_validate_field_data(data: str) -> str:
    data = data.strip().upper()
    if data.startswith("'"):
        if len(data) == 1:
            raise ValidationError("There needs to be some text after a single quote")
        data = data[1:].encode("cp037").hex().upper()
    elif data.startswith("-"):
        if len(data) == 1 or not data[1:].isdigit():
            raise ValidationError("Invalid Negative Number")
        neg_data = int(data)
        if neg_data < -0x80000000:
            raise ValidationError(f"Negative Number cannot be less than {-0x80000000}")
        data = f"{neg_data & tpf2_app.config['REG_MAX']:08X}"
    elif len(data) % 2 == 1 and data.isdigit():
        number_data = int(data)
        if number_data > 0x7FFFFFFF:
            raise ValidationError(f"Number cannot be greater than {0x7FFFFFFF}")
        data = f"{number_data:08X}"
    else:
        try:
            int(data, 16)
            if len(data) % 2:
                data = f"0{data}"
        except ValueError:
            data = data.encode("cp037").hex().upper()
    return data


def form_validate_multiple_field_data(data: str, macro_name: str) -> str:
    updated_field_data = list()
    for key_value in data.split(","):
        if key_value.count(":") != 1:
            raise ValidationError(f"Include a single colon : to separate field and data - {key_value}")
        field = key_value.split(":")[0].strip().upper()
        label_ref = Server.search_field(field)
        if not label_ref:
            raise ValidationError(f"Field name not found - {field}")
        if macro_name != label_ref["name"]:
            raise ValidationError(f"Field not in the same macro - {field} not in {macro_name}")
        data = form_validate_field_data(key_value.split(":")[1])
        updated_field_data.append(f"{field}:{data}")
    return ",".join(updated_field_data)


def form_field_lookup(data: str, macro_name: str) -> str:
    data = data.upper()
    label_ref = Server.search_field(data)
    if not label_ref:
        raise ValidationError(f"Field name not found - {data}")
    if macro_name != label_ref["name"]:
        raise ValidationError(f"Field not in the same macro - {data} not in {macro_name}")
    return data


def form_validate_macro_name(macro_name: str) -> str:
    macro_name = macro_name.upper()
    label_ref = Server.search_field(macro_name)
    if not label_ref or label_ref["name"] != macro_name:
        raise ValidationError("This is not a valid macro name")
    return macro_name


class TestDataForm(FlaskForm):
    name = StringField("Name of Test Data (Must be unique in the system)", validators=[InputRequired()])
    seg_name = StringField("Segment Name (Must exists in the system)", validators=[InputRequired()])
    stop_segments = StringField("Stop Segment Name List (Separate multiple segments with comma). Optional")
    save = SubmitField("Save & Continue - Add Further Data")

    def __init__(self, test_data: dict = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.segments: List[str] = list()
        self.stop_segment_list: List[str] = list()
        self.test_data: dict = test_data if test_data else dict()
        if test_data and request.method == "GET":
            self.name.data = test_data["name"]
            self.seg_name.data = test_data["seg_name"]
            stop_segments: List[str] = test_data["stop_segments"]
            self.stop_segments.data = ", ".join(stop_segments)

    def validate_seg_name(self, seg_name: StringField):
        seg_name.data = seg_name.data.upper()
        segment: str = seg_name.data
        if not self.segments:
            response = Server.segments()
            self.segments: List[str] = response["segments"] if "segments" in response else list()
        if segment not in self.segments:
            raise ValidationError(f"{segment} not found")
        return

    def validate_stop_segments(self, stop_segments: StringField):
        stop_segments.data = stop_segments.data.upper().strip()
        if not stop_segments.data:
            return
        self.stop_segment_list: List[str] = stop_segments.data.split(",")
        self.stop_segment_list = [segment.strip() for segment in self.stop_segment_list]
        invalid_segments: List[str] = [segment for segment in self.stop_segment_list
                                       if len(segment) != 4 or not segment.isalnum()]
        if invalid_segments:
            raise ValidationError(f"{', '.join(invalid_segments)} are invalid segments.")
        return

    def validate_name(self, name: StringField):
        if (not self.test_data or self.test_data["name"] != name.data) and Server.get_test_data_by_name(name.data):
            raise ValidationError(f"The name '{name.data}' already exists - Please use an unique name")
        return


class DeleteForm(FlaskForm):
    delete = SubmitField("Delete Test Data")


class RegisterForm(FlaskForm):
    r0 = BooleanField("R0")
    r1 = BooleanField("R1")
    r2 = BooleanField("R2")
    r3 = BooleanField("R3")
    r4 = BooleanField("R4")
    r5 = BooleanField("R5")
    r6 = BooleanField("R6")
    r7 = BooleanField("R7")
    r8 = BooleanField("R8")
    r9 = BooleanField("R9")
    r10 = BooleanField("R10")
    r11 = BooleanField("R11")
    r12 = BooleanField("R12")
    r13 = BooleanField("R13")
    r14 = BooleanField("R14")
    r15 = BooleanField("R15")
    save = SubmitField("Save & Continue - Add Further Data")


class FieldSearchForm(FlaskForm):
    field = StringField("Field name", validators=[InputRequired()])
    search = SubmitField("Search")

    @staticmethod
    def validate_field(_, field: StringField) -> None:
        field.data = field.data.upper()
        label_ref = Server.search_field(field.data)
        if not label_ref:
            raise ValidationError("Field name not found")
        field.data = label_ref


class FieldLengthForm(FlaskForm):
    length = IntegerField("Length", validators=[NumberRange(1, 4095, "Length can be from 1 to 4095")])
    base_reg = StringField("Base Register - Keep it blank for default macros like AAA, ECB, GLOBAL, IMG etc.")
    save = SubmitField("Save & Continue - Add Further Data")

    def __init__(self, macro_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.macro_name = macro_name

    def validate_base_reg(self, base_reg: StringField) -> None:
        base_reg.data = base_reg.data.upper()
        if base_reg.data and base_reg.data not in tpf2_app.config["REGISTERS"]:
            raise ValidationError("Invalid Base Register - Register can be from R0 to R15")
        if (not base_reg.data or base_reg.data == "R0") and self.macro_name not in tpf2_app.config["DEFAULT_MACROS"]:
            raise ValidationError(f"Base Register cannot be blank or R0 for macro {self.macro_name}")
        return


class FieldDataForm(FlaskForm):
    variation = SelectField("Select variation or choose 'New Variation' to create a new variation", coerce=int)
    variation_name = StringField("New Variation Name - Leave it blank for existing variation")
    field_data = StringField("Enter Data - Input hex characters. Odd number of digit will be considered a number. "
                             "Prefix with 0 to make the number a digit. Non hex characters are considered as text. "
                             "Prefix with quote to enforce text.", validators=[InputRequired()])
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_field_data(_, field_data: StringField) -> None:
        field_data.data = form_validate_field_data(field_data.data)


class RegisterFieldDataForm(FlaskForm):
    reg = StringField("Enter Register - Valid values are from R0 to R15")
    field_data = StringField("Enter Data - Input hex characters. Odd number of digit will be considered a number. "
                             "Prefix with 0 to make the number a digit. Non hex characters are considered as text. "
                             "Prefix with quote to enforce text.", validators=[InputRequired()])
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_reg(_, reg: StringField) -> None:
        reg.data = reg.data.upper()
        if reg.data not in tpf2_app.config["REGISTERS"]:
            raise ValidationError("Invalid Register - Register can be from R0 to R15")
        return

    @staticmethod
    def validate_field_data(_, field_data: StringField) -> None:
        hex_data = form_validate_field_data(field_data.data)
        hex_data = hex_data[:8]
        hex_data = hex_data.zfill(8)
        field_data.data = hex_data


class PnrForm(FlaskForm):
    variation = SelectField("Select variation or choose 'New Variation' to create a new variation", coerce=int)
    variation_name = StringField("New Variation Name - Leave it blank for existing variation")
    key = SelectField("Select type of PNR element", choices=tpf2_app.config["PNR_KEYS"], default="name")
    locator = StringField("Enter PNR Locator - 6 character alpha numeric - Leave it blank for AAA PNR")
    text_data = StringField("Enter text - Separate it with comma for multiple PNR elements. "
                            "Leave it blank for adding PNR fields later.")
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_locator(_, locator):
        if not locator.data:
            return
        locator.data = locator.data.upper()
        if len(locator.data) != 6 or not locator.data.isalnum():
            raise ValidationError("PNR Locator needs to be 6 character alpha numeric")
        return

    @staticmethod
    def validate_text_data(_, text_data):
        text_data.data = text_data.data.strip().upper()


class PnrOutputForm(FlaskForm):
    key = SelectField("Select type of PNR element", choices=tpf2_app.config["PNR_KEYS"], default="header")
    locator = StringField("Enter PNR Locator - 6 character alpha numeric - Leave it blank for AAA PNR")
    field_data = TextAreaField(PNR_OUTPUT_FIELD_DATA_TEXT, render_kw={"rows": "5"}, validators=[InputRequired()])
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_field_data(_, field_data: TextAreaField):
        data_stream: str = field_data.data
        data_dict = dict()
        for key_value in data_stream.split(","):
            if key_value.count(":") != 1:
                raise ValidationError(f"Include a single colon : to separate field and length - {key_value}")
            field = key_value.split(":")[0].strip().upper()
            label_ref = Server.search_field(field)
            if not label_ref:
                raise ValidationError(f"Field name not found - {field}")
            if label_ref["name"] != "PR001W":
                raise ValidationError(f"Field not in the data macro - {field} not in PR001W")
            data = key_value.split(":")[1]
            try:
                length = int(data)
            except ValueError:
                raise ValidationError(f"Length of the {field} is not an integer - {data} not a number")
            data_dict[field] = length
        field_data.data = data_dict
        return

    @staticmethod
    def validate_locator(_, locator):
        if not locator.data:
            return
        locator.data = locator.data.upper()
        if len(locator.data) != 6 or not locator.data.isalnum():
            raise ValidationError("PNR Locator needs to be 6 character alpha numeric")
        return


class MultipleFieldDataForm(FlaskForm):
    field_data = TextAreaField(FIELD_DATA_TEXT, render_kw={"rows": "5"}, validators=[InputRequired()])
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_field_data(_, field_data: TextAreaField):
        data_stream: str = field_data.data
        data_dict = {"macro_name": str(), "field_data": dict()}
        for key_value in data_stream.split(","):
            if key_value.count(":") != 1:
                raise ValidationError(f"Include a single colon : to separate field and data - {key_value}")
            key = key_value.split(":")[0].strip().upper()
            label_ref = Server.search_field(key)
            if not label_ref:
                raise ValidationError(f"Field name not found - {key}")
            data_dict["macro_name"] = data_dict["macro_name"] or label_ref["name"]
            if data_dict["macro_name"] != label_ref["name"]:
                raise ValidationError(f"Field not in the same macro - {key} not in {data_dict['macro_name']}")
            data = form_validate_field_data(key_value.split(":")[1])
            data = b64encode(bytes.fromhex(data)).decode()
            data_dict["field_data"][key] = data
        field_data.data = data_dict


class TpfdfForm(FlaskForm):
    variation = SelectField("Select variation or choose 'New Variation' to create a new variation", coerce=int)
    variation_name = StringField("New Variation Name - Leave it blank for existing variation")
    macro_name = StringField("Enter the name of TPFDF macro", validators=[InputRequired()])
    key = StringField("Enter key as 2 hex characters",
                      validators=[InputRequired(), Length(min=2, max=2, message="Please enter 2 characters only")])
    field_data = TextAreaField(FIELD_DATA_TEXT, render_kw={"rows": "5"}, validators=[InputRequired()])
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_macro_name(_, macro_name: StringField):
        macro_name.data = form_validate_macro_name(macro_name.data)

    @staticmethod
    def validate_key(_, key: StringField):
        key.data = key.data.upper()
        try:
            int(key.data, 16)
        except ValueError:
            raise ValidationError("Invalid hex characters")
        return

    def validate_field_data(self, field_data: TextAreaField):
        field_data.data = form_validate_multiple_field_data(field_data.data, self.macro_name.data)


class DebugForm(FlaskForm):
    seg_list = StringField("Enter segment names separated by comma")
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def validate_seg_list(_, seg_list: StringField):
        updated_seg_list = list()
        segments = Server.segments()
        for seg_name in seg_list.data.split(","):
            seg_name = seg_name.upper()
            if seg_name not in segments:
                raise ValidationError(f"Segment {seg_name} not present in the database")
            updated_seg_list.append(seg_name)
        seg_list.data = ",".join(updated_seg_list)


class FixedFileForm(FlaskForm):
    variation = SelectField("Select variation or choose 'New Variation' to create a new variation", coerce=int)
    variation_name = StringField("New Variation Name - Leave it blank for existing variation")
    macro_name = StringField("Fixed File - Macro Name", validators=[InputRequired()])
    rec_id = StringField("Fixed File - Record ID (4 hex characters or 2 alphabets)", validators=[InputRequired()])
    fixed_type = StringField("Fixed File - File Type (Equate name or number)", validators=[InputRequired()])
    fixed_ordinal = StringField("Fixed File - Ordinal Number (Even digit is hex or Odd digit is number)",
                                validators=[InputRequired()])
    fixed_fch_count = IntegerField("Fixed File - Number of Forward Chains", validators=[NumberRange(0, 100)], default=0,
                                   widget=Input(input_type="number"))
    fixed_fch_label = StringField("Fixed File - Forward Chain Label (Required only if number of forward chain is > 0")
    fixed_field_data = TextAreaField(f"Fixed File - Field Data ({FIELD_DATA_TEXT})", render_kw={"rows": "3"})
    fixed_item_field = StringField("Fixed File Item - Item Label")
    fixed_item_adjust = BooleanField("Fixed File Item  - Check this ON if the item field data has similar field "
                                     "names as the item field name")
    fixed_item_repeat = IntegerField("Fixed File Item - No of times you want this item to be repeated (1 to 100)",
                                     validators=[NumberRange(0, 100)], default=1, widget=Input(input_type="number"))
    fixed_item_count = StringField("Fixed File Item - Item Count Label")
    fixed_item_field_data = TextAreaField(f"Fixed File - Item Field Data ({FIELD_DATA_TEXT})", render_kw={"rows": "3"})
    pool_macro_name = StringField("Pool File - Macro Name")
    pool_rec_id = StringField("Pool File - Record Id (4 hex characters or 2 alphabets)")
    pool_index_field = StringField("Pool File - Field in Fixed File where reference of this pool file will be stored")
    pool_fch_count = IntegerField("Pool File - Number of Forward Chains", validators=[NumberRange(0, 100)], default=0,
                                  widget=Input(input_type="number"))
    pool_fch_label = StringField("Pool File - Forward Chain Label (Required only if number of forward chain is > 0")
    pool_field_data = TextAreaField(f"Pool File - Field Data ({FIELD_DATA_TEXT})", render_kw={"rows": "3"})
    pool_item_field = StringField("Pool File Item - Item Label")
    pool_item_adjust = BooleanField("Pool File Item  - Check this ON if the item field data has similar field "
                                    "names as the item field name")
    pool_item_repeat = IntegerField("Pool File Item - No of times you want this item to be repeated (1 to 100)",
                                    validators=[NumberRange(0, 100)], default=1, widget=Input(input_type="number"))
    pool_item_count = StringField("Pool File Item - Item Count Label")
    pool_item_field_data = TextAreaField(f"Pool File - Item Field Data ({FIELD_DATA_TEXT})", render_kw={"rows": "3"})
    save = SubmitField("Save & Continue - Add Further Data")

    @staticmethod
    def _validate_record_id(data: str) -> str:
        if len(data) != 2 and len(data) != 4:
            raise ValidationError("Record ID must be 2 or 4 digits")
        data = data.upper()
        if len(data) == 2:
            if data == "00":
                raise ValidationError("Record ID cannot be zeroes")
            data = data.encode("cp037").hex().upper()
        else:
            if data == "0000":
                raise ValidationError("Record ID cannot be zeroes")
            try:
                int(data, 16)
            except ValueError:
                raise ValidationError("Invalid hex characters")
        return data

    @staticmethod
    def validate_macro_name(_, macro_name: StringField):
        macro_name.data = form_validate_macro_name(macro_name.data)

    def validate_rec_id(self, rec_id: StringField):
        rec_id.data = self._validate_record_id(rec_id.data)

    @staticmethod
    def validate_fixed_type(_, fixed_type: StringField):
        fixed_type.data = fixed_type.data.upper()
        if not fixed_type.data.isdigit():
            label_ref = Server.search_field(fixed_type.data)
            if not label_ref:
                raise ValidationError(f"Equate {fixed_type.data} not found")
            fixed_type.data = str(label_ref["dsp"])
        return

    @staticmethod
    def validate_fixed_ordinal(_, fixed_ordinal: StringField):
        fixed_ordinal.data = fixed_ordinal.data.upper()
        if len(fixed_ordinal.data) % 2 == 0:
            try:
                int(fixed_ordinal.data, 16)
            except ValueError:
                raise ValidationError("Invalid hex characters")
        else:
            if not fixed_ordinal.data.isdigit():
                raise ValidationError("Invalid number")
            fixed_ordinal.data = hex(int(fixed_ordinal.data))[2:].upper()
            fixed_ordinal.data = fixed_ordinal.data if len(fixed_ordinal.data) % 2 == 0 else "0" + fixed_ordinal.data
        return

    def validate_fixed_fch_label(self, fixed_fch_label: StringField):
        if self.fixed_fch_count.data > 0 and not fixed_fch_label.data:
            raise ValidationError("Forward chain label required if forward chain count > 0")
        if fixed_fch_label.data:
            fixed_fch_label.data = form_field_lookup(fixed_fch_label.data, self.macro_name.data)
        return

    def validate_fixed_field_data(self, fixed_field_data: TextAreaField):
        if not fixed_field_data.data:
            return
        fixed_field_data.data = form_validate_multiple_field_data(fixed_field_data.data, self.macro_name.data)

    def validate_fixed_item_field(self, fixed_item_field: StringField):
        if not fixed_item_field.data:
            return
        fixed_item_field.data = form_field_lookup(fixed_item_field.data, self.macro_name.data)

    def validate_fixed_item_count(self, fixed_item_count: StringField):
        if not fixed_item_count.data:
            return
        fixed_item_count.data = form_field_lookup(fixed_item_count.data, self.macro_name.data)

    def validate_fixed_item_field_data(self, fixed_item_field_data: StringField):
        if not fixed_item_field_data.data and self.fixed_item_field.data:
            raise ValidationError("Item field data required when item field specified")
        if not fixed_item_field_data.data:
            return
        fixed_item_field_data.data = form_validate_multiple_field_data(fixed_item_field_data.data, self.macro_name.data)

    @staticmethod
    def validate_pool_macro_name(_, pool_macro_name: StringField):
        if not pool_macro_name.data:
            return
        pool_macro_name.data = form_validate_macro_name(pool_macro_name.data)

    def validate_pool_rec_id(self, pool_rec_id: StringField):
        if not pool_rec_id.data and self.pool_macro_name.data:
            raise ValidationError("Pool Record ID required if Pool Macro Name is specified")
        if not pool_rec_id.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying Record ID")
        pool_rec_id.data = self._validate_record_id(pool_rec_id.data)

    def validate_pool_index_field(self, pool_index_field: StringField):
        if not pool_index_field.data and self.pool_macro_name.data:
            raise ValidationError("Index Field required if Pool Macro Name is specified")
        if not pool_index_field.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_index_field.data = form_field_lookup(pool_index_field.data, self.macro_name.data)

    def validate_pool_fch_label(self, pool_fch_label: StringField):
        if self.pool_fch_count.data > 0 and not pool_fch_label.data:
            raise ValidationError("Forward chain label required if forward chain count > 0")
        if not pool_fch_label.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_fch_label.data = form_field_lookup(pool_fch_label.data, self.pool_macro_name.data)
        return

    def validate_pool_field_data(self, pool_field_data: TextAreaField):
        if not pool_field_data.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_field_data.data = form_validate_multiple_field_data(pool_field_data.data, self.pool_macro_name.data)

    def validate_pool_item_field(self, pool_item_field: StringField):
        if not pool_item_field.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_item_field.data = form_field_lookup(pool_item_field.data, self.pool_macro_name.data)

    def validate_pool_item_count(self, pool_item_count: StringField):
        if not pool_item_count.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_item_count.data = form_field_lookup(pool_item_count.data, self.pool_macro_name.data)

    def validate_pool_item_field_data(self, pool_item_field_data: StringField):
        if not pool_item_field_data.data and self.pool_item_field.data:
            raise ValidationError("Item field data required when item field specified")
        if not pool_item_field_data.data:
            return
        if not self.pool_macro_name.data:
            raise ValidationError("Specify Pool Macro Name before specifying this field")
        pool_item_field_data.data = form_validate_multiple_field_data(pool_item_field_data.data,
                                                                      self.pool_macro_name.data)
