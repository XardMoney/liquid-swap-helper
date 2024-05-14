from aptos_sdk.transactions import EntryFunction
from pydantic import BaseModel

from core import enums
from core.contracts import TokenBase


class TransactionSimulationResult(BaseModel):
    result: enums.TransactionStatus
    vm_status: str | None = None
    gas_used: int


class TransactionPayloadData(BaseModel):
    payload: EntryFunction | dict
    amount_out_decimals: float
    amount_in_decimals: float
    token_out: TokenBase
    token_in: TokenBase

    class Config:
        arbitrary_types_allowed = True


class TransactionReceipt(BaseModel):
    status: enums.TransactionStatus
    vm_status: str | None = None
