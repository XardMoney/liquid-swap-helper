import asyncio
import random

from aptos_sdk.account import Account
from loguru import logger

from core.config import TOKENS_INFO
from core.contracts import TokenBase
from modules.liquidswap.swap import LiquidSwapSwap
from settings import (
    SLEEP_RANGE_BETWEEN_ACCOUNTS, TOKENS_SWAP_INPUT, TOKENS_SWAP_OUTPUT, REVERSE_SWAP, SLEEP_RANGE_BETWEEN_REVERSE_SWAP
)
from utils.file import append_line


class Worker:
    # TODO здесь необходимо сделать запуск модулей из сгенерированых последовательностей
    def __init__(self, semaphore, account: Account, proxy: str | None = None):
        self.semaphore = semaphore
        self.account = account
        self.proxies = {
            'http://': proxy,
            'https://': proxy
        } if proxy else None

    async def swap(self):
        coin_x_symbol = random.choice(TOKENS_SWAP_INPUT)
        coin_y_symbol = random.choice(TOKENS_SWAP_OUTPUT)
        coin_x = TokenBase(coin_x_symbol, TOKENS_INFO[coin_x_symbol])
        coin_y = TokenBase(coin_y_symbol, TOKENS_INFO[coin_y_symbol])

        module = LiquidSwapSwap(self.account, coin_x, coin_y, proxies=self.proxies)
        await module.async_init()

        txn_hash = await module.send_txn()
        if not txn_hash:
            return False
        logger.success('Swap successfully! txn hash: {}', txn_hash)

        if REVERSE_SWAP:
            sleep_time = random.randint(*SLEEP_RANGE_BETWEEN_REVERSE_SWAP)
            logger.info('sleeping: {} second', sleep_time)
            await asyncio.sleep(sleep_time)

            reverse_module = LiquidSwapSwap(self.account, coin_y, coin_x, proxies=self.proxies)
            await reverse_module.async_init()

            txn_hash = await reverse_module.send_txn()
            if not txn_hash:
                return False
            logger.success('Swap successfully! txn hash: {}', txn_hash)

        return True

    async def start_work(self, sleep_needed):
        async with self.semaphore:
            if sleep_needed:
                sleep_time = random.randint(*SLEEP_RANGE_BETWEEN_ACCOUNTS)
                logger.info('sleeping: {} second', sleep_time)
                await asyncio.sleep(sleep_time)

            result = await self.swap()

            if result:
                await append_line(str(self.account.private_key), "files/succeeded_wallets.txt")
                return True

            await append_line(str(self.account.private_key), "files/failed_wallets.txt")
            return False
