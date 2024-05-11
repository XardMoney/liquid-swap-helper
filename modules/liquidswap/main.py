import asyncio
import random

from aptos_sdk.account import Account
from loguru import logger

from core.contracts import TokenBase
from core.config import TOKENS_INFO
from modules.liquidswap.swap import LiquidSwapSwap
from settings import TOKENS_SWAP_INPUT, TOKENS_SWAP_OUTPUT, REVERSE_SWAP, SLEEP_RANGE_BETWEEN_REVERSE_SWAP


class LiquidSwapModule:
    def __init__(
            self,
            account: Account,
            proxies: dict = None
    ):
        self.account = account
        self.proxies = proxies

    async def swap(self):
        coin_x_symbol = random.choice(TOKENS_SWAP_INPUT)
        coin_y_symbol = random.choice(TOKENS_SWAP_OUTPUT)
        coin_x = TokenBase(coin_x_symbol, TOKENS_INFO[coin_x_symbol])
        coin_y = TokenBase(coin_y_symbol, TOKENS_INFO[coin_y_symbol])

        module = LiquidSwapSwap(self.account, coin_x, coin_y, proxies=self.proxies)
        await module.async_init()

        send_txn = await module.send_txn()
        logger.success('send_txn: {}', send_txn)
        if not send_txn:
            return False

        if REVERSE_SWAP:
            sleep_time = random.randint(*SLEEP_RANGE_BETWEEN_REVERSE_SWAP)
            logger.info('sleep: {} second', sleep_time)
            await asyncio.sleep(sleep_time)

            reverse_module = LiquidSwapSwap(self.account, coin_y, coin_x, proxies=self.proxies)
            await reverse_module.async_init()

            send_txn = await reverse_module.send_txn()
            logger.success('send_txn: {}', send_txn)
            if not send_txn:
                return False

        return True


if __name__ == '__main__':
    pass
