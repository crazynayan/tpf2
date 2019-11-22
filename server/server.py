from typing import Dict, List

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
        return test_data

    def run_test_data(self, test_data_id: str) -> dict:
        response = requests.get(f'{self.SERVER_URL}/test_data/{test_data_id}/run', headers=self.auth_header)
        if response.status_code != 200:
            return dict()
        test_data = response.json()
        outputs = test_data['outputs']
        if 'regs' in outputs and outputs['regs']:
            test_data['outputs']['regs'] = {reg: (value, f"{value & tpf2_app.config['REG_MAX']:08X}")
                                            for reg, value in outputs['regs'].items()}
        return test_data


server = Server()
