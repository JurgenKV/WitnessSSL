import logging
import os
from datetime import datetime

# Настройка логирования по умолчанию
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = logging.INFO


def setup_logging(verbose: bool = False, log_to_file: bool = True, log_dir: str = "logs"):
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
        check_logs_count(log_dir, max_files=10)

        log_filename = datetime.now().strftime("%Y-%m-%d") + ".txt"
        log_path = os.path.join(log_dir, log_filename)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))

        logging.getLogger().addHandler(file_handler)

    return logger

def check_logs_count(log_dir: str = "logs", max_files: int = 10) -> None:
    if not os.path.exists(log_dir):
        return

    files = [
        f for f in os.listdir(log_dir)
        if os.path.isfile(os.path.join(log_dir, f)) and f.endswith(".txt")
    ]
    files.sort()

    while len(files) >= max_files:
        oldest = files.pop(0)
        file_path = os.path.join(log_dir, oldest)
        try:
            os.remove(file_path)
        except OSError as e:
            logging.warning(f"Не удалось удалить старый лог-файл {oldest}: {e}")