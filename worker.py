import asyncio
import random
from itertools import cycle

from aptos_sdk.account import Account

from core.config import TOKENS_INFO
from modules.liquidswap.swap import LiquidSwapSwap
import settings
from utils.file import append_line, clear_file, read_lines
from utils.log import Logger


class Worker(Logger):
    # TODO здесь необходимо сделать запуск модулей из сгенерированых последовательностей
    def __init__(self, semaphore):
        Logger.__init__(self)
        self.semaphore = semaphore

    def check_settings(self):
        if not settings.AMOUNT_PERCENT and not settings.AMOUNT_QUANTITY:
            self.logger_msg('AMOUNT_PERCENT and AMOUNT_QUANTITY cannot be an empty value', 'critical')
            return False

        for token in settings.TOKENS_SWAP_INPUT:
            if not TOKENS_INFO.get(token):
                self.logger_msg(f'input token: {token} unavailable for swap', 'critical')
                return False

        for token in settings.TOKENS_SWAP_OUTPUT:
            if not TOKENS_INFO.get(token):
                self.logger_msg(f'output token: {token} unavailable to swap', 'critical')
                return False

        return True

    async def start(self):
        await clear_file("files/succeeded_wallets.txt")
        await clear_file("files/failed_wallets.txt")
        if settings.USE_PROXY:
            proxies = list(dict.fromkeys(await read_lines("files/proxies.txt")))

            if len(proxies) == 0:
                self.logger_msg("Proxy usage is enabled, but the file with them is empty", "critical")
                return
        else:
            self.logger_msg("Working without proxies")
            proxies = [None]

        private_keys = list(dict.fromkeys(await read_lines("files/private_keys.txt")))
        accounts = list(zip(proxies if settings.STRICT_PROXY else cycle(proxies), private_keys))

        if settings.SHUFFLE_ACCOUNTS:
            random.shuffle(accounts)

        if not self.check_settings():
            return

        tasks = []
        for i, (proxy, private_key) in enumerate(accounts):
            account = Account.load_key(private_key)
            tasks.append(
                asyncio.create_task(
                    self.execute(account, proxy, sleep_needed=False if i < settings.SEMAPHORE_LIMIT else True)
                )
            )

        res = await asyncio.gather(*tasks)
        self.logger_msg(
            f'Wallets: {len(res)} Succeeded: {len([x for x in res if x])} Failed: {len([x for x in res if not x])}'
        )

    async def execute(self, account: Account, proxy: str, sleep_needed: bool = False):
        async with self.semaphore:
            if sleep_needed:
                sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ACCOUNTS)
                self.logger_msg(f'sleeping: {sleep_time} second')
                await asyncio.sleep(sleep_time)

            # TODO сделать универсальное получение модулей и методов
            module = LiquidSwapSwap(account, proxy)
            result = await module.full_swap()

            if result:
                await append_line(str(account.private_key), "files/succeeded_wallets.txt")
                return True

            await append_line(str(account.private_key), "files/failed_wallets.txt")
            return False
