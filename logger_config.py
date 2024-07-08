import logging
from pathlib import Path
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from mylib.my_func import _save_df_to_parquet
from contextlib import contextmanager

def json_encode(df_: pd.DataFrame):
    def my_json_encode(x):
        if isinstance(x, (tuple, list, dict)):
            return json.dumps(x, ensure_ascii=False)
        elif isinstance(x, (str, int, float)):
            return str(x)
        else:
            return 'null'
    
    for col in df_.select_dtypes('object').columns:
        df_[col] = df_[col].apply(my_json_encode).astype('string')
    
    return df_

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
            log_record['data_stream'] = str(self._convert_to_serializable(record.data_stream))
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

class CustomAdapter(logging.LoggerAdapter):
    def __init__(self, logger, extra, log_file):
        super().__init__(logger, extra)
        self.log_file = log_file
    
    def process(self, msg, kwargs):
        extra = self.extra.copy()
        if 'extra' in kwargs:
            extra.update(kwargs['extra'])
        kwargs['extra'] = extra
        return msg, kwargs
    
    def archive_log_file(self):
        logger = self.logger
        
        # Получаем путь к лог файлу
        log_file = self.log_file
        parquet_dir = log_file.parent
        
        # Закрываем все хендлеры логгера
        for handler in logger.handlers:
            handler.close()
            logger.removeHandler(handler)
        
        # Чтение лог файла и конвертация в DataFrame
        
        with open(log_file, 'r', encoding='utf-8') as file:
            log_tmp = file.read()
            df = (pd.json_normalize(json.loads(('['+log_tmp+']').replace('}\n{', '},\n{')))
                  .convert_dtypes()
                  .assign(timestamp=lambda x: pd.to_datetime(x['timestamp']))
                  .pipe(json_encode)
                  )
        
            # Сохранение DataFrame в Parquet
            _save_df_to_parquet(df, log_file.stem, parquet_dir)
            
            # Удаление оригинального лог файла
        log_file.unlink()

def setup_logger(name, log_file_name, file_level=logging.DEBUG, console_level=logging.INFO):
    # Конфигурация логирования
    log_dir = Path("logs")
    log_file = log_dir.joinpath(f"{log_file_name}.json")

    # Создание директории для логов, если она не существует
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    if not logger.hasHandlers():
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(file_level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s - %(data_stream)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return CustomAdapter(logger, {'data': None, 'data_stream': None}, log_file)






@contextmanager
def timeit(_logger: logging.LoggerAdapter, msg: str = '', level: str = 'INFO', _data: dict={}):
    start_time = datetime.now()
    yield
    elapsed_time = datetime.now() - start_time
    if isinstance(_data, dict):
        _data['msg'] = msg
        _data['timeit'] = elapsed_time
    else:
        _data = {'msg': msg, 'timeit': elapsed_time}
    if level == 'INFO':
        _logger.info(f'TimeIt', extra={'data': [_data], 'data_stream': f'{msg}: {elapsed_time}'})
    else:
        _logger.debug(f'TimeIt', extra={'data': [_data], 'data_stream': f'{msg}: {elapsed_time}'})