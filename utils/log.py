from datetime import datetime
from abc import ABC
from typing import Literal

from aptos_sdk.account_address import AccountAddress
from loguru import logger
from sys import stderr

from settings import DEBUG_MODE


class Logger(ABC):
    def __init__(self, account_address: AccountAddress | None = None):
        self.logger = logger
        self.account_address = account_address

        self.logger.remove()
        logger_format = "<cyan>{time:HH:mm:ss}</cyan> | <level>" "{level: <8}</level> | <level>{message}</level>"
        if DEBUG_MODE:
            self.logger.add(stderr, level="DEBUG", format=logger_format)
        else:
            self.logger.add(stderr, level="INFO", format=logger_format)
        date = datetime.today().date()
        self.logger.add(f"./files/logs/{date}.log", rotation="500 MB", level="INFO", format=logger_format)

    def logger_msg(
            self,
            msg: str,
            type_msg: Literal['debug', 'info', 'error', 'success', 'warning', 'critical'] = 'info'
    ):
        class_name = self.__class__.__name__

        info = ''
        if self.account_address is not None:
            info += f'[{self.account_address}] |'
        info += f'[{class_name}] |'

        match type_msg:
            case 'debug':
                self.logger.debug(f"{info} {msg}")
            case 'info':
                self.logger.info(f"{info} {msg}")
            case 'error':
                self.logger.error(f"{info} {msg}")
            case 'success':
                self.logger.success(f"{info} {msg}")
            case 'warning':
                self.logger.warning(f"{info} {msg}")
            case 'critical':
                self.logger.critical(f"{info} {msg}")
