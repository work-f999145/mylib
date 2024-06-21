import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path
from tqdm import tqdm

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
        if hasattr(record, 'data'):
            log_record['data'] = record.data
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False, indent=4)

class TqdmStream:
    @staticmethod
    def write(msg):
        if msg.strip():  # избегаем пустых строк
            tqdm.write(msg.rstrip())

    @staticmethod
    def flush():
        pass  # метод flush не нужен, но он должен быть определен

def setup_logger(name, log_file_name, file_level=logging.DEBUG, console_level=logging.INFO, tqdm_ex=False, extra_data=None):
    # Конфигурация логирования
    log_dir = Path("logs")
    log_file = log_dir.joinpath(f"{log_file_name}.json")

    # Создание директории для логов, если она не существует
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.hasHandlers():
        # file_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10**8, backupCount=5)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(file_level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
        
        if tqdm_ex:
            console_handler = logging.StreamHandler(stream=TqdmStream)
        else:
            console_handler = logging.StreamHandler()
        # console_handler = logging.StreamHandler(stream=TqdmStream)
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
