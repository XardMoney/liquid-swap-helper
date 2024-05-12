import asyncio
import random
from typing import Literal

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.bcs import Serializer
from aptos_sdk.transactions import TransactionArgument, EntryFunction
from aptos_sdk.type_tag import TypeTag, StructTag
from loguru import logger

import settings
from core.base import ModuleBase
from core.config import NUMBER_OF_RETRIES
from core.contracts import TokenBase
from core.enums import ModuleExecutionStatus
from core.models import TransactionPayloadData
from modules.liquidswap.config import POOLS_INFO
from modules.liquidswap.decorators import tx_retry
from modules.liquidswap.exceptions import BuildTransactionError
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
        self.pool_version = None
        self.swap_address = None

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
            if amount_in is not None:
                pool_data[(pool_version, pool_type)] = amount_in

        most_profitable_pool = max(pool_data, key=pool_data.get)
        most_profitable_amount_in = pool_data[most_profitable_pool]

        self.pool_version, self.pool_type = most_profitable_pool
        self.router_address = POOLS_INFO[self.pool_version]['router_address']
        self.swap_address = POOLS_INFO[self.pool_version]['swap_address']
        logger.success(
            f'Pool version: {self.pool_version}\n'
            f'Pool type: {self.pool_type}\n'
            f'Router address: {self.router_address}\n'
            f'Swap function: {self.swap_address}'
        )

        return most_profitable_amount_in

    def calculate_amount_out_from_balance(
            self,
            coin_x: TokenBase,
    ) -> int | None:
        """
        Calculates amount out of token with decimals
        :param coin_x:
        :return:
        """
        initial_balance_x_decimals = self.initial_balance_x_wei / 10 ** self.token_x_decimals

        if self.initial_balance_x_wei == 0:
            logger.error(f"Wallet {coin_x.symbol.upper()} balance = 0")
            return None

        if initial_balance_x_decimals < settings.MIN_BALANCE:
            logger.error(
                f"Wallet {coin_x.symbol.upper()} balance less than min balance, "
                f"balance: {initial_balance_x_decimals}, min balance: {settings.MIN_BALANCE}"
            )
            return None

        if settings.AMOUNT_PERCENT:
            min_amount_out_percent, max_amount_out_percent = settings.AMOUNT_PERCENT
            percent = random.randint(int(min_amount_out_percent), int(max_amount_out_percent)) / 100
            amount_out_wei = int(self.initial_balance_x_wei * percent)
        elif settings.AMOUNT_QUANTITY:
            min_amount_out, max_amount_out = settings.AMOUNT_QUANTITY

            if initial_balance_x_decimals < min_amount_out:
                logger.error(
                    f"Wallet {coin_x.symbol.upper()} balance less than min amount out, "
                    f"balance: {initial_balance_x_decimals}, min amount out: {min_amount_out}"
                )
                return None

            if initial_balance_x_decimals < max_amount_out:
                max_amount_out = initial_balance_x_decimals

            amount_out_wei = self.get_random_amount_out_of_token(min_amount_out, max_amount_out, self.token_x_decimals)
        else:
            logger.error('AMOUNT_PERCENT and AMOUNT_QUANTITY is empty value!')
            return None

        return amount_out_wei

    async def build_transaction_payload(self) -> TransactionPayloadData | None:
        amount_out_wei = self.calculate_amount_out_from_balance(coin_x=self.coin_x)
        if amount_out_wei is None:
            return None

        amount_in_wei = await self.get_most_profitable_amount_in_and_set_pool_type(
            amount_out=amount_out_wei,
            coin_x_address=self.coin_x.contract_address,
            coin_y_address=self.coin_y.contract_address,
            coin_x_decimals=self.token_x_decimals,
            coin_y_decimals=self.token_y_decimals
        )

        if amount_in_wei is None:
            return None

        amount_out_decimals = amount_out_wei / 10 ** self.token_x_decimals
        amount_in_decimals = amount_in_wei / 10 ** self.token_y_decimals

        match self.pool_version:
            case "v0":
                payload = EntryFunction.natural(
                    f"{self.swap_address}::scripts_v2",
                    "swap",
                    [
                        TypeTag(StructTag.from_str(self.coin_x.contract_address)),
                        TypeTag(StructTag.from_str(self.coin_y.contract_address)),
                        TypeTag(StructTag.from_str(f"{self.router_address}::curves::{self.pool_type}"))
                    ],
                    [
                        TransactionArgument(int(amount_out_wei), Serializer.u64),
                        TransactionArgument(int(amount_in_wei), Serializer.u64)
                    ]
                )
            case "v0.5":
                payload = {
                    "function": f"{self.swap_address}::router::swap_coin_for_coin_x1",
                    "type_arguments": [
                        self.coin_x.contract_address,
                        self.coin_y.contract_address,
                        f"{self.router_address}::curves::{self.pool_type}"
                    ],
                    "arguments": [
                        str(amount_out_wei),
                        [
                            str(amount_in_wei)
                        ],
                        "0x05"
                    ],
                    "type": "entry_function_payload"
                }
            case _:
                return None

        return TransactionPayloadData(
            payload=payload,
            amount_x_decimals=amount_out_decimals,
            amount_y_decimals=amount_in_decimals
        )

    async def send_swap_type_txn(
            self,
            account: Account,
            txn_payload_data: TransactionPayloadData,
    ) -> str | None:
        """
        Sends swap type transaction, if reverse action is enabled in task, sends reverse swap type transaction
        :param account:
        :param txn_payload_data:
        :return:
        """

        is_registered = await self.is_token_registered_for_address(
            self.account.address(),
            self.coin_y.contract_address
        )
        if not is_registered:
            txn_hash = await self.register_coin_for_wallet(
                self.account,
                self.coin_y
            )
            logger.success('Register coin successfully! txn hash: {}', txn_hash)

        out_decimals = txn_payload_data.amount_x_decimals
        in_decimals = txn_payload_data.amount_y_decimals

        logger.warning(
            '{} ({}) -> {} ({}).', out_decimals, self.coin_x.symbol.upper(), in_decimals, self.coin_y.symbol.upper()
        )

        if isinstance(txn_payload_data.payload, EntryFunction):
            txn_hash = await self.simulate_and_send_transfer_type_transaction(
                account=account,
                txn_payload=txn_payload_data.payload,
                txn_info_message=""
            )
            return txn_hash

        elif isinstance(txn_payload_data.payload, dict):
            tx_hash = await self.client.submit_transaction(self.account, txn_payload_data.payload)
            txn_receipt = await self.wait_for_receipt(tx_hash)
            return self.check_txn_receipt(txn_receipt, tx_hash)

    @tx_retry(attempts=NUMBER_OF_RETRIES)
    async def send_txn(self) -> str | None:
        txn_payload_data = await self.build_transaction_payload()

        if txn_payload_data is None:
            msg = "Error while building transaction payload"
            raise BuildTransactionError(msg)

        txn_hash = await self.send_swap_type_txn(
            self.account,
            txn_payload_data,
        )

        return txn_hash
