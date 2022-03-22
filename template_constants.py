PNR, GLOBAL, AAA = "PNR", "Global", "AAA"
CREATE, ADD, UPDATE, UNIQUE_TAG = "create", "add", "update", "unique_tag"
TEMPLATE_TYPES = (PNR, GLOBAL)

URL: dict = {
    PNR: {
        CREATE: "create_pnr_template",
        ADD: "add_pnr_template",
        UPDATE: "update_pnr_template",
        UNIQUE_TAG: "Key",
    },
    GLOBAL: {
        CREATE: "create_global_template",
        ADD: "add_global_template",
        UPDATE: "update_global_template",
        UNIQUE_TAG: "Global Name",
    },
}


class TemplateConstant:

    def __init__(self, template_type):
        self.type = template_type

    @property
    def add(self) -> str:
        return URL[self.type][ADD]

    @property
    def create(self) -> str:
        return URL[self.type][CREATE]

    @property
    def update(self) -> str:
        return URL[self.type][UPDATE]

    @property
    def unique_tag(self) -> str:
        return URL[self.type][UNIQUE_TAG]

    @property
    def is_type_valid(self) -> bool:
        return self.type in TEMPLATE_TYPES

    def get_unique_tag_data(self, template: dict):
        if self.type == PNR:
            return template["key"].upper()
        elif self.type == GLOBAL:
            return template["global_name"]

    def get_data_type(self, template: dict):
        if self.type == PNR:
            return "Text" if template["text"] else "Field Data"
        elif self.type == GLOBAL:
            return "Global Record" if template["is_global_record"] else "Global Field"

    def get_data(self, template: dict):
        if self.type == PNR:
            return template["text"] if template["text"] else template["field_data"]
        elif self.type == GLOBAL:
            if not template["field_data"] and template["is_global_record"]:
                return "Initialized to zeroes"
            return template["field_data"] if template["is_global_record"] else template["hex_data"]
