import functools
import random
from asyncio import sleep
from loguru import logger

from settings import SLEEP_RANGE_BETWEEN_ACCOUNTS


def tx_retry(attempts, exceptions=(Exception,)):
    def decorator_retry(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    logger.info(f"Попытка {attempt}/{attempts} выполнена успешно.")
                    return result
                except exceptions as e:
                    logger.error(f"Попытка {attempt}/{attempts} не удалась: {e}")
                    sleep_time = random.randint(*SLEEP_RANGE_BETWEEN_ACCOUNTS)
                    logger.info('Сон до попытки следующей попытки: {}', sleep_time)
                    await sleep(sleep_time)
            return None
        return wrapper
    return decorator_retry
