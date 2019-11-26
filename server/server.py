from base64 import b64decode, b64encode
from typing import Dict, List
from urllib.parse import quote

import requests
from requests import Response

from client import tpf2_app


class Server:
    SERVER_URL = tpf2_app.config['SERVER_URL']

    def __init__(self):
        self.auth_header: Dict[str, str] = dict()

    def authenticate(self, email: str, password: str) -> bool:
        response: Response = requests.post(f"{self.SERVER_URL}/tokens", auth=(email, password))
        if response.status_code != 200:
            return False
        response_dict: dict = response.json()
        if 'token' not in response_dict:
            return False
        self.auth_header['Authorization'] = f"Bearer {response_dict['token']}"
        return True

    def segments(self) -> List[str]:
        response: Response = requests.get(f"{self.SERVER_URL}/segments", headers=self.auth_header)
        if response.status_code != 200:
            return list()
        return response.json()['segments']

    def macros(self) -> List[str]:
        response: Response = requests.get(f"{self.SERVER_URL}/macros", headers=self.auth_header)
        if response.status_code != 200:
            return list()
        return response.json()['macros']

    def instructions(self, seg_name: str) -> List[dict]:
        response = requests.get(f"{self.SERVER_URL}/segments/{seg_name}/instructions", headers=self.auth_header)
        if response.status_code != 200:
            return list()
        instructions = response.json()['instructions']
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

    def symbol_table(self, macro_name: str) -> List[dict]:
        response = requests.get(f"{self.SERVER_URL}/macros/{macro_name}/symbol_table", headers=self.auth_header)
        if response.status_code != 200:
            return list()
        return response.json()['symbol_table']

    def get_all_test_data(self) -> List[dict]:
        response = requests.get(f'{self.SERVER_URL}/test_data', headers=self.auth_header)
        if response.status_code != 200:
            return list()
        return response.json()

    def get_test_data(self, test_data_id: str) -> dict:
        response = requests.get(f'{self.SERVER_URL}/test_data/{test_data_id}', headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        test_data: dict = response.json()
        test_data['outputs'] = test_data['outputs'][0]
        test_data['id'] = test_data_id
        if 'regs' in test_data and test_data['regs']:
            test_data['regs'] = self._decode_regs(test_data['regs'])
        for core in test_data['cores']:
            for field_byte in core['field_bytes']:
                field_byte['data'] = self._decode_data(field_byte['data'])
        return test_data

    def get_test_data_by_name(self, name: str) -> dict:
        name = quote(name)
        response = requests.get(f'{self.SERVER_URL}/test_data', params={'name': name}, headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        return response.json()

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

    def run_test_data(self, test_data_id: str) -> dict:
        response = requests.get(f'{self.SERVER_URL}/test_data/{test_data_id}/run', headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        test_data = response.json()
        outputs = test_data['outputs']
        if 'regs' in outputs and outputs['regs']:
            test_data['outputs']['regs'] = self._decode_regs(outputs['regs'])
        if 'cores' in outputs and outputs['cores']:
            for core in outputs['cores']:
                for field_byte in core['field_bytes']:
                    field_byte['data'] = self._decode_data(field_byte['data'])
        return test_data

    def search_field(self, field_name: str) -> dict:
        field_name = quote(field_name)
        response = requests.get(f'{self.SERVER_URL}/fields/{field_name}', headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        return response.json()

    def create_test_data(self, test_data: dict) -> dict:
        if 'cores' in test_data:
            for core in test_data['cores']:
                for field_byte in core['field_bytes']:
                    field_byte['data'] = b64encode(bytes.fromhex(field_byte['data'][0])).decode()
        if 'regs' in test_data:
            test_data['regs'] = {reg: values[1] for reg, values in test_data['regs'].items()}
        response = requests.post(f'{self.SERVER_URL}/test_data', json=test_data, headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        return response.json()

    def delete_test_data(self, test_data_id: str) -> dict:
        response = requests.delete(f'{self.SERVER_URL}/test_data/{test_data_id}', headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        return response.json()


server = Server()
