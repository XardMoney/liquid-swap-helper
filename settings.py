import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv("DEBUG_MODE", '1') in ['1', 'true']

SHUFFLE_ACCOUNTS = True

# Use proxy (True or False)
USE_PROXY = False
STRICT_PROXY = False

# Limit of accounts that can be run concurrently
SEMAPHORE_LIMIT = 5

# Limit of retries for all the actions
NUMBER_OF_RETRIES = 5

SLEEP_RANGE = [15, 25]

# Swap settings
TOKENS_SWAP_INPUT = ["aptos"]
TOKENS_SWAP_OUTPUT = ["stAPTDitto", "stAPTAmnis"]
MIN_BALANCE = 0.1
AMOUNT_PERCENT = (10, 30)
AMOUNT_QUANTITY = ()

SLEEP_RANGE_BETWEEN_REVERSE_SWAP = [15, 25]
REVERSE_SWAP = True

