from base64 import b64decode, b64encode
from typing import Dict, List
from urllib.parse import quote

import requests
from flask_login import current_user
from requests import Response

from flask_app import tpf2_app


class Server:

    @staticmethod
    def _common_request(url: str, method: str = 'GET', **kwargs) -> dict:
        request_url = f"{tpf2_app.config['SERVER_URL']}{url}"
        if 'auth' not in kwargs:
            auth_header = {'Authorization': f"Bearer {current_user.token}"}
            kwargs['headers'] = auth_header
        if method == 'GET':
            response: Response = requests.get(request_url, **kwargs)
        elif method == 'POST':
            response: Response = requests.post(request_url, **kwargs)
        elif method == 'PATCH':
            response: Response = requests.patch(request_url, **kwargs)
        elif method == 'DELETE':
            response: Response = requests.delete(request_url, **kwargs)
        else:
            raise TypeError
        if response.status_code == 401 and current_user.is_authenticated:
            current_user.token = str()
            current_user.save()
        return response.json() if response.status_code == 200 else dict()

    @classmethod
    def authenticate(cls, email: str, password: str) -> str:
        response: dict = cls._common_request(f"/tokens", method='POST', auth=(email, password))
        return response['token'] if 'token' in response else str()

    @classmethod
    def segments(cls) -> List[str]:
        response: dict = cls._common_request(f"/segments")
        return response['segments'] if response else list()

    @classmethod
    def macros(cls) -> List[str]:
        response: dict = cls._common_request(f"/macros")
        return response['macros'] if response else list()

    @classmethod
    def instructions(cls, seg_name: str) -> List[dict]:
        response: dict = cls._common_request(f"/segments/{seg_name}/instructions")
        instructions = response['instructions'] if response else list()
        response_list: List[dict] = list()
        for instruction in instructions:
            ins_dict = dict()
            ins = instruction.split(':')
            ins_dict['index'] = ins[0]
            ins_dict['label'] = ins[1]
            ins_dict['command'] = ins[2]
            ins_dict['operands'] = ins[3] if len(ins) > 3 else str()
            response_list.append(ins_dict)
        return response_list

    @classmethod
    def symbol_table(cls, macro_name: str) -> List[dict]:
        response: dict = cls._common_request(f"/macros/{macro_name}/symbol_table")
        return response['symbol_table'] if response else list()

    @classmethod
    def get_all_test_data(cls) -> List[dict]:
        response = cls._common_request(f"/test_data")
        return response if response else list()

    @classmethod
    def get_test_data(cls, test_data_id: str) -> dict:
        test_data: dict = cls._common_request(f"/test_data/{test_data_id}")
        if not test_data:
            return dict()
        test_data['outputs'] = test_data['outputs'][0]
        if 'regs' in test_data and test_data['regs']:
            test_data['regs'] = cls._decode_regs(test_data['regs'])
        for core in test_data['cores']:
            for field_data in core['field_data']:
                field_data['data'] = cls._decode_data(field_data['data'])
        for pnr in test_data['pnr']:
            for field_data in pnr['field_data']:
                field_data['data'] = cls._decode_data(field_data['data'])
        for tpfdf in test_data['tpfdf']:
            for field_data in tpfdf['field_data']:
                field_data['data'] = cls._decode_data(field_data['data'])
        return test_data

    @classmethod
    def get_test_data_by_name(cls, name: str) -> dict:
        name = quote(name)
        return cls._common_request(f"/test_data", params={'name': name})

    @staticmethod
    def _decode_data(encoded_data) -> List[str]:
        data = b64decode(encoded_data)
        hex_data = data.hex().upper()
        number_data = 'NA'
        if len(hex_data) <= 8:
            number_data = int(hex_data, 16)
        if len(hex_data) == 4 and number_data > 0x7FFF:
            number_data -= 0x10000
        if len(hex_data) == 8 and number_data > 0x7FFFFFFF:
            number_data -= tpf2_app.config['REG_MAX'] + 1
        char_data = data.decode('cp037')
        return [hex_data, number_data, char_data]

    @staticmethod
    def _decode_regs(regs: Dict[str, int]) -> Dict[str, list]:
        return {reg: [f"{value & tpf2_app.config['REG_MAX']:08X}", value] for reg, value in regs.items()}

    @classmethod
    def run_test_data(cls, test_data_id: str) -> dict:
        test_data: dict = cls._common_request(f"/test_data/{test_data_id}/run")
        if not test_data:
            return dict()
        outputs = test_data['outputs']
        if 'regs' in outputs and outputs['regs']:
            test_data['outputs']['regs'] = cls._decode_regs(outputs['regs'])
        if 'cores' in outputs and outputs['cores']:
            for core in outputs['cores']:
                for field_data in core['field_data']:
                    field_data['data'] = cls._decode_data(field_data['data'])
        return test_data

    @classmethod
    def search_field(cls, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/fields/{field_name}")

    @classmethod
    def create_test_data(cls, header: dict) -> dict:
        return cls._common_request(f"/test_data", method='POST', json=header)

    @classmethod
    def rename_test_data(cls, test_data_id: str, header: dict):
        return cls._common_request(f"/test_data/{test_data_id}/rename", method='PATCH', json=header)

    @classmethod
    def copy_test_data(cls, test_data_id: str):
        return cls._common_request(f"/test_data/{test_data_id}/copy", method='POST')

    @classmethod
    def delete_test_data(cls, test_data_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}", method='DELETE')

    @classmethod
    def add_output_field(cls, test_data_id: str, macro_name: str, field_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/cores/{macro_name}/fields",
                                   method='PATCH', json=field_dict)

    @classmethod
    def delete_output_field(cls, test_data_id: str, macro_name: str, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/test_data/{test_data_id}/output/cores/{macro_name}/fields/{field_name}",
                                   method='DELETE')

    @classmethod
    def add_output_regs(cls, test_data_id: str, reg_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/output/regs", method='PATCH', json=reg_dict)

    @classmethod
    def add_input_field(cls, test_data_id: str, macro_name: str, field_data: dict) -> dict:
        field_data['data'] = b64encode(bytes.fromhex(field_data['data'])).decode()
        return cls._common_request(f"/test_data/{test_data_id}/input/cores/{macro_name}/fields",
                                   method='PATCH', json=field_data)

    @classmethod
    def delete_input_field(cls, test_data_id: str, macro_name: str, field_name: str) -> dict:
        field_name = quote(field_name)
        return cls._common_request(f"/test_data/{test_data_id}/input/cores/{macro_name}/fields/{field_name}",
                                   method='DELETE')

    @classmethod
    def add_input_regs(cls, test_data_id: str, reg_dict: dict) -> dict:
        reg_dict['value'] = int(reg_dict['value'], 16)
        if reg_dict['value'] > 0x7FFFFFFF:
            reg_dict['value'] -= tpf2_app.config['REG_MAX'] + 1
        return cls._common_request(f"/test_data/{test_data_id}/input/regs", method='PATCH', json=reg_dict)

    @classmethod
    def delete_input_regs(cls, test_data_id: str, reg: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/regs/{reg}", method='DELETE')

    @classmethod
    def create_pnr(cls, test_data_id: str, pnr_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr", method='PATCH', json=pnr_dict)

    @classmethod
    def add_pnr_fields(cls, test_data_id: str, pnr_id: str, core_dict: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr/{pnr_id}/fields",
                                   method='PATCH', json=core_dict)

    @classmethod
    def delete_pnr(cls, test_data_id: str, pnr_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/pnr/{pnr_id}", method='DELETE')

    @classmethod
    def add_tpfdf_lrec(cls, test_data_id: str, tpfdf: dict) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/tpfdf", method='PATCH', json=tpfdf)

    @classmethod
    def delete_tpfdf_lrec(cls, test_data_id: str, df_id: str) -> dict:
        return cls._common_request(f"/test_data/{test_data_id}/input/tpfdf/{df_id}", method='DELETE')
