from enum import Enum


class TransactionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    SENT = "sent"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"
    TIME_OUT = "time_out"


class ModuleExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    TEST_MODE = "test_mode"
    TIME_OUT = "time_out"
    SENT = "sent"
    ERROR = "error"
