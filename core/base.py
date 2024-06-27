import random
import time
from asyncio import sleep

from aptos_sdk.account import Account
from aptos_sdk.account_address import AccountAddress
from aptos_sdk.async_client import ApiError
from aptos_sdk.transactions import RawTransaction, TransactionPayload, EntryFunction
from aptos_sdk.type_tag import TypeTag, StructTag

from core.contracts import TokenBase
from core import enums
from core.client import AptosCustomRestClient, CustomClient
from core.config import RPC_URLS
from core.models import TransactionSimulationResult, TransactionReceipt
from modules.liquidswap.decorators import retry
from modules.liquidswap.exceptions import (
    TransactionSimulationError, TransactionSubmitError, TransactionFailedError, TransactionTimeoutError, TokenInfoError
)
from settings import GAS_MULTIPLIER, GAS_LIMIT, NUMBER_OF_RETRIES
from utils.log import Logger


class ModuleBase(Logger):
    def __init__(
            self,
            account: Account,
            cex_address: str,
            base_url: str = random.choice(RPC_URLS),
            proxies: dict = None
    ):
        Logger.__init__(self, account_address=account.account_address)

        self.base_url = base_url
        self.aptos_client = AptosCustomRestClient(base_url=base_url, proxies=proxies)
        self.custom_client = CustomClient(proxies=proxies)
        self.account = account
        self.cex_address = cex_address.strip()
        self.aptos_client.client_config.max_gas_amount = random.randint(*GAS_LIMIT)

        self.coin_x: TokenBase | None = None
        self.coin_y: TokenBase | None = None

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

        if not self.token_x_decimals or not self.token_y_decimals:
            raise TokenInfoError

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
            balance = await self.aptos_client.account_resource(
                wallet_address,
                f"0x1::coin::CoinStore<{token_address}>",
            )
            return int(balance["data"]["coin"]["value"])

        except Exception as e:
            self.logger_msg(str(e), 'error')
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
            data = await self.aptos_client.account_resource(
                resource_address,
                payload
            )
            return data

        except Exception as e:
            self.logger_msg(str(e), 'debug')
            return None

    @retry(attempts=NUMBER_OF_RETRIES)
    async def get_token_info(self, token_obj: TokenBase) -> dict | None:
        """
        Gets token info
        :param token_obj:
        :return:
        """
        if token_obj.symbol == "aptos":
            return None

        coin_address = AccountAddress.from_str(token_obj.address)

        token_info = await self.aptos_client.account_resource(
            coin_address,
            f"0x1::coin::CoinInfo<{token_obj.contract_address}>",
        )
        return token_info["data"]

    async def submit_bcs_transaction(self, signed_transaction):
        try:
            tx_hash = await self.aptos_client.submit_bcs_transaction(signed_transaction)
            return tx_hash
        except ApiError as e:
            self.logger_msg(f"ApiError: {e}", 'error')
            return None

    async def txn_pending_status(self, txn_hash: str) -> bool:
        """
        Checks if transaction is pending
        :param txn_hash:
        :return:
        """
        response = await self.aptos_client.client.get(f"{self.base_url}/transactions/by_hash/{txn_hash}")

        if response.status_code == 404:
            return True

        elif response.status_code >= 400:
            raise Exception(f"Error getting transaction due RPC error: {response.json()}")

        return response.json()["type"] == "pending_transaction"

    async def wait_for_receipt(self, txn_hash: str) -> TransactionReceipt:
        """
        Waits for transaction receipt
        :param txn_hash:
        :return:
        """
        start_time = time.time()
        while await self.txn_pending_status(txn_hash=txn_hash):
            if time.time() - start_time > self.aptos_client.client_config.transaction_wait_in_seconds:

                return TransactionReceipt(
                    status=enums.TransactionStatus.TIME_OUT,
                    vm_status=None
                )

            await sleep(1)

        response = await self.aptos_client.client.get(f"{self.base_url}/transactions/by_hash/{txn_hash}")
        vm_status = response.json().get("vm_status")
        if vm_status is None:
            await sleep(5)
            response = await self.aptos_client.client.get(f"{self.base_url}/transactions/by_hash/{txn_hash}")
            vm_status = response.json().get("vm_status")

        if response.json().get("success") is True:
            receipt = TransactionReceipt(
                status=enums.TransactionStatus.SUCCESS,
                vm_status=vm_status
            )
        else:
            receipt = TransactionReceipt(
                status=enums.TransactionStatus.FAILED,
                vm_status=vm_status
            )

        return receipt

    async def is_token_registered_for_address(
            self,
            wallet_address: AccountAddress,
            token_contract: str
    ):
        """
        Checks if token is registered for address
        :param wallet_address:
        :param token_contract:
        :return:
        """
        try:
            is_registered = await self.aptos_client.account_resource(
                wallet_address,
                f'0x1::coin::CoinStore<{token_contract}>'
            )
            return True

        except Exception as ex:
            self.logger_msg(f'error: {ex}', 'debug')
            return False

    async def register_coin_for_wallet(
            self,
            sender_account: Account,
            token_obj: TokenBase,
    ) -> str | None:
        """
        Sends coin register transaction
        :param sender_account:
        :param token_obj:
        :return:
        """
        payload = EntryFunction.natural(
            f"0x1::managed_coin",
            "register",
            [TypeTag(StructTag.from_str(token_obj.contract_address))],
            []
        )
        txn_info_message = f"Coin register {token_obj.symbol.upper()} for wallet"

        txn_hash = await self.simulate_and_send_transfer_type_transaction(
            account=sender_account,
            txn_payload=payload,
            txn_info_message=txn_info_message
        )

        return txn_hash

    async def build_raw_transaction(
            self,
            account: Account,
            payload: EntryFunction,
            gas_limit: int,
            gas_price: int
    ) -> RawTransaction:
        """
        Builds raw transaction
        :param account:
        :param payload:
        :param gas_limit:
        :param gas_price:
        :return:
        """
        raw_transaction = RawTransaction(
            sender=account.address(),
            sequence_number=await self.aptos_client.account_sequence_number(account.address()),
            payload=TransactionPayload(payload),
            max_gas_amount=gas_limit,
            gas_unit_price=gas_price,
            expiration_timestamps_secs=int(time.time()) + 600,
            chain_id=1
        )
        return raw_transaction

    async def estimate_transaction(
            self,
            raw_transaction: RawTransaction,
            sender_account: Account
    ) -> TransactionSimulationResult:
        """
        Estimates transaction gas usage
        :param raw_transaction:
        :param sender_account:
        :return:
        """
        txn_data = await self.aptos_client.simulate_transaction(
            transaction=raw_transaction,
            sender=sender_account
        )
        vm_status = txn_data[0]["vm_status"]

        if txn_data[0]["success"] is True:
            result = TransactionSimulationResult(
                result=enums.TransactionStatus.SUCCESS,
                vm_status=vm_status,
                gas_used=int(txn_data[0]["gas_used"])
            )
        else:
            result = TransactionSimulationResult(
                result=enums.TransactionStatus.FAILED,
                vm_status=vm_status,
                gas_used=0
            )

        return result

    async def prebuild_payload_and_estimate_transaction(
            self,
            txn_payload: EntryFunction,
            account: Account,
            gas_limit: int,
            gas_price: int
    ) -> TransactionSimulationResult:
        """
        Prebuilds payload and estimates transaction
        :param txn_payload:
        :param account:
        :param gas_limit:
        :param gas_price:
        :return:
        """
        raw_transaction = await self.build_raw_transaction(
            account=account,
            payload=txn_payload,
            gas_limit=gas_limit,
            gas_price=gas_price
        )

        simulation_result = await self.estimate_transaction(
            raw_transaction=raw_transaction,
            sender_account=account
        )

        return simulation_result

    @staticmethod
    def get_random_amount_out_of_token(
            min_amount,
            max_amount,
            decimals: int
    ) -> int:
        """
        Get random_task amount out of token with decimals
        :param min_amount:
        :param max_amount:
        :param decimals:
        :return:
        """
        random_amount = random.uniform(min_amount, max_amount)
        return int(random_amount * 10 ** decimals)

    def check_txn_receipt(self, txn_receipt, tx_hash) -> str | None:
        if txn_receipt.status == enums.TransactionStatus.SUCCESS:
            # msg = f"Transaction success, vm status: {txn_receipt.vm_status}. Txn Hash: {tx_hash}"
            # self.logger_msg(msg, 'success')
            return tx_hash

        elif txn_receipt.status == enums.TransactionStatus.FAILED:
            msg = f"Transaction failed, vm status: {txn_receipt.vm_status}. Txn Hash: {tx_hash}"
            raise TransactionFailedError(msg)

        elif txn_receipt.status == enums.TransactionStatus.TIME_OUT:
            msg = f"Transaction timeout, vm status: {txn_receipt.vm_status}. Txn Hash: {tx_hash}"
            raise TransactionTimeoutError(msg)

    async def simulate_and_send_transfer_type_transaction(
            self,
            account: Account,
            txn_payload: EntryFunction,
            txn_info_message: str
    ) -> str | None:
        """
        Simulates and sends transfer type transaction
        :param account:
        :param txn_payload:
        :param txn_info_message:
        :return:
        """
        if txn_info_message:
            self.logger_msg(f"Action: {txn_info_message}", 'warning')

        simulation_status = await self.prebuild_payload_and_estimate_transaction(
            account=account,
            txn_payload=txn_payload,
            gas_limit=self.aptos_client.client_config.max_gas_amount,
            gas_price=self.aptos_client.client_config.gas_unit_price
        )

        if simulation_status.result == enums.TransactionStatus.FAILED:
            err_msg = f"Transaction simulation failed. Status: {simulation_status.vm_status}"
            raise TransactionSimulationError(err_msg)

        self.logger_msg(
            f"Transaction simulation success. {txn_info_message} Gas used: {simulation_status.gas_used}",
            'debug'
        )

        if int(simulation_status.gas_used) <= 200:
            gas_limit = int(int(simulation_status.gas_used) * 2)
        else:
            gas_limit = int(int(simulation_status.gas_used) * GAS_MULTIPLIER)

        self.aptos_client.client_config.max_gas_amount = gas_limit

        signed_transaction = await self.aptos_client.create_bcs_signed_transaction(
            sender=account,
            payload=TransactionPayload(txn_payload)
        )
        tx_hash = await self.submit_bcs_transaction(signed_transaction=signed_transaction)
        if tx_hash is None:
            err_msg = f"Transaction submission failed"
            raise TransactionSubmitError(err_msg)

        self.logger_msg(
            f"Txn sent. Waiting for receipt (Timeout in {self.aptos_client.client_config.transaction_wait_in_seconds}s). "
            f"https://explorer.aptoslabs.com/txn/{tx_hash}",
            'warning'
        )
        txn_receipt = await self.wait_for_receipt(tx_hash)

        return self.check_txn_receipt(txn_receipt, tx_hash)
