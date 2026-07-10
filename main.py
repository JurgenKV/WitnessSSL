import argparse
import sys
import time
import logging
import os
import subprocess
import certificate

from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from crl import next_scheduled_time, get_next_crl_update
from domains import get_domains
from log import setup_logging
from certificate import get_certificate_info
from utils import get_all_certs

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Проверка SSL-сертификатов по CRL")
    parser.add_argument('domains', nargs='*', help='Список доменов для проверки')
    parser.add_argument('--file', '-f', help='Файл со списком доменов (по одному на строку)')
    #parser.add_argument('--interval', '-i', type=bool, default=True,
    #                    help='Интервал проверки в секундах (0 – однократная проверка)')
    parser.add_argument('--verbose', '-v', default='True' , help='Подробный вывод')
    args = parser.parse_args()

    setup_logging(args.verbose)
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    logger.info("СКРИПТ ЗАПУЩЕН.")

    domains = get_domains(args)
    if not domains:
        logger.error("Не указаны домены для проверки.")
        sys.exit(1)

    domains = list(set([d.strip() for d in domains if d.strip()]))
    logger.info(f"Домены для проверки: {', '.join(domains)}")

    run_check(domains)
    recheck_by_scheduler() # LINUX

    # if args.interval:
    #     logger.info("Запуск в режиме демона с учётом расписания и обновлений CRL.")
    #     while True:
    #         run_check(domains)
    #         now = datetime.now(timezone.utc)
    #         t0 = next_scheduled_time(0)
    #         t12 = next_scheduled_time(12)
    #         next_schedule = min(t0, t12)
    #         next_crl = get_next_crl_update()
    #         next_event = next_crl if (next_crl is not None and next_crl < next_schedule) else next_schedule
    #         wait_seconds = (next_event - now).total_seconds()
    #         if wait_seconds < 0:
    #             wait_seconds = 0
    #         logger.info(f"Ожидание {wait_seconds:.0f} секунд до следующего запуска ({next_event.strftime('%Y-%m-%d %H:%M:%S UTC')})")
    #         time.sleep(wait_seconds)
    # else:
    #     run_check(domains)


def run_check(domains):
    cert_list = []
    for domain in domains:
        cert_list.append(get_certificate_info(domain))
    certificate.save_certificates_to_file(cert_list, str(Path(__file__).resolve().parent / 'Json/certificate_date.json'))
    get_all_certs(cert_list)

######## ONLY LINUX ########
def recheck_by_scheduler():
    next_crl_updates = get_next_crl_update(5)
    schedule_crl_updates(next_crl_updates)

def schedule_crl_updates(dates: List[datetime], script_path = str(Path(__file__).resolve().parent)):
    remove_jobs_cmd = "for job in $(atq | awk '{print $1}'); do atrm $job; done"
    subprocess.run(remove_jobs_cmd, shell=True, check=False)

    for dt in dates:
        dt_str = dt.isoformat(timespec='seconds')  # Пример - "2026-09-08T07:54:00+00:00"
        at_time_cmd = f"date -d '{dt_str}' +'%H:%M %Y-%m-%d'"
        at_time = subprocess.check_output(at_time_cmd, shell=True, text=True).strip()
        job_cmd = f"sleep 1m && cd {script_path} && /usr/bin/python3 {script_path}/main.py"
        at_cmd = f"echo '{job_cmd}' | at {at_time}"

        logger.info(f"Планируем задание на {dt_str} -> at {at_time}")
        subprocess.run(at_cmd, shell=True, check=True)

    logger.info("Текущие задания at:")
    logger.info(subprocess.check_output("atq", shell=True, text=True))

######## ONLY LINUX ########
if __name__ == '__main__':
    main()