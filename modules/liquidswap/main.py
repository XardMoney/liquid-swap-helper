import random

from aptos_sdk.account import Account
from loguru import logger

from contracts.base import TokenBase
from core.config import TOKENS_INFO
from modules.liquidswap.swap import LiquidSwapSwap
from settings import TOKENS_SWAP_INPUT, TOKENS_SWAP_OUTPUT


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
        logger.success('coin_x: {} initial balance: {}', coin_x.symbol, module.initial_balance_x_wei)

        # min_amount_out = module.initial_balance_x_wei * config.MIN_SWAP_PERCENT_BALANCE
        # max_amount_out = module.initial_balance_x_wei * config.MAX_SWAP_PERCENT_BALANCE
        # amount_out = round(random.uniform(min_amount_out, max_amount_out))
        # logger.info('amount_out {}', amount_out)
        #
        # amount_in = await module.get_most_profitable_amount_in_and_set_pool_type(
        #     amount_out,
        #     coin_x.contract_address,
        #     coin_y.contract_address,
        #     module.token_x_decimals,
        #     module.token_y_decimals,
        # )
        # logger.success(
        #     'amount_in: {}, selected pool: {}, router_address: {}', amount_in, module.pool_type, module.router_address
        # )


if __name__ == '__main__':
    pass
