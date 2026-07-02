import datetime

class Certificate:
    name = "UNKNOWN"
    domain = "UNKNOWN"
    revoke_status = 2
    c_authority = "UNKNOWN"
    cert_create_date = datetime.date.today()
    cert_end_date = datetime.date.today()
    days_until_end = 0
    crl = "UNKNOWN"
    crl_last_update = datetime.date.today()
    crl_next_update = datetime.date.today()

    def __init__(self, name: str, domain: str, c_authority: str):
        self.name = name
        self.domain = domain
        self.c_authority = c_authority

    def set_crl(self, crl: str):
        self.crl = crl

    def set_cert_date(self, cert_create_date: datetime, cert_end_date: datetime, days_until_end: int):
        self.cert_create_date = cert_create_date
        self.cert_end_date = cert_end_date
        self.days_until_end = days_until_end

    def set_crl_date(self, crl_last_update: datetime, crl_next_update: datetime):
        self.crl_last_update = crl_last_update
        self.crl_next_update = crl_next_update

# REVOKE_STATUS
# 0 - Не отозван. Все ок
# 1 - Отозван
# 2 - Объект создан. Не дошел до перезаписи
# 3 - Ошибка проверки при проверке сертификата\crl
# 4 - Ошибка. Не найдены точки распространения CRL