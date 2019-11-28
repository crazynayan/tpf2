import os
from base64 import b64encode


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or b64encode(os.urandom(24)).decode()
    SERVER_URL = os.environ.get('SERVER_URL') or 'http://172.17.56.225:8000/'
    SERVER_USER_ID = 'nayan'
    REG_BITS: int = 32
    REG_MAX: int = (1 << REG_BITS) - 1  # 0xFFFFFFFF
    REGISTERS: tuple = ('R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14',
                        'R15')
    DEFAULT_MACROS: tuple = ('WA0AA', 'EB0EB', 'GLOBAL', 'MI0MI')
    PNR_KEYS = [
        ('name', 'NAME'),
        ('hfax', 'HFAX'),
        ('fqtv', 'FQTV'),
        ('itin', 'ITIN'),
        ('subs_card_seg', 'SUBS_CARD_SEG'),
        ('group_plan', 'GROUP_PLAN'),
    ]
