import datetime
import json
import os
import socket
import ssl
import logging

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import NameOID
from typing import List, Dict, Any

from crl import fetch_crl, get_crl_distribution_points, is_certificate_revoked
from models import Certificate
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_certificate_from_domain(domain: str, port: int = 443) -> x509.Certificate:
    """
    Получает сертификат с домена по TLS-соединению.
    """
    logger.debug(f"Начинаем получение сертификата для {domain}:{port}")
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with socket.create_connection((domain, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                der_cert = ssock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(der_cert, default_backend())
                logger.debug(f"Сертификат для {domain} успешно загружен, субъект: {cert.subject}")
                return cert
    except Exception as e:
        logger.exception(f"Ошибка при получении сертификата для {domain}:{port}")
        raise  # пробрасываем исключение дальше, чтобы обработать на уровне выше


def get_certificate_info(domain: str) -> Certificate:
    """
    Основная функция проверки сертификата домена.
    Возвращает объект Certificate с заполненными полями.
    """
    logger.info(f"Начало проверки сертификата для домена: {domain}")
    try:
        x509_cert = get_certificate_from_domain(domain)
        logger.debug(f"Получен X.509 сертификат для {domain}")

        crl_urls = get_crl_distribution_points(x509_cert)
        logger.debug(f"Для {domain} найдено {len(crl_urls)} точек распространения CRL")

        cert_info = extract_certificate_info(domain, x509_cert, crl_urls)

        if not cert_info.crl:
            logger.warning(f"Для {domain} не найдены точки распространения CRL. Пропускаем проверку отзыва.")
            cert_info.revoke_status = 4
            return cert_info

        # Проверяем по всем доступным CRL
        for url in cert_info.crl:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                logger.debug(f"Пропускаем CRL с неподдерживаемым протоколом: {url}")
                continue

            logger.debug(f"Загружаем CRL из {url}")
            crl = fetch_crl(url)

            if crl is None:
                logger.warning(f"Не удалось загрузить CRL из {url}, пропускаем")
                continue

            cert_info.add_crl_date(crl)
            logger.debug(f"CRL {url} загружен, дата обновления: {crl.last_update}")

            if is_certificate_revoked(x509_cert, crl):
                logger.info(f"Сертификат {domain} ОТОЗВАН (CRL: {url})")
                cert_info.revoke_status = 1
                return cert_info

        logger.info(f"Сертификат {domain} действителен (не найден в CRL)")
        cert_info.revoke_status = 0
        return cert_info

    except Exception as e:
        logger.exception(f"Критическая ошибка при проверке {domain}")
        return Certificate("ERROR", domain, "UNKNOWN", "0")


def extract_certificate_info(domain: str, x509_cert: x509.Certificate, crl_urls) -> Certificate:
    """
    Извлекает из x509-сертификата данные и возвращает объект Certificate.
    """
    logger.debug(f"Извлечение информации из сертификата для {domain}")

    # 1. Получаем Common Name из Subject
    subject = x509_cert.subject
    cn_attrs = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    name = cn_attrs[0].value if cn_attrs else domain
    logger.debug(f"Common Name: {name}")

    # 2. Даты
    cert_create_date = x509_cert.not_valid_before_utc
    cert_end_date = x509_cert.not_valid_after_utc
    logger.debug(f"Срок действия: с {cert_create_date} по {cert_end_date}")

    # 3. Кол-во дней до конца сертификата
    days_until_end = (cert_end_date - datetime.datetime.now(datetime.timezone.utc)).days
    logger.debug(f"Дней до истечения: {days_until_end}")

    # 4. Издатель (Issuer) – его CN
    issuer = x509_cert.issuer
    issuer_cn_attrs = issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    c_authority = issuer_cn_attrs[0].value if issuer_cn_attrs else ""
    logger.debug(f"Удостоверяющий центр: {c_authority}")

    # 5. CRL
    crl = crl_urls
    logger.debug(f"CRL URLs: {crl}")

    # 6. Серийный номер сертификата
    serial_number = x509_cert.serial_number

    # Создаём объект
    cert = Certificate(name, domain, c_authority, str(serial_number))
    cert.set_cert_date(cert_create_date, cert_end_date, days_until_end)
    cert.set_crl(crl)

    return cert


def certificate_to_dict(cert: Certificate) -> Dict[str, Any]:
    """
    Преобразует объект Certificate в словарь для JSON-сериализации.
    """
    try:
        return {
            "cert_name": cert.cert_name,
            "domain": cert.domain,
            "c_authority": cert.c_authority,
            "revoke_status": cert.revoke_status,
            "serial_number": cert.serial_number,
            "cert_create_date": int(cert.cert_create_date.timestamp()) if cert.cert_create_date else 0,
            "cert_end_date": int(cert.cert_end_date.timestamp()) if cert.cert_end_date else 0,
            "days_until_end": cert.days_until_end,
            "crl": cert.crl,
            "crl_last_update": int(cert.crl_last_update.timestamp()) if cert.crl_last_update else 0,
            "crl_next_update": int(cert.crl_next_update.timestamp()) if cert.crl_next_update else 0,
            "obj_create_date": int(cert.obj_create_date.timestamp()) if cert.obj_create_date else 0,
        }
    except Exception as e:
        logger.exception(f"Ошибка преобразования сертификата {cert.domain} в словарь")
        raise

def save_certificates_to_file(
        certificates: List[Certificate],
        file_path: str = "/var/lib/zabbix/certificates.json"
) -> bool:
    """
    Сохраняет список сертификатов в JSON-файл.
    """
    logger.info(f"Сохранение {len(certificates)} сертификатов в файл {file_path}")
    try:
        data_list = [certificate_to_dict(cert) for cert in certificates]
        json_payload = json.dumps(data_list, ensure_ascii=False, indent=2)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_payload)

        logger.info(f"JSON успешно сохранён в {file_path}")
        return True
    except Exception as e:
        logger.exception(f"Ошибка при сохранении файла {file_path}")
        return False