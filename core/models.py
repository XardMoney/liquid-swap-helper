from aptos_sdk.transactions import EntryFunction
from pydantic import BaseModel

from core import enums


class TransactionSimulationResult(BaseModel):
    result: enums.TransactionStatus
    vm_status: str | None = None
    gas_used: int


class TransactionPayloadData(BaseModel):
    payload: EntryFunction
    amount_x_decimals: float
    amount_y_decimals: float

    class Config:
        arbitrary_types_allowed = True


class ModuleExecutionResult(BaseModel):
    execution_status: enums.ModuleExecutionStatus = enums.ModuleExecutionStatus.FAILED
    retry_needed: bool = True
    execution_info: str | None = None
    hash: str | None = None


class TransactionReceipt(BaseModel):
    status: enums.TransactionStatus
    vm_status: str | None = None
