import asyncio
from typing import Literal

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from loguru import logger

from core.base import ModuleBase
from contracts.base import TokenBase
from modules.liquidswap.config import POOLS_INFO
from utils.math import get_coins_out_with_fees_stable, d, get_coins_out_with_fees


class LiquidSwapSwap(ModuleBase):
    def __init__(
            self,
            account: Account,
            coin_x: TokenBase,
            coin_y: TokenBase,
            proxies: dict = None
    ):
        super().__init__(
            account=account,
            coin_x=coin_x,
            coin_y=coin_y,
            proxies=proxies
        )

        self.account = account

        self.router_address = None
        self.resource_data = None
        self.pool_type = None

    async def get_token_pair_reserve(
            self,
            pool_type: str,
            resource_address: AccountAddress,
            router_address: AccountAddress
    ) -> dict | None:
        res_payload = f"{router_address}::liquidity_pool::LiquidityPool" \
                      f"<{self.coin_x.contract_address}, {self.coin_y.contract_address}, " \
                      f"{router_address}::curves::{pool_type}>"

        resource_data = await self.get_token_reserve(
            resource_address=resource_address,
            payload=res_payload
        )

        if resource_data is not None:
            self.resource_data = resource_data

            reserve_x = resource_data["data"]["coin_x_reserve"]["value"]
            reserve_y = resource_data["data"]["coin_y_reserve"]["value"]

            return {
                self.coin_x.contract_address: reserve_x,
                self.coin_y.contract_address: reserve_y
            }

        else:

            res_payload = f"{router_address}::liquidity_pool::LiquidityPool" \
                          f"<{self.coin_y.contract_address}, {self.coin_x.contract_address}, " \
                          f"{router_address}::curves::{pool_type}>"

            reversed_data = await self.get_token_reserve(
                resource_address=resource_address,
                payload=res_payload
            )
            if reversed_data is None:
                logger.error(f"Error getting token pair reserve (reverse), {pool_type} pool")
                return None

            self.resource_data = reversed_data
            reserve_x = reversed_data["data"]["coin_x_reserve"]["value"]
            reserve_y = reversed_data["data"]["coin_y_reserve"]["value"]

            return {
                self.coin_x.contract_address: reserve_y,
                self.coin_y.contract_address: reserve_x
            }

    async def get_amount_in(
            self,
            pool_type: Literal['Stable', 'Uncorrelated'],
            resource_address: AccountAddress,
            router_address: AccountAddress,
            amount_out: int,
            coin_x_address: str,
            coin_y_address: str,
            coin_x_decimals: int,
            coin_y_decimals: int
    ) -> int | None:
        tokens_reserve: dict = await self.get_token_pair_reserve(
            pool_type=pool_type,
            resource_address=resource_address,
            router_address=router_address
        )
        logger.debug('resource_data: {}', self.resource_data)
        if tokens_reserve is None:
            return None

        reserve_x = int(tokens_reserve[coin_x_address])
        reserve_y = int(tokens_reserve[coin_y_address])

        if reserve_x is None or reserve_y is None:
            return None

        pool_fee = int(self.resource_data["data"]["fee"])

        match pool_type:
            case 'Stable':
                amount_in = int(get_coins_out_with_fees_stable(
                    coin_in=d(amount_out),
                    reserve_in=d(reserve_x),
                    reserve_out=d(reserve_y),
                    scale_in=d(pow(10, coin_x_decimals)),
                    scale_out=d(pow(10, coin_y_decimals)),
                    fee=d(pool_fee)
                ))
            case 'Uncorrelated':
                amount_in = int(get_coins_out_with_fees(
                    coin_in_val=d(amount_out),
                    reserve_in=d(reserve_x),
                    reserve_out=d(reserve_y),
                    fee=d(pool_fee)
                ))
            case _:
                amount_in = None

        return amount_in

    async def get_most_profitable_amount_in_and_set_pool_type(
            self,
            amount_out: int,
            coin_x_address: str,
            coin_y_address: str,
            coin_x_decimals: int,
            coin_y_decimals: int
    ):
        pool_data = {}
        tasks = []

        for pool_version, pool_info in POOLS_INFO.items():
            for pool_type in pool_info['types']:
                resource_address = pool_info['resource_address']
                router_address = pool_info['router_address']
                task = asyncio.create_task(
                    self.get_amount_in(
                        pool_type=pool_type,
                        resource_address=resource_address,
                        router_address=router_address,
                        amount_out=amount_out,
                        coin_x_address=coin_x_address,
                        coin_y_address=coin_y_address,
                        coin_x_decimals=coin_x_decimals,
                        coin_y_decimals=coin_y_decimals
                    )
                )
                tasks.append((pool_version, pool_type, task))

        for pool_version, pool_type, task in tasks:
            amount_in = await task
            logger.debug(f'pool_version: {pool_version} pool_type: {pool_type} amount_in: {amount_in}')
            if amount_in is not None:
                pool_data[(pool_version, pool_type)] = amount_in

        logger.debug('pool_data: {}', pool_data)
        most_profitable_pool = max(pool_data, key=pool_data.get)
        logger.debug('most_profitable_pool: {}', most_profitable_pool)
        most_profitable_amount_in = pool_data[most_profitable_pool]

        pool_version, self.pool_type = most_profitable_pool
        self.router_address = POOLS_INFO[pool_version]['router_address']

        return most_profitable_amount_in
