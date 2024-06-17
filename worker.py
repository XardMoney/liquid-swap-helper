import asyncio
import random

from aptos_sdk.account import Account

from core.config import TOKENS_INFO
from core.dataclasses import ExcelAccountData
from modules.liquidswap.swap import LiquidSwapSwap
import settings
from utils.file import append_line, clear_file
from utils.log import Logger
from utils.ms_office import get_data_from_excel


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
        accounts_data = get_data_from_excel(
            settings.EXCEL_FILE_PATH,
            settings.EXCEL_PAGE_NAME,
            ExcelAccountData,
            encrypted=settings.EXCEL_ENCRYPTED
        )

        if settings.SHUFFLE_ACCOUNTS:
            random.shuffle(accounts_data)

        if not self.check_settings():
            return

        tasks = []
        for i, account_data in enumerate(accounts_data):
            tasks.append(
                asyncio.create_task(
                    self.execute(account_data, sleep_needed=False if i < settings.SEMAPHORE_LIMIT else True)
                )
            )

        res = await asyncio.gather(*tasks)
        self.logger_msg(
            f'Wallets: {len(res)} Succeeded: {len([x for x in res if x])} Failed: {len([x for x in res if not x])}'
        )

    async def execute(self, account_data: type[ExcelAccountData], sleep_needed: bool = False):
        async with self.semaphore:
            if sleep_needed:
                sleep_time = random.randint(*settings.SLEEP_RANGE_BETWEEN_ACCOUNTS)
                self.logger_msg(f'sleeping: {sleep_time} second')
                await asyncio.sleep(sleep_time)

            account = Account.load_key(account_data.private_key)
            # TODO сделать универсальное получение модулей и методов
            module = LiquidSwapSwap(account, cex_address=account_data.cex_address, proxy=account_data.proxy)
            result = await module.full_swap()

            if result:
                await append_line(str(account_data.name), "files/succeeded_wallets.txt")
                return True

            await append_line(str(account_data.name), "files/failed_wallets.txt")
            return False
