import logging
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

