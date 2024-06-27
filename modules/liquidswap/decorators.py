import functools
import random
from asyncio import sleep

import settings


def swap_retry(attempts, exceptions=(Exception,)):
    def decorator_retry(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    txn_hash = await func(self, *args,  **kwargs)
                    if kwargs.get('is_revesre'):
                        msg = f'Reverse swap transaction SUCCESS! '
                    else:
                        msg = f'Swap transaction SUCCESS! '

                    msg += f'Attempt {attempt}/{attempts} https://explorer.aptoslabs.com/txn/{txn_hash}'
                    self.logger_msg(msg, 'success')
                    return txn_hash
                except exceptions as e:
                    if kwargs.get('is_revesre'):
                        msg = f'Reverse swap transaction ERROR! '
                    else:
                        msg = f'Swap transaction ERROR! '

                    msg += f'Attempt {attempt}/{attempts}. Error: {e}'
                    self.logger_msg(msg, 'error')
                    sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ATTEMPT)
                    self.logger_msg(f'Sleep until next attempt: {sleep_time} second.')
                    await sleep(sleep_time)
            return None
        return wrapper
    return decorator_retry


def retry(attempts, exceptions=(Exception,)):
    def decorator_retry(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            func_name = func.__name__
            for attempt in range(1, attempts + 1):
                try:
                    res = await func(self, *args,  **kwargs)
                    msg = f'Function {func_name}: attempt {attempt}/{attempts} executed!'
                    self.logger_msg(msg, 'success')
                    return res
                except exceptions as e:
                    msg = f'Function {func_name}: attempt {attempt}/{attempts}. Error: {e}'
                    self.logger_msg(msg, 'error')
                    sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ATTEMPT)
                    self.logger_msg(f'Sleep until next attempt: {sleep_time} second.')
                    await sleep(sleep_time)
            return None
        return wrapper
    return decorator_retry
