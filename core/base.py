import random

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from loguru import logger

from contracts.base import TokenBase
from core.client import AptosCustomRestClient
from core.config import RPC_URLS


class ModuleBase:
    def __init__(
            self,
            coin_x: TokenBase,
            coin_y: TokenBase,
            account: Account,
            base_url: str = random.choice(RPC_URLS),
            proxies: dict = None
    ):

        self.base_url = base_url
        self.client = AptosCustomRestClient(base_url=base_url, proxies=proxies)
        self.account = account

        self.coin_x = coin_x
        self.coin_y = coin_y

    async def async_init(self):
        self.initial_balance_x_wei = await self.get_wallet_token_balance(
            wallet_address=self.account.address(),
            token_address=self.coin_x.contract_address
        )
        self.initial_balance_y_wei = await self.get_wallet_token_balance(
            wallet_address=self.account.address(),
            token_address=self.coin_y.contract_address
        )

        self.token_x_decimals = await self.get_token_decimals(token_obj=self.coin_x)
        self.token_y_decimals = await self.get_token_decimals(token_obj=self.coin_y)

    async def get_token_decimals(self, token_obj: TokenBase) -> int | None:
        """
        Gets token decimals
        :param token_obj:
        :return:
        """
        if token_obj.symbol == "aptos":
            return 8

        token_info = await self.get_token_info(token_obj=token_obj)
        if not token_info:
            return None

        return token_info["decimals"]

    async def get_wallet_token_balance(
            self,
            wallet_address: AccountAddress,
            token_address: str,
    ) -> int:
        """
        Gets wallet token balance
        :param wallet_address:
        :param token_address:
        :return:
        """
        try:
            balance = await self.client.account_resource(
                wallet_address,
                f"0x1::coin::CoinStore<{token_address}>",
            )
            logger.debug(balance)
            return int(balance["data"]["coin"]["value"])

        except Exception as e:
            logger.error(e)
            return 0

    async def get_token_reserve(
            self,
            resource_address: AccountAddress,
            payload: str
    ) -> dict | None:
        """
        Gets token reserve
        :param resource_address:
        :param payload:
        :return:
        """
        try:
            data = await self.client.account_resource(
                resource_address,
                payload
            )
            return data

        except Exception as e:
            logger.error(e)
            return None

    async def get_token_info(self, token_obj: TokenBase) -> dict | None:
        """
        Gets token info
        :param token_obj:
        :return:
        """
        if token_obj.symbol == "aptos":
            return None

        coin_address = AccountAddress.from_str(token_obj.address)

        try:
            token_info = await self.client.account_resource(
                coin_address,
                f"0x1::coin::CoinInfo<{token_obj.contract_address}>",
            )
            return token_info["data"]

        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
