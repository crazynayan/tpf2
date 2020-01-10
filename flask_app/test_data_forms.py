from base64 import b64encode

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, NumberRange, Length

from flask_app import tpf2_app
from flask_app.server import Server


class TestDataForm(FlaskForm):
    name = StringField('Name of Test Data (Must be unique in the system)', validators=[DataRequired()])
    seg_name = StringField('Segment Name (Must exists in the system)', validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_seg_name(_, seg_name: StringField) -> None:
        seg_name.data = seg_name.data.upper()
        seg_name = seg_name.data
        if seg_name not in Server.segments():
            raise ValidationError(f"{seg_name} not found")
        return

    @staticmethod
    def validate_name(_, name: StringField) -> None:
        if Server.get_test_data_by_name(name.data):
            raise ValidationError(f"The name '{name.data}' already exists - Please use an unique name")
        return


class ConfirmForm(FlaskForm):
    confirm = SubmitField('Save & Close')


class DeleteForm(FlaskForm):
    delete = SubmitField('Delete Test Data')


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
    def validate_field(_, field: StringField) -> None:
        field.data = field.data.upper()
        label_ref = Server.search_field(field.data)
        if not label_ref:
            raise ValidationError('Field name not found')
        field.data = label_ref


class FieldLengthForm(FlaskForm):
    length = IntegerField('Length', validators=[NumberRange(1, 4095, "Length can be from 1 to 4095")])
    base_reg = StringField('Base Register - Keep it blank for default macros like AAA, ECB, GLOBAL, IMG etc.')
    save = SubmitField('Save & Continue - Add Further Data')

    def __init__(self, macro_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.macro_name = macro_name

    def validate_base_reg(self, base_reg: StringField) -> None:
        base_reg.data = base_reg.data.upper()
        if base_reg.data and base_reg.data not in tpf2_app.config['REGISTERS']:
            raise ValidationError('Invalid Base Register - Register can be from R0 to R15')
        if (not base_reg.data or base_reg.data == 'R0') and self.macro_name not in tpf2_app.config['DEFAULT_MACROS']:
            raise ValidationError(f"Base Register cannot be blank or R0 for macro {self.macro_name}")
        return


def form_validate_field_data(data) -> str:
    data = data.strip().upper()
    if data.startswith("'"):
        if len(data) == 1:
            raise ValidationError("There needs to be some text after a single quote")
        data = data[1:].encode('cp037').hex().upper()
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
            data = data.encode('cp037').hex().upper()
    return data


class FieldDataForm(FlaskForm):
    field_data = StringField("Enter Data - Input hex characters. Odd number of digit will be considered a number. "
                             "Prefix with 0 to make the number a digit. Non hex characters are considered as text. "
                             "Prefix with quote to enforce text.", validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_field_data(_, field_data: StringField) -> None:
        field_data.data = form_validate_field_data(field_data.data)


class RegisterFieldDataForm(FlaskForm):
    reg = StringField('Enter Register - Valid values are from R0 to R15')
    field_data = StringField("Enter Data - Input hex characters. Odd number of digit will be considered a number. "
                             "Prefix with 0 to make the number a digit. Non hex characters are considered as text. "
                             "Prefix with quote to enforce text.", validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_reg(_, reg: StringField) -> None:
        reg.data = reg.data.upper()
        if reg.data not in tpf2_app.config['REGISTERS']:
            raise ValidationError("Invalid Register - Register can be from R0 to R15")
        return

    @staticmethod
    def validate_field_data(_, field_data: StringField) -> None:
        hex_data = form_validate_field_data(field_data.data)
        hex_data = hex_data[:8]
        hex_data = hex_data.zfill(8)
        field_data.data = hex_data


class PnrForm(FlaskForm):
    key = SelectField('Select type of PNR element', choices=tpf2_app.config['PNR_KEYS'], default='name')
    locator = StringField('Enter PNR Locator - 6 character alpha numeric - Leave it blank for AAA PNR')
    text_data = StringField('Enter text - Separate it with comma for multiple PNR elements. '
                            'Leave it blank for adding PNR fields later.')
    save = SubmitField('Save & Continue - Add Further Data')

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


class MultipleFieldDataForm(FlaskForm):
    field_data = TextAreaField('Enter multiple field and data separated by comma. The field and data should be '
                               'separated by colon. All fields should be from a single macro. Data by default is in '
                               'hex characters. Odd number of digit will be considered a number. '
                               'Prefix with 0 to make the number a digit. Non hex characters are considered as text. '
                               'Prefix with quote to enforce text.', render_kw={'rows': '5'},
                               validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_field_data(_, field_data: TextAreaField):
        data_stream: str = field_data.data
        data_dict = {'macro_name': str(), 'field_data': dict()}
        for key_value in data_stream.split(','):
            if key_value.count(':') != 1:
                raise ValidationError(f"Include a single colon : to separate field and data - {key_value}")
            key = key_value.split(':')[0].strip().upper()
            label_ref = Server.search_field(key)
            if not label_ref:
                raise ValidationError(f'Field name not found - {key}')
            data_dict['macro_name'] = data_dict['macro_name'] or label_ref['name']
            if data_dict['macro_name'] != label_ref['name']:
                raise ValidationError(f"Field not in the same macro - {key} not in {data_dict['macro_name']}")
            data = form_validate_field_data(key_value.split(':')[1])
            data = b64encode(bytes.fromhex(data)).decode()
            data_dict['field_data'][key] = data
        field_data.data = data_dict


class TpfdfForm(FlaskForm):
    macro_name = StringField('Enter the name of TPFDF macro', validators=[DataRequired()])
    key = StringField('Enter key as 2 hex characters',
                      validators=[DataRequired(), Length(min=2, max=2, message='Please enter 2 characters only')])
    field_data = TextAreaField('Enter multiple field and data separated by comma. The field and data should be '
                               'separated by colon. All fields should be from a single macro mentioned above. '
                               'Data by default is in hex characters. Odd number of digit will be considered a number. '
                               'Prefix with 0 to make the number a digit. Non hex characters are considered as text. '
                               'Prefix with quote to enforce text.', render_kw={'rows': '5'},
                               validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    @staticmethod
    def validate_macro_name(_, macro_name: StringField):
        macro_name.data = macro_name.data.upper()
        label_ref = Server.search_field(macro_name.data)
        if not label_ref or label_ref['name'] != macro_name.data:
            raise ValidationError('This is not a valid macro name')

    @staticmethod
    def validate_key(_, key: StringField):
        key.data = key.data.upper()
        try:
            int(key.data, 16)
        except ValueError:
            raise ValidationError('Please enter hex characters only')
        return

    def validate_field_data(self, field_data: TextAreaField):
        updated_field_data = list()
        for key_value in field_data.data.split(','):
            if key_value.count(':') != 1:
                raise ValidationError(f"Include a single colon : to separate field and data - {key_value}")
            field = key_value.split(':')[0].strip().upper()
            label_ref = Server.search_field(field)
            if not label_ref:
                raise ValidationError(f'Field name not found - {field}')
            if self.macro_name.data != label_ref['name']:
                raise ValidationError(f"Field not in the same macro - {field} not in {self.macro_name.data}")
            data = form_validate_field_data(key_value.split(':')[1])
            updated_field_data.append(f"{field}:{data}")
        field_data.data = ','.join(updated_field_data)
