import logging
import os
from datetime import datetime

# Настройка логирования по умолчанию
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = logging.INFO


def setup_logging(verbose: bool = False, log_to_file: bool = True, log_dir: str = "Logs"):
    """
    Настройка логирования.

    :param verbose: если True, уровень DEBUG, иначе INFO.
    :param log_to_file: если True, создаётся папка log_dir и файл с логами за текущий день.
    :param log_dir: каталог для хранения файлов логов.
    :return: настроенный логгер.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOGGING_FORMAT)
    logger = logging.getLogger(__name__)

    if log_to_file:
        os.makedirs(log_dir, exist_ok=True)

        log_filename = datetime.now().strftime("%d-%m-%Y") + ".txt"
        log_path = os.path.join(log_dir, log_filename)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))

        logging.getLogger().addHandler(file_handler)

    return logger