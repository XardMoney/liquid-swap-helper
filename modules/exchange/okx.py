import asyncio
from typing import Literal

import ccxt.async_support as ccxt
from ccxt import okx, PermissionDenied, RequestTimeout, ExchangeError, RateLimitExceeded

from modules.liquidswap.decorators import retry
from settings import NUMBER_OF_RETRIES, COLLECT_FROM_SUB_CEX
from utils.log import Logger


class OKXExchange(Logger):
    def __init__(
            self,
            api_key: str,
            api_secret: str,
            api_password: str,
            proxy: str | None = None

    ):
        Logger.__init__(self)
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_password = api_password
        self.proxy = proxy.strip() if proxy else None
        self.client = self.get_okx_client()

    def get_okx_client(self) -> okx | None:
        return ccxt.okx({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'password': self.api_password,
            'enableRateLimit': True,
            'aiohttp_proxy': self.proxy,
        })

    @retry(NUMBER_OF_RETRIES)
    async def withdraw(self, ccy: str, network: str, amount: float, address: str):
        await self.transfer_from_subs(ccy=ccy, silent_mode=True)
        balance = await self.get_free_balance(ccy, 'funding')

        if not balance or balance < amount:
            self.logger_msg(
                f'Exchange balance less than amount! balance: {balance} {ccy}, amount: {amount} {ccy}', 'error'
            )
            return

        async with self.client:
            resp = await self.client.withdraw(ccy, amount, address, params={
                "network": network
            })
            self.logger_msg(f'withdraw resp: {resp}', 'debug')

    @retry(NUMBER_OF_RETRIES, (PermissionDenied, RequestTimeout, ExchangeError, RateLimitExceeded))
    async def get_free_balance(
            self, ccy, balance_type: Literal['fund', 'unified', 'funding', 'trading']
    ) -> float | None:
        async with self.client:
            free_balance = await self.client.fetch_free_balance(params={'type': balance_type})
            self.logger_msg(f"[{ccy}] | [{balance_type}] free_balance: {free_balance}", 'debug')

            free_token_balance = free_balance.get(ccy)
            return free_token_balance

    async def transfer_from_spot_to_funding(self, ccy: str = 'ETH'):

        await asyncio.sleep(5)

        if ccy == 'USDC.e':
            ccy = 'USDC'

        balance = await self.get_free_balance(ccy, 'trading')
        if not balance:
            self.logger_msg(msg=f"Main trading account balance: 0 {ccy}", type_msg='warning')
            return

        self.logger_msg(msg=f"Main trading account balance: {balance} {ccy}")

        async with self.client:
            await self.client.transfer(ccy, balance, 'trading', 'funding')

        self.logger_msg(msg=f"Transfer {balance} {ccy} to funding account complete", type_msg='success')

    async def transfer_from_sub_accounts(self, ccy: str = 'ETH', amount: float = None, silent_mode: bool = False):
        if ccy == 'USDC.e':
            ccy = 'USDC'

        if not silent_mode:
            self.logger_msg(msg=f'Checking subAccounts balance')

        async with self.client:
            sub_list = await self.client.private_get_users_subaccount_list()

        await asyncio.sleep(1)
        for sub_data in sub_list['data']:
            sub_name = sub_data['subAcct']

            async with self.client:
                params = {
                    'subAcct': sub_name,
                    'ccy': ccy
                }
                sub_balance = await self.client.private_get_asset_subaccount_balances(params)
                if sub_balance:
                    sub_balance = float(sub_balance['data'][0]['availBal'])

            await asyncio.sleep(1)
            amount = amount if amount else sub_balance
            if sub_balance == amount and sub_balance != 0.0:
                self.logger_msg(msg=f'{sub_name} | subAccount balance : {sub_balance:.8f} {ccy}')
                async with self.client:
                    params = {
                        "ccy": ccy,
                        "type": "2",
                        "amt": f"{amount:.10f}",
                        "from": "6",
                        "to": "6",
                        "subAcct": sub_name
                    }
                    await self.client.privatePostAssetTransfer(params)
                self.logger_msg(msg=f"Transfer {amount:.8f} {ccy} to main account complete", type_msg='success')

    async def transfer_from_subs(self, ccy, amount: float = None, silent_mode: bool = False):
        if COLLECT_FROM_SUB_CEX:
            await self.transfer_from_sub_accounts(ccy=ccy, amount=amount, silent_mode=silent_mode)
            return await self.transfer_from_spot_to_funding(ccy=ccy)

        return True
