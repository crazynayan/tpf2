import os
from base64 import b64encode


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or b64encode(os.urandom(24)).decode()
    SERVER_URL = 'http://172.17.56.225:8000/'
    REG_BITS: int = 32
    REG_MAX: int = (1 << REG_BITS) - 1  # 0xFFFFFFFF
