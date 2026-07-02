import datetime
import socket
import ssl
import logging

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography import x509
from cryptography.x509.oid import NameOID
from typing import Optional

from crl import fetch_crl, get_crl_distribution_points, is_certificate_revoked
from models import Certificate
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def get_certificate_from_domain(domain: str, port: int = 443) -> x509.Certificate:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((domain, port), timeout=10) as sock:
        with context.wrap_socket(sock, server_hostname=domain) as ssock:
            der_cert = ssock.getpeercert(binary_form=True)
            return x509.load_der_x509_certificate(der_cert, default_backend())

def get_certificate_info(domain: str) -> Certificate:
    try:
        logger.info(f"Проверка домена: {domain}")
        x509_cert = get_certificate_from_domain(domain)
        crl_urls = get_crl_distribution_points(x509_cert)
        cert_info = extract_certificate_info(domain, x509_cert, crl_urls)

        if not cert_info.crl:
            logger.warning(f"Для {domain} не найдены точки распространения CRL. Пропускаем.")
            cert_info.revoke_status = 4
            return cert_info

        # Проверяем по всем доступным CRL
        for url in cert_info.crl:
            parsed = urlparse(url)
            if parsed.scheme not in ('http', 'https'):
                continue  # только HTTP/HTTPS поддерживаем

            crl = fetch_crl(url)

            if crl is None:
                continue

            cert_info.add_crl_date(crl)

            if is_certificate_revoked(x509_cert, crl):
                logger.info(f"Сертификат {domain} ОТОЗВАН (CRL: {url})")
                cert_info.revoke_status = 1
                return cert_info

        logger.info(f"Сертификат {domain} действителен (не найден в CRL)")
        cert_info.revoke_status = 0
        return cert_info

    except Exception as e:
        logger.error(f"Ошибка при проверке {domain}: {e}")
        return Certificate("ERROR", domain, "UNKNOWN")


def extract_certificate_info(domain: str, x509_cert: x509.Certificate, crl_urls) -> Certificate:
    """
    Извлекает из x509-сертификата данные и возвращает объект Certificate.
    """
    # 1. Получаем Common Name из Subject
    subject = x509_cert.subject
    cn_attrs = subject.get_attributes_for_oid(NameOID.COMMON_NAME)
    name = cn_attrs[0].value if cn_attrs else domain  # если CN нет, используем домен

    # 2. Даты
    cert_create_date = x509_cert.not_valid_before_utc
    cert_end_date = x509_cert.not_valid_after_utc

    # 3. Кол-во дней до конца сертификата
    days_until_end = (cert_end_date - datetime.datetime.now(datetime.timezone.utc)).days

    # 4. Издатель (Issuer) – его CN
    issuer = x509_cert.issuer
    issuer_cn_attrs = issuer.get_attributes_for_oid(NameOID.COMMON_NAME)
    c_authority = issuer_cn_attrs[0].value if issuer_cn_attrs else ""

    # 5. CRL
    crl = crl_urls


    # Create object
    cert = Certificate(name, domain, c_authority=c_authority)
    cert.set_cert_date(cert_create_date, cert_end_date, days_until_end)
    cert.set_crl(crl)
    #cert.set_crl_date()

    return cert