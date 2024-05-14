import functools
import random
from asyncio import sleep
from loguru import logger

import settings


def tx_retry(attempts, exceptions=(Exception,)):
    def decorator_retry(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    logger.info(f"Attempt {attempt}/{attempts} successfully!")
                    return result
                except exceptions as e:
                    logger.error(f"Attempt {attempt}/{attempts} failed: {e}")
                    sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ATTEMPT)
                    logger.info(f'Sleep until next attempt: {sleep_time} second.')
                    await sleep(sleep_time)
            return None
        return wrapper
    return decorator_retry


class RetryDecorator:
    def __init__(self, attempts, exceptions=(Exception,)):
        self.attempts = attempts
        self.exceptions = exceptions

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            async def wrapper(*args, **kwargs):
                for attempt in range(1, self.attempts + 1):
                    try:
                        result = await self.func(instance, *args, **kwargs)
                        instance.logger_msg(f"Attempt {attempt}/{self.attempts} successfully!", 'success')
                        return result
                    except self.exceptions as e:
                        instance.logger_msg(f"Attempt {attempt}/{self.attempts} failed: {e}", 'error')
                        sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ATTEMPT)
                        instance.logger_msg(f'Sleep until next attempt: {sleep_time} second.')
                        await sleep(sleep_time)
                return None

            return wrapper
