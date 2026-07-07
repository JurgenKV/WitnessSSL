import logging
import re
from typing import List

logger = logging.getLogger(__name__)


def get_domains(args):
    # Файл при передаче параметров (названия файла) через консоль
    if args.file:
        domains = read_domains_from_file(args.file)
    elif args.domains:
        domains = args.domains
    else:
        # Константный файл.
        domains = read_domains_from_file("TEST_config.config")

    return domains

def read_domains_from_file(filename: str) -> List[str]:
    domains = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                match = re.search(r'^\s*server_name\s+(.+?);', line, re.IGNORECASE)
                if match:
                    names_str = match.group(1).strip()
                    names = [name.strip() for name in names_str.split() if name.strip()]
                    domains.extend(names)
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
    except Exception as e:
        logger.exception(f"Ошибка при чтении файла {filename}: {e}")
    if not domains:
        logger.warning(f"Не найдено ни одного server_name в файле {filename}.")
    return domains
