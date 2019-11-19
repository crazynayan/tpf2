import os
from base64 import b64encode


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or b64encode(os.urandom(24)).decode()
    SERVER_URL = 'https://tpf-server.crazyideas.co.in/'
