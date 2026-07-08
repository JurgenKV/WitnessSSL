import logging
import requests

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from urllib.parse import urlparse
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
    logger.debug("Извлечение точек распространения CRL из сертификата")
    try:
        ext = cert.extensions.get_extension_for_oid(ExtensionOID.CRL_DISTRIBUTION_POINTS)
        points = ext.value
        uris = []
        for point in points:
            for name in point.full_name:
                if isinstance(name, x509.UniformResourceIdentifier):
                    uris.append(name.value)
        logger.debug(f"Найдено {len(uris)} точек CRL: {uris}")
        return uris
    except x509.ExtensionNotFound:
        logger.debug("Расширение CRL Distribution Points не найдено в сертификате")
        return []
    except Exception as e:
        logger.exception("Ошибка при извлечении точек распространения CRL")
        return []


def fetch_crl(url: str) -> Optional[x509.CertificateRevocationList]:
    """
    Загружает CRL по URL с кешированием.
    """
    now = datetime.now(timezone.utc)

    # Проверка кеша
    if url in CRL_CACHE:
        crl_obj, next_update, fetch_time = CRL_CACHE[url]
        # Используем next_update_utc, если доступно, иначе fallback на next_update
        if next_update and now < next_update:
            logger.debug(f"Используем кеш CRL для {url} (действителен до {next_update})")
            return crl_obj
        if not next_update and (now - fetch_time) < timedelta(hours=1):
            logger.debug(f"Используем кеш CRL (без nextUpdate) для {url}, загружен {fetch_time}")
            return crl_obj
        else:
            logger.debug(f"Кеш CRL для {url} устарел, выполняем загрузку")

    # Загрузка
    logger.info(f"Загрузка CRL из {url}")
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.content
        logger.debug(f"Получено {len(data)} байт от {url}")

        # Парсинг DER или PEM
        try:
            crl = x509.load_der_x509_crl(data, default_backend())
            logger.debug("CRL распарсен как DER")
        except ValueError:
            crl = x509.load_pem_x509_crl(data, default_backend())
            logger.debug("CRL распарсен как PEM")

        # Определяем дату следующего обновления
        if hasattr(crl, 'next_update_utc'):
            next_update = crl.next_update_utc
        else:
            next_update = crl.next_update  # для старых версий

        # Сохраняем в кеш
        CRL_CACHE[url] = (crl, next_update, now)
        logger.info(f"CRL успешно загружен и закэширован: {url}, следующее обновление: {next_update}")
        return crl

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка HTTP при загрузке CRL {url}: {e}")
        return None
    except ValueError as e:
        logger.error(f"Ошибка парсинга CRL {url} (неверный формат): {e}")
        return None
    except Exception as e:
        logger.exception(f"Неожиданная ошибка при загрузке CRL {url}")
        return None

def next_scheduled_time(hours: int) -> datetime:
    now = datetime.now(timezone.utc)
    candidate = now.replace(hour=hours, minute=0, second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate

def get_next_crl_update(count_of_dates: int = 5) -> List[datetime]:
    now = datetime.now(timezone.utc)
    future_updates = []

    logger.debug("Поиск ближайших обновлений CRL в кеше...")
    for url, (crl, next_update, fetch_time) in CRL_CACHE.items():
        if next_update is not None and next_update > now:
            future_updates.append(next_update)

    future_updates.sort()
    nearest_five = future_updates[:count_of_dates]

    if nearest_five:
        logger.info(
            f"Найдено {len(nearest_five)} ближайших обновлений CRL: "
            + ", ".join(d.strftime('%Y-%m-%d %H:%M:%S UTC') for d in nearest_five)
        )
    else:
        logger.info("Нет доступных CRL с будущим обновлением.")

    return nearest_five


def is_certificate_revoked(cert: x509.Certificate, crl: x509.CertificateRevocationList) -> bool:
    """
    Проверяет, присутствует ли серийный номер сертификата в CRL.
    """
    serial = cert.serial_number
    logger.debug(f"Проверка отзыва сертификата с серийным номером {serial} в CRL (содержит {len(list(crl))} записей)")
    try:
        for revoked_cert in crl:
            if revoked_cert.serial_number == serial:
                logger.debug(f"Серийный номер {serial} найден в CRL — сертификат отозван")
                return True
        logger.debug(f"Серийный номер {serial} не найден в CRL")
        return False
    except Exception as e:
        logger.exception("Ошибка при проверке отзыва в CRL")
        return False  # В случае ошибки считаем, что не отозван (или можно пробросить исключение, но оставим так)