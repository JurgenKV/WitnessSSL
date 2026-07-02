import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse

import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.x509.oid import ExtensionOID

logger = logging.getLogger(__name__)

# Кеш для CRL: {url: (crl_object, next_update, fetch_time)}
CRL_CACHE = {}

def get_crl_distribution_points(cert: x509.Certificate) -> List[str]:
    """
    Извлекает URI точек распространения CRL из сертификата.
    """
    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.CRL_DISTRIBUTION_POINTS)
        points = ext.value
        uris = []
        for point in points:
            for name in point.full_name:
                if isinstance(name, x509.UniformResourceIdentifier):
                    uris.append(name.value)
        return uris
    except x509.ExtensionNotFound:
        return []

def fetch_crl(url: str) -> Optional[x509.CertificateRevocationList]:
    now = datetime.now(timezone.utc)  # вместо datetime.utcnow()
    if url in CRL_CACHE:
        crl_obj, next_update, fetch_time = CRL_CACHE[url]
        # Используем next_update_utc, если доступно, иначе fallback на next_update
        if next_update and now < next_update:
            logger.debug(f"Используем кеш CRL для {url}")
            return crl_obj
        if not next_update and (now - fetch_time) < timedelta(hours=1):
            logger.debug(f"Используем кеш CRL (без nextUpdate) для {url}")
            return crl_obj
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.content
        try:
            crl = x509.load_der_x509_crl(data, default_backend())
        except ValueError:
            crl = x509.load_pem_x509_crl(data, default_backend())

        # Предпочитаем next_update_utc, если доступно, иначе next_update
        if hasattr(crl, 'next_update_utc'):
            next_update = crl.next_update_utc
        else:
            next_update = crl.next_update  # для старых версий

        CRL_CACHE[url] = (crl, next_update, now)
        logger.debug(f"CRL загружен и закеширован: {url}")
        return crl
    except Exception as e:
        logger.error(f"Не удалось загрузить CRL {url}: {e}")
        return None

def is_certificate_revoked(cert: x509.Certificate, crl: x509.CertificateRevocationList) -> bool:
    """
    Проверяет, присутствует ли серийный номер сертификата в CRL.
    """
    serial = cert.serial_number
    for revoked_cert in crl:
        if revoked_cert.serial_number == serial:
            return True
    return False