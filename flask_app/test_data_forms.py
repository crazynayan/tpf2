from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import DataRequired, ValidationError, NumberRange

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
    confirm = SubmitField('Confirm - Create Data')


class DeleteForm(FlaskForm):
    delete = SubmitField('Delete - This Test Data (Permanently)')


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
    base_reg = StringField('Base Register - Keep it R0 for default macros like AAA, ECB, GLOBAL, IMG etc.',
                           default='R0', validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    def __init__(self, macro_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.macro_name = macro_name

    def validate_base_reg(self, base_reg: StringField) -> None:
        base_reg.data = base_reg.data.upper()
        if base_reg.data and base_reg.data not in tpf2_app.config['REGISTERS']:
            raise ValidationError('Invalid Base Register - Register can be from R0 to R15')
        if base_reg.data == 'R0' and self.macro_name not in tpf2_app.config['DEFAULT_MACROS']:
            raise ValidationError(f"Base Register cannot be R0 for macro {self.macro_name}")
        return


class FieldDataForm(FlaskForm):
    field_data = StringField("Enter Data - Input hex characters. Odd number of digit will be considered a number. "
                             "Prefix with 0 to make the number of digit. Non hex characters are considered as text. "
                             "Prefix with quote to enforce text.", validators=[DataRequired()])
    save = SubmitField('Save & Continue - Add Further Data')

    def validate_field_data(self, field_data: StringField) -> None:
        hex_data = field_data.data.strip().upper()
        if hex_data.startswith("'"):
            if len(hex_data) == 1:
                raise ValidationError("There needs to be some text after a single quote")
            hex_data = hex_data[1:].encode('cp037').hex().upper()
        elif hex_data.startswith("-"):
            if len(hex_data) == 1 or not hex_data[1:].isdigit():
                raise ValidationError("Invalid Negative Number")
            neg_data = int(hex_data)
            if neg_data < -0x80000000:
                raise ValidationError(f"Negative Number cannot be less than {-0x80000000}")
            hex_data = f"{neg_data & tpf2_app.config['REG_MAX']:08X}"
        elif len(hex_data) % 2 == 1 and hex_data.isdigit():
            number_data = int(hex_data)
            if number_data > 0x7FFFFFFF:
                raise ValidationError(f"Number cannot be greater than {0x7FFFFFFF}")
            hex_data = f"{number_data:08X}"
        else:
            try:
                int(hex_data, 16)
                if len(hex_data) % 2:
                    hex_data = f"0{hex_data}"
            except ValueError:
                hex_data = hex_data.encode('cp037').hex().upper()
        field_data.data = hex_data
        return


class RegisterFieldDataForm(FieldDataForm):
    reg = StringField('Enter Register - Valid values are from R0 to R15')

    @staticmethod
    def validate_reg(_, reg: StringField) -> None:
        reg.data = reg.data.upper()
        if reg.data not in tpf2_app.config['REGISTERS']:
            raise ValidationError("Invalid Register - Register can be from R0 to R15")
        return

    def validate_field_data(self, field_data: StringField) -> None:
        super().validate_field_data(field_data)
        hex_data = field_data.data
        hex_data = hex_data[:8]
        hex_data = hex_data.zfill(8)
        field_data.data = hex_data


class PnrForm(FlaskForm):
    key = SelectField('Select type of PNR element', choices=tpf2_app.config['PNR_KEYS'], default='name')
    locator = StringField('Enter PNR Locator - 6 character alpha numeric - Leave it blank for AAA PNR')
    text_data = StringField('Enter text - Separate it with comma for multiple PNR elements.'
                            'Leave it blank if you plan to add PNR fields.')
    save = SubmitField('Save & Continue - Add PNR Data')

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
        text_data.data = text_data.data.upper()
