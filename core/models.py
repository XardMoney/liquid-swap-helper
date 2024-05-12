from aptos_sdk.transactions import EntryFunction
from pydantic import BaseModel

from core import enums


class TransactionSimulationResult(BaseModel):
    result: enums.TransactionStatus
    vm_status: str | None = None
    gas_used: int


class TransactionPayloadData(BaseModel):
    payload: EntryFunction | dict
    amount_x_decimals: float
    amount_y_decimals: float

    class Config:
        arbitrary_types_allowed = True


class TransactionReceipt(BaseModel):
    status: enums.TransactionStatus
    vm_status: str | None = None
