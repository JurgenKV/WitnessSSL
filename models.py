import datetime
from datetime import timezone

from cryptography.x509 import CertificateRevocationList

class Certificate:
    def __init__(self, cert_name: str, domain: str, c_authority: str, serial_number: str):
        self.cert_name = cert_name
        self.domain = domain
        self.c_authority = c_authority
        self.serial_number = serial_number
        self.revoke_status = 2
        self.cert_create_date = None
        self.cert_end_date = None
        self.days_until_end = 0
        self.crl = "UNKNOWN"
        self.crl_last_update = None
        self.crl_next_update = None
        self.obj_create_date = datetime.datetime.now(timezone.utc)

    def set_crl(self, crl: str):
        self.crl = crl

    def set_cert_date(self, cert_create_date: datetime.datetime, cert_end_date: datetime.datetime, days_until_end: int):
        self.cert_create_date = cert_create_date
        self.cert_end_date = cert_end_date
        self.days_until_end = days_until_end

    def add_crl_date(self, crl: CertificateRevocationList):
        if self.crl_last_update is None:
            self.crl_last_update = crl.last_update_utc

        if self.crl_next_update is None:
            self.crl_next_update = crl.next_update_utc

        if self.crl_last_update.timestamp() > crl.last_update_utc.timestamp():
            self.crl_last_update = crl.last_update_utc

        if self.crl_next_update.timestamp() > crl.next_update_utc.timestamp():
            self.crl_next_update = crl.next_update_utc


# REVOKE_STATUS
# 0 - Не отозван. Все ок
# 1 - Отозван
# 2 - Объект создан. Не дошел до перезаписи
# 3 - Ошибка при проверке/получении сертификата
# 4 - Ошибка. Не найдены точки распространения CRL (crl пуст)
# 5 - Критическая ошибка при проверке домена
# 6 - Ошибка при проверке/получении CRL