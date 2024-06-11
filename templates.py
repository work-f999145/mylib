import asyncio
import aiohttp
from typing import Optional, Any
from pydantic import BaseModel, ValidationError, Field, ConfigDict, HttpUrl, model_validator, field_validator
from typing import NamedTuple
import requests
from random import randint

class TaskTuple(NamedTuple):
    number: str
    community_id: int
    id: int
    page: int



class ValidationBaseModel(BaseModel):
    model_config = ConfigDict(
            # use_enum_values=True,  # используем значение из Enum
            # validate_assignment=True,  # включаем валидацию при изменении
            # extra='allow',
            extra='ignore',
        )

"""
Шаблоны запросов
"""

# -----------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------
# asyncio
async def fetch_data(task: TaskTuple, proxy: dict) -> tuple[dict|Exception, dict, str|dict|None]:
    input_data = {
                    'shop_number': task.number,
                    'community_id': task.community_id,
                    'category_id': task.id,
                    'page': task.page
                    }
    
    url = 'https://api.mobile.bristol.ru/api/v3/products'        
    headers = {
                'AnonToken': f'e6TD2C01MWSXCUUlMMqTrNG7NH1OXvhCu8HjISTNosfTv6hZGT8yWN6brpQDbR5MCEQAOV078PzXv4Mf9t{randint(0,9)}K8g==',
                'Origin': 'https://bristol.ru',
            }
    params = {
                'shop_number': task.number,
                'community_id': str(task.community_id),
                'category_id': str(task.id),
                'page': str(task.page),
                'consumer': 'website',
                'count': '24',
                'remnants_in_shop': 'В наличии',
            }
    proxy_str = f'http://{proxy['USER']}:{proxy['PASS']}@{proxy['IP']}:{proxy['PORT']}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url=url, headers=headers, params=params, proxy=proxy_str, timeout=10) as response:
                try:
                    data = await response.json()
                except Exception as e:
                    return (e, input_data, response.text(encoding='utf-8'))
                
                try:
                    return (ValidationBaseModel(**data), input_data, None)
                except ValidationError as e:
                    return (e, input_data, data)

    except Exception as e:
        return (e, input_data, 'get error')
    

# -----------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------

# Sychrone
def get_address(bottom_latitude, top_latitude, left_longitude, right_longitude, proxy: dict|None) -> tuple[dict|Exception, dict, str|dict|None]:
    
    url = 'https://193.232.108.94/api/cita/v1/stores/map'
    headers = {
                'Content-Type': 'application/json',
                'Host': '5d.5ka.ru'
            }
    params = {
            'bottom_latitude': str(bottom_latitude),
            'top_latitude': str(top_latitude),
            'left_longitude': str(left_longitude),
            'right_longitude': str(right_longitude),
            }

    proxy_str = f'http://{proxy['USER']}:{proxy['PASS']}@{proxy['IP']}:{proxy['PORT']}'
    input_data = params.copy()
    input_data['proxy'] = proxy

    res: requests.Response
    try:
        res = requests.get(url=url, headers=headers, params=params, proxy=proxy_str, timeout=10)
    except Exception as e:
        return (e, input_data, 'get error')
    try:
        data = res.json()
    except requests.exceptions.JSONDecodeError as e:
        return (e, input_data, res.text)
    try:
        return (ValidationBaseModel(**data), input_data, None)
    except ValidationError as e:
        return (e, input_data, data)
        
# -----------------------------------------------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------------------------------------------

