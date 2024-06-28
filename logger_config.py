import logging
import logging.handlers
import json
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np


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
            log_record['data'] = self._convert_to_serializable(record.data)
        if hasattr(record, 'data_stream'):
            log_record['data_stream'] = self._convert_to_serializable(record.data_stream)
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record, ensure_ascii=False, indent=4)

    def _convert_to_serializable(self, data):
        if isinstance(data, np.integer):
            return int(data)
        if isinstance(data, np.floating):
            return float(data)
        if isinstance(data, np.ndarray):
            return data.tolist()
        if isinstance(data, datetime):
            return data.isoformat()
        if isinstance(data, timedelta):
            return str(data)
        if isinstance(data, dict):
            return {key: self._convert_to_serializable(value) for key, value in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._convert_to_serializable(item) for item in data]
        return data


def setup_logger(name, log_file_name, file_level=logging.DEBUG, console_level=logging.INFO):
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
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s - %(data_stream)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    class CustomAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = self.extra.copy()
            if 'extra' in kwargs:
                extra.update(kwargs['extra'])
            kwargs['extra'] = extra
            return msg, kwargs

    return CustomAdapter(logger, {'data': None, 'data_stream': None})
