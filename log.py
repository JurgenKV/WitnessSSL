import logging

# Настройка логирования по умолчанию (может быть переопределена в main)
LOGGING_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = logging.INFO

def setup_logging(verbose: bool = False):
    #глобальный логгер
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOGGING_FORMAT)
    return logging.getLogger(__name__)


#add log files