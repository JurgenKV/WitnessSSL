import logging
from datetime import datetime
from typing import List
from models import Certificate

logger = logging.getLogger(__name__)

def get_all_certs(certificates: List[Certificate]):
     for cert in certificates:
         logger.info("---")
         logger.info(f"ИМЯ СЕРТИФИКАТА: {cert.cert_name}")
         logger.info(f"ДОМЕН: {cert.domain}")
         logger.info(f"ЦЕНТР СЕРТИФИКАЦИИ: {cert.c_authority}")
         logger.info(f"СЕРИЙНЫЙ НОМЕР: {cert.serial_number}")
         logger.info(f"СТАТУС ОТЗЫВА: {cert.revoke_status}")
         logger.info(f"ДАТА СОЗДАНИЯ СЕРТИФИКАТА: {cert.cert_create_date}")
         logger.info(f"ДАТА ОКОНЧАНИЯ СЕРТИФИКАТА: {cert.cert_end_date}")
         logger.info(f"ДНЕЙ ДО ОКОНЧАНИЯ СЕРТИФИКАТА: {cert.days_until_end}")
         logger.info(f"CRL: {cert.crl}")
         logger.info(f"CRL LAST UPDATE: {cert.crl_last_update}")
         logger.info(f"CRL NEXT UPDATE: {cert.crl_next_update}")
         logger.info(f"OBJ CREATE DATE: {cert.obj_create_date}")

def get_all_certs_by_format(certificates: List[Certificate]):
    print("Формат - Домен/ Кем выдан / дата создания")
    for cert in certificates:
        #print("---")
        #print(f"ИМЯ СЕРТИФИКАТА: {cert.cert_name}")
        #print(f"ДОМЕН: {cert.domain}")
        #print(f"ЦЕНТР СЕРТИФИКАЦИИ: {cert.c_authority}")
        #print(f"СОЗДАНИЯ СЕРТИФИКАТА: {cert.cert_create_date}")
        #print(f"ОКОНЧАНИЯ СЕРТИФИКАТА: {cert.cert_end_date}")

        #print("---")
        #print(f"ИМЯ СЕРТИФИКАТА: {cert.cert_name}")
        date_str = str(cert.cert_create_date)  # "2026-07-16 13:00:00+00:00"
        dt = datetime.fromisoformat(date_str)
        formatted_date = dt.strftime('%d.%m.%Y')
        print(f"{cert.domain} /{cert.c_authority} /{formatted_date}")
        #print(f"ОКОНЧАНИЯ СЕРТИФИКАТА: {cert.cert_end_date}")

