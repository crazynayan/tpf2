VARIATION_PROMPT: str = "Select variation or choose 'New Variation' to create a new variation"
VARIATION_NAME_PROMPT: str = "New Variation Name - Leave it blank for existing variation"

OLD_FIELD_DATA_PROMPT: str = """
Enter multiple fields and data separated by comma. The field and data should be separated by colon. All fields should be 
 from a single macro mentioned above. Data by default is in hex characters. Odd number of digit will be considered a 
 4 byte number. Prefix with 0 to make it odd for enforcing a number. Non hex characters are considered as text. Prefix 
 with quote to enforce text.
"""
PNR_OUTPUT_FIELD_DATA_PROMPT: str = """
Enter multiple fields with attributes separated by comma. Format of each field is FieldName:Length:ItemNumber.
 FieldName should be from PNR macros. Length should start with L followed by a number. If it is not specified
 then the length from the data macro will be automatically determined. ItemNumber should start with I followed by a
 number. If it is not specified then item number 1 is assumed. An e.g. is as follows
 PR00_G0_TYP,PR00_G0_TYP:I2,PR00_G0_TYP:L2:I3
"""
PNR_INPUT_FIELD_DATA_PROMPT: str = """
Enter multiple fields with attributes separated by comma. Leave it blank if you want to provide PNR text.
 Format of each field is FieldName:HexData:ItemNumber. FieldName should be from PNR macros. 
 ItemNumber should start with I followed by a number. All item numbers should be in sequence without gaps. 
 An e.g. is as follows PR00_G0_BAS_0_AAC:E2E2:I1,PR00_G0_TYP:02:I2
"""

PNR_KEY_PROMPT: str = "Select type of PNR element"
PNR_LOCATOR_PROMPT: str = "Enter PNR Locator - 6 character alpha numeric - Leave it blank for AAA PNR"
PNR_TEXT_PROMPT: str = """
    Enter text - Separate it with comma for multiple PNR elements.\n
    Leave it blank if you want to provide field data in hex.
"""

GLOBAL_NAME_PROMPT: str = "Enter Global Name - Must exists in global definition"
IS_GLOBAL_RECORD_PROMPT: str = "Check this if this global is a global record. (Unchecked indicates global field)"
GLOBAL_HEX_DATA_PROMPT: str = """
    Global Field - Enter input data in hex format to initialize the global field. \nLeave it blank for global record.
"""
GLOBAL_SEG_NAME_PROMPT: str = "Global Record - Segment Name. Only required if data for global record is specified."
GLOBAL_FIELD_DATA_PROMPT: str = """
    Global Record - Enter multiple fields and data separated by comma.\n 
    The field and data should be separated by colon. Data should be in hex format.\n Leave it blank to init with zeroes.
"""

TEMPLATE_NAME_PROMPT: str = "Enter a name that uniquely identifies your template"
TEMPLATE_DESCRIPTION_PROMPT: str = "Enter the purpose of the template"
