from typing import List
from models import Certificate

def get_all_certs(certificates: List[Certificate]):
     for cert in certificates:
        if cert.revoke_status == 0:
            print(f"{cert.domain}: \nИМЯ СЕРТА: {cert.cert_name}"
                  f"\nДНЕЙ ДО ОКОНЧАНИЯ: {cert.days_until_end}"
                  f"\nДЕЙСТВИТЕЛЕН ДО {cert.cert_end_date}"
                  f"\nCA:{cert.c_authority}\n")

        elif cert.revoke_status == 1:
            print(f"{cert.domain}: ОТОЗВАН\n")
        elif cert.revoke_status >= 2:
            print(f"{cert.domain}: ERROR\n")
