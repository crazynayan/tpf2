from base64 import b64decode, b64encode
from typing import Dict, List
from urllib.parse import quote

import requests
from flask import flash
from flask_login import current_user, logout_user
from requests import Response

from config import Config


class Server:

    @staticmethod
    def _common_request(url: str, method: str = "GET", **kwargs) -> dict:
        request_url = f"{Config.SERVER_URL}{url}"
        if "auth" not in kwargs:
            if current_user.is_anonymous:
                return dict()
            auth_header = {"Authorization": f"Bearer {current_user.api_key}"}
            kwargs["headers"] = auth_header
        if method == "GET":
            response: Response = requests.get(request_url, **kwargs)
        elif method == "POST":
            response: Response = requests.post(request_url, **kwargs)
        elif method == "PATCH":
            response: Response = requests.patch(request_url, **kwargs)
        elif method == "DELETE":
            response: Response = requests.delete(request_url, **kwargs)
        else:
            raise TypeError
        if response.status_code == 401 and current_user.is_authenticated:
            flash("Session timeout. Please login again.")
            logout_user()
        return response.json() if response.status_code == 200 else dict()

    @staticmethod
    def _decode_data(encoded_data) -> List[str]:
        data = b64decode(encoded_data)
        hex_data = data.hex().upper()
        number_data = "Not a number"
        if not encoded_data:
            return [hex_data, number_data, str()]
        if len(hex_data) <= 8:
            number_data = int(hex_data, 16)
        if len(hex_data) == 4 and number_data > 0x7FFF:
            number_data -= 0x10000
        if len(hex_data) == 8 and number_data > 0x7FFFFFFF:
            number_data -= Config.REG_MAX + 1
        char_data = "".join([bytes([char]).decode("cp037") if bytes([char]).decode("cp037").isascii() and char >= 0x40
                             else "\u2666" for char in data])
        return [hex_data, number_data, char_data]

    @staticmethod
    def _decode_regs(regs: Dict[str, int]) -> Dict[str, list]:
        return {reg: [f"{value & Config.REG_MAX:08X}", value] for reg, value in regs.items()}

    @classmethod
    def _decode_test_data(cls, test_data: dict) -> dict:
        if "regs" in test_data and test_data["regs"]:
            test_data["regs"] = cls._decode_regs(test_data["regs"])
        for core in test_data["cores"]:
            core["hex_data"] = cls._decode_data(core["hex_data"])
            for field_data in core["field_data"]:
                field_data["data"] = cls._decode_data(field_data["data"])
        for pnr in test_data["pnr"]:
            for field_data in pnr["field_data"]:
                field_data["data"] = cls._decode_data(field_data["data"])
        for tpfdf in test_data["tpfdf"]:
            for field_data in tpfdf["field_data"]:
                field_data["data"] = cls._decode_data(field_data["data"])
        for fixed_file in test_data["fixed_files"]:
            fixed_file["rec_id"] = hex(fixed_file["rec_id"])[2:].upper()
            for field_data in fixed_file["field_data"]:
                field_data["data"] = cls._decode_data(field_data["data"])
            for file_item in fixed_file["file_items"]:
                for field_data in file_item["field_data"]:
                    field_data["data"] = cls._decode_data(field_data["data"])
            for pool_file in fixed_file["pool_files"]:
                pool_file["rec_id"] = hex(pool_file["rec_id"])[2:].upper()
                for field_data in pool_file["field_data"]:
                    field_data["data"] = cls._decode_data(field_data["data"])
                for file_item in pool_file["file_items"]:
                    for field_data in file_item["field_data"]:
                        field_data["data"] = cls._decode_data(field_data["data"])
        test_data["pnr"].sort(key=lambda pnr_item: (pnr_item["variation"], pnr_item["locator"], pnr_item["key"]))
        test_data["cores"].sort(key=lambda core_item: (core_item["variation"], core_item["macro_name"]))
        return test_data

    @classmethod
    def authenticate(cls, email: str, password: str) -> dict:
        response: dict = cls._common_request(f"/tokens", method="POST", auth=(email, password))
        return response if "token" in response else dict()

    @classmethod
    def segments(cls) -> dict:
        response: dict = cls._common_request(f"/segments")
        return response if response else dict()

    @classmethod
    def upload_segment(cls, blob_name) -> dict:
        response: dict = cls._common_request(f"/segments/upload", method="POST", json={"blob_name": blob_name})
        return response

    @classmethod
    def macros(cls) -> List[str]:
        response: dict = cls._common_request(f"/macros")
        return response["macros"] if response else list()

    @classmethod
    def instructions(cls, seg_name: str) -> dict:
        response: dict = cls._common_request(f"/segments/{seg_name}/instructions")
        instructions = response["instructions"] if response else list()
        response["formatted_instructions"] = list()
        for instruction in instructions:
            ins_dict = dict()
            ins = instruction.split(":")
            ins_dict["index"] = ins[0]
            ins_dict["label"] = ins[1]
            ins_dict["command"] = ins[2]
            ins_dict["operands"] = ins[3] if len(ins) > 3 else str()
            ins_dict["supported"] = instruction not in response["not_supported"]
            response["formatted_instructions"].append(ins_dict)
        response["formatted_not_supported"] = [ins for ins in response["formatted_instructions"]
                                               if not ins["supported"]]
        return response

    @classmethod
    def symbol_table(cls, macro_name: str) -> List[dict]:
        response: dict = cls._common_request(f"/macros/{macro_name}/symbol_table")
        return response["symbol_table"] if response else list()

    @classmethod
    def get_all_test_data(cls) -> List[dict]:
        response = cls._common_request(f"/test_data")
        return response if response else list()

    @classmethod
    def get_test_data(cls, test_data_id: str) -> dict:
        test_data: dict = cls._common_request(f"/test_data/{test_data_id}")
        if not test_data:
            return dict()
        test_data["outputs"] = test_data["outputs"][0]
        test_data["class_display"] = "disabled" if test_data["owner"] != current_user.email else str()
        test_data["stop_seg_string"] = ", ".join(test_data["stop_segments"]) if test_data["stop_segments"] else \
            "No Stop Segments"
        test_data["cores"].sort(key=lambda item: (item["macro_name"], item["heap_name"]))
        return cls._decode_test_data(test_data)

    @classmethod
    def get_test_data_by_name(cls, name: str) -> dict:
        name = quote(name)
        return cls._common_request(f"/test_data", params={"name": name})

    @classmethod
    def run_test_data(cls, test_data_id: str) -> dict:
        test_data: dict = cls._common_request(f"/test_data/{test_data_id}/run")
        if not test_data:
            return dict()
        test_data = cls._decode_test_data(test_data)
        for output in test_data["outputs"]:
            if "regs" in output and output["regs"]:
                output["regs"] = cls._decode_regs(output["regs"])
            if "cores" in output:
                for core in output["cores"]:
                    for field_data in core["field_data"]:
                        field_data["data"] = cls._decode_data(field_data["data"])
            if "pnr_outputs" in output:
                for pnr_output in output["pnr_outputs"]:
                    for field_data in pnr_output["field_data"]:
                        field_data["data"] = cls._decode_data(field_data["data"])
        fields = [field_data["field"] for core in test_data["outputs"][0]["cores"] for field_data in core["field_data"]]
        pnr_fields = [field_data["field"] for pnr_output in test_data["outputs"][0]["pnr_outputs"]
                      for field_data in pnr_output["field_data"]]
        test_data["fields"] = fields
        test_data["pnr_fields"] = pnr_fields
        test_data["stop_seg_string"] = ", ".join(test_data["stop_segments"]) if test_data["stop_segments"] else \
            "No Stop Segments"
        return test_data

    @classmethod
    def search_field(cls, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/fields/{field_name}")

    @classmethod
    def create_test_data(cls, header: dict) -> dict:
        return cls._common_request(f"/test_data", method="POST", json=header)

    @classmethod
    def rename_test_data(cls, test_data_id: str, header: dict):
        return cls._common_request(f"/test_data/{test_data_id}/rename", method="PATCH", json=header)

    @classmethod
    def copy_test_data(cls, test_data_id: str):
        return cls._common_request(f"/test_data/{test_data_id}/copy", method="POST")

    @classmethod
    def delete_test_data(cls, test_data_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}", method="DELETE")

    @classmethod
    def add_output_field(cls, test_data_id: str, macro_name: str, field_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/cores/{macro_name}/fields",
                                   method="PATCH", json=field_dict)

    @classmethod
    def delete_output_field(cls, test_data_id: str, macro_name: str, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/test_data/{test_data_id}/output/cores/{macro_name}/fields/{field_name}",
                                   method="DELETE")

    @classmethod
    def add_output_regs(cls, test_data_id: str, reg_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/regs", method="PATCH", json=reg_dict)

    @classmethod
    def add_input_field(cls, test_data_id: str, macro_name: str, field_data: dict) -> dict:
        field_data["data"] = b64encode(bytes.fromhex(field_data["data"])).decode()
        return cls._common_request(f"/test_data/{test_data_id}/input/cores/{macro_name}/fields",
                                   method="PATCH", json=field_data)

    @classmethod
    def delete_input_field(cls, test_data_id: str, macro_name: str, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/test_data/{test_data_id}/input/cores/{macro_name}/fields/{field_name}",
                                   method="DELETE")

    @classmethod
    def add_input_heap(cls, test_data_id: str, body: dict) -> dict:
        body["hex_data"] = b64encode(bytes.fromhex(body["hex_data"])).decode()
        return cls._common_request(f"/test_data/{test_data_id}/input/heap", method="PATCH", json=body)

    @classmethod
    def delete_input_heap(cls, test_data_id: str, heap_name: str, variation: int) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/heap/{heap_name}/variations/{variation}",
                                   method="DELETE")

    @classmethod
    def add_input_regs(cls, test_data_id: str, reg_dict: dict) -> dict:
        reg_dict["value"] = int(reg_dict["value"], 16)
        if reg_dict["value"] > 0x7FFFFFFF:
            reg_dict["value"] -= Config.REG_MAX + 1
        return cls._common_request(f"/test_data/{test_data_id}/input/regs", method="PATCH", json=reg_dict)

    @classmethod
    def delete_input_regs(cls, test_data_id: str, reg: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/regs/{reg}", method="DELETE")

    @classmethod
    def create_pnr(cls, test_data_id: str, pnr_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr", method="PATCH", json=pnr_dict)

    @classmethod
    def add_output_pnr(cls, test_data_id: str, pnr_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/pnr", method="PATCH", json=pnr_dict)

    @classmethod
    def delete_output_pnr(cls, test_data_id: str, pnr_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/pnr/{pnr_id}", method="DELETE")

    @classmethod
    def add_pnr_fields(cls, test_data_id: str, pnr_id: str, core_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr/{pnr_id}/fields",
                                   method="PATCH", json=core_dict)

    @classmethod
    def delete_pnr(cls, test_data_id: str, pnr_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr/{pnr_id}", method="DELETE")

    @classmethod
    def add_tpfdf_lrec(cls, test_data_id: str, tpfdf: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/tpfdf", method="PATCH", json=tpfdf)

    @classmethod
    def delete_tpfdf_lrec(cls, test_data_id: str, df_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/tpfdf/{df_id}", method="DELETE")

    @classmethod
    def add_fixed_file(cls, test_data_id: str, fixed_file: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/fixed_files", method="PATCH", json=fixed_file)

    @classmethod
    def delete_fixed_file(cls, test_data_id: str, file_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/fixed_files/{file_id}", method="DELETE")

    @classmethod
    def add_debug(cls, test_data_id: str, debug: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/debug", method="PATCH", json=debug)

    @classmethod
    def delete_debug(cls, test_data_id: str, seg_name: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/debug/{seg_name}", method="DELETE")

    @classmethod
    def get_variations(cls, test_data_id: str, variation_type: str) -> List[dict]:
        response = cls._common_request(f"/test_data/{test_data_id}/variations", params={"type": variation_type})
        return response["variations"] if response else list()
