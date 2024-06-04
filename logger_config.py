import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path


# Конфигурация логирования
log_dir = Path("logs")
log_file = log_dir.joinpath("app.json")

# Создание директории для логов, если она не существует
log_dir.mkdir(parents=True, exist_ok=True)


# Настройка логирования
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now().isoformat(),
            "name": record.name,
            "level": record.levelname,
            "function": record.funcName,
            "message": record.getMessage()
        }
        if hasattr(record, 'user_data'):
            log_record['user_data'] = record.user_data
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logger(name, file_level=logging.DEBUG, console_level=logging.INFO, extra_data=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.hasHandlers():
        file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10**8, backupCount=5)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    class CustomAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = self.extra.copy()
            if 'extra' in kwargs:
                extra.update(kwargs['extra'])
            kwargs['extra'] = extra
            return msg, kwargs

    return CustomAdapter(logger, extra_data or {})
