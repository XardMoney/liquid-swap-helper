import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = os.getenv('DEBUG_MODE', 0)

SHUFFLE_ACCOUNTS = False

# Limit of accounts that can be run concurrently
SEMAPHORE_LIMIT = 1

# Limit of retries for all the actions
NUMBER_OF_RETRIES = 5

SLEEP_RANGE_BETWEEN_ACCOUNTS = [150, 250]  # [0, 10000]
SLEEP_RANGE_BETWEEN_ATTEMPT = [10, 20]  # [0, 10000]

# Swap settings
TOKEN_SWAP_INPUT = "APT"  # "APT", "stAPTDitto", "stAPTAmnis"
TOKENS_SWAP_OUTPUT = ["stAPTDitto", "stAPTAmnis"]  # "APT", "stAPTDitto", "stAPTAmnis"
MIN_BALANCE = 3 # 0.1 - 1000
AMOUNT_PERCENT = (85, 95)  # (1, 100)
AMOUNT_QUANTITY = (0.15, 0.5)  # (0.1, 5)

SLEEP_RANGE_BETWEEN_REVERSE_SWAP = [150, 250]  # [0, 10000]
REVERSE_SWAP = True  # True/False
SWAPS_LIMIT_RANGE = [2, 5]  # [1, 5]

GAS_MULTIPLIER = 1.25  # 1.01 - 2

# Gas limit of each transaction, 100000 = 0.1 APT (random selection)
GAS_LIMIT = [5200, 5700]


'-------------------------------------------DASHBOARD REGISTRATION----------------------------------------------------'
REF_CODE = None
SLEEP_RANGE_AFTER_REGISTRATION = [15, 30]  # [0, 10000]


'------------------------------------------------DATA CONTROL---------------------------------------------------------'
# Encrypted excel file
EXCEL_ENCRYPTED = False
# Path to file with the accounts data (if unsure, leave the option at the default)
EXCEL_FILE_PATH = os.getenv('EXCEL_FILE_PATH', "files/accounts.xlsx")
# Name of page with the accounts data (if unsure, leave the option at the default)
EXCEL_PAGE_NAME = "data"

'----------------------------------------------EXCHANGE CONTROL--------------------------------------------------------'

MIN_WALLET_BALANCE = 2
DEPOSIT_LIMIT_RANGE = [10, 15]
SLEEP_RANGE_BEFORE_SEND_TO_CEX = [100, 300]
WITHDRAW_PERCENT_RANGE = (90, 95)

COLLECT_FROM_SUB_CEX = True
# http://user:login@ip:port
OKX_PROXY = os.getenv('OKX_PROXY', None)
OKX_API_KEY = os.getenv('OKX_API_KEY', '')
OKX_API_SECRET = os.getenv('OKX_API_SECRET', '')
OKX_API_PASS_PHRASE = os.getenv('OKX_API_PASS_PHRASE', '')
