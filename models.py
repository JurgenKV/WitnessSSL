import datetime
from typing import List
from cryptography.x509 import CertificateRevocationList

class Certificate:
    def __init__(self, name: str, domain: str, c_authority: str):
        self.name = name
        self.domain = domain
        self.c_authority = c_authority
        self.revoke_status = 2
        self.cert_create_date = None
        self.cert_end_date = None
        self.days_until_end = 0
        self.crl = "UNKNOWN"
        self.crl_last_update: List[datetime.datetime] = []
        self.crl_next_update: List[datetime.datetime] = []

    def set_crl(self, crl: str):
        self.crl = crl

    def set_cert_date(self, cert_create_date: datetime.datetime, cert_end_date: datetime.datetime, days_until_end: int):
        self.cert_create_date = cert_create_date
        self.cert_end_date = cert_end_date
        self.days_until_end = days_until_end

    def add_crl_date(self, crl: CertificateRevocationList):
        self.crl_last_update.append(crl.last_update_utc)
        self.crl_next_update.append(crl.next_update_utc)

# REVOKE_STATUS
# 0 - Не отозван. Все ок
# 1 - Отозван
# 2 - Объект создан. Не дошел до перезаписи
# 3 - Ошибка проверки при проверке сертификата\crl
# 4 - Ошибка. Не найдены точки распространения CRL