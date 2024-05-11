import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", '1') in ['1', 'true']

SHUFFLE_ACCOUNTS = True

# Use proxy (True or False)
USE_PROXY = True
STRICT_PROXY = False

# Limit of accounts that can be run concurrently
SEMAPHORE_LIMIT = 1

# Limit of retries for all the actions
NUMBER_OF_RETRIES = 5

SLEEP_RANGE_BETWEEN_ACCOUNTS = [150, 250]

# Swap settings
TOKENS_SWAP_INPUT = ["APT"]
TOKENS_SWAP_OUTPUT = ["stAPTDitto", "stAPTAmnis"]
MIN_BALANCE = 0.1
AMOUNT_PERCENT = ()
AMOUNT_QUANTITY = (0.15, 6)

SLEEP_RANGE_BETWEEN_REVERSE_SWAP = [150, 250]
REVERSE_SWAP = True

GAS_LIMIT = [4200, 4700]
GAS_PRICE = 1
