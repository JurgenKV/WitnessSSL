import argparse
import sys
import time
import logging
import os
from pathlib import Path

import certificate
from domains import get_domains
from log import setup_logging
from certificate import get_certificate_info
from utils import get_all_certs

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Проверка SSL-сертификатов по CRL")
    parser.add_argument('domains', nargs='*', help='Список доменов для проверки')
    parser.add_argument('--file', '-f', help='Файл со списком доменов (по одному на строку)')
    parser.add_argument('--interval', '-i', type=int, default=0,
                        help='Интервал проверки в секундах (0 – однократная проверка)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Подробный вывод')
    args = parser.parse_args()

    # Настройка логирования
    setup_logging(args.verbose)
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Собираем список доменов
    domains = []
    domains = get_domains(args)

    if not domains:
        logger.error("Не указаны домены для проверки.")
        sys.exit(1)

    # Удаляем возможные дубликаты и пустые строки
    domains = list(set([d.strip() for d in domains if d.strip()]))
    logger.info(f"Домены для проверки: {', '.join(domains)}")
    cert_list = []
    def run_check():
        for domain in domains:
            cert_list.append(get_certificate_info(domain))
        get_all_certs(cert_list)
        certificate.save_certificates_to_file(cert_list, Path(__file__).parent / 'cert.txt')

    if args.interval > 0:
        logger.info(f"Запуск периодической проверки каждые {args.interval} секунд.")
        while True:
            run_check()
            logger.info(f"Ожидание {args.interval} секунд до следующей проверки...")
            time.sleep(args.interval)
    else:
        run_check()

if __name__ == '__main__':
    main()