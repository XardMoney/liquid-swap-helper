from aptos_sdk.account import Account
from core.config import SLEEP_RANGE, TOKENS_INFO
from modules.liquidswap.main import LiquidSwapModule
from utils.file import append_line, clear_file, read_lines
from settings import USE_PROXY, SHUFFLE_ACCOUNTS, STRICT_PROXY, SEMAPHORE_LIMIT, AMOUNT_PERCENT, AMOUNT_QUANTITY, \
    TOKENS_SWAP_OUTPUT, TOKENS_SWAP_INPUT
from itertools import cycle
from utils.log import log
import asyncio
import random


def check_settings():
    if not AMOUNT_PERCENT and not AMOUNT_QUANTITY:
        log.critical('AMOUNT_PERCENT and AMOUNT_QUANTITY cannot be an empty value')
        return False

    for token in TOKENS_SWAP_INPUT:
        if not TOKENS_INFO.get(token):
            log.critical('input token: {} unavailable for swap', token)
            return False

    for token in TOKENS_SWAP_OUTPUT:
        if not TOKENS_INFO.get(token):
            log.critical('output token: {} unavailable to swap', token)
            return False

    return True


class Worker:
    def __init__(self, semaphore, module: LiquidSwapModule):
        self.semaphore = semaphore
        self.module = module

    async def start_work(self, sleep_needed):
        async with self.semaphore:
            if sleep_needed:
                await asyncio.sleep(random.randint(*SLEEP_RANGE))

            result = await self.module.swap()

            if result:
                await append_line(str(self.module.account.private_key), "files/succeeded_wallets.txt")
                return True

            await append_line(str(self.module.account.private_key), "files/failed_wallets.txt")
            return False


async def main():
    await clear_file("files/succeeded_wallets.txt")
    await clear_file("files/failed_wallets.txt")
    if USE_PROXY:
        proxies = list(dict.fromkeys(await read_lines("files/proxies.txt")))

        if len(proxies) == 0:
            log.critical("Proxy usage is enabled, but the file with them is empty")
            return
    else:
        log.info("Working without proxies")
        proxies = [None]

    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    private_keys = list(dict.fromkeys(await read_lines("files/private_keys.txt")))
    accounts = list(zip(proxies if STRICT_PROXY else cycle(proxies), private_keys))

    if SHUFFLE_ACCOUNTS:
        random.shuffle(accounts)

    if not check_settings():
        return

    tasks = []
    for i, (proxy, private_key) in enumerate(accounts):
        account = Account.load_key(private_key)
        module = LiquidSwapModule(account, proxies={'http://': proxy})
        worker = Worker(semaphore, module)
        tasks.append(
            asyncio.create_task(
                worker.start_work(False if i < SEMAPHORE_LIMIT else True)
            )
        )

    res = await asyncio.gather(*tasks)
    log.info(f'Wallets: {len(res)} Succeeded: {len([x for x in res if x])} Failed: {len([x for x in res if not x])}')


if __name__ == "__main__":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    except Exception:
        pass

    asyncio.run(main())
