import os
from dotenv import load_dotenv

load_dotenv()

DEBUG_MODE = 0

SHUFFLE_ACCOUNTS = True

# Use proxy (True or False)
USE_PROXY = True
STRICT_PROXY = False

# Limit of accounts that can be run concurrently
SEMAPHORE_LIMIT = 1

# Limit of retries for all the actions
NUMBER_OF_RETRIES = 5

SLEEP_RANGE_BETWEEN_ACCOUNTS = [150, 250]  # [0, 10000]

# Swap settings
TOKENS_SWAP_INPUT = ["APT"]  # "APT", "stAPTDitto", "stAPTAmnis"
TOKENS_SWAP_OUTPUT = ["stAPTDitto", "stAPTAmnis"]  # "APT", "stAPTDitto", "stAPTAmnis"
MIN_BALANCE = 0.1  # 0.1 - 1000
AMOUNT_PERCENT = (10, 30)  # (1, 100)
AMOUNT_QUANTITY = (0.15, 0.5)  # (0.1, 5)

SLEEP_RANGE_BETWEEN_REVERSE_SWAP = [150, 250]  # [0, 10000]
REVERSE_SWAP = True  # True/False
SWAPS_LIMIT_RANGE = [2, 10]  # [1, 5]

GAS_MULTIPLIER = 1.15  # 1.01 - 2


# MODULES = ['liquid_swap.swap, liquid_swap.full_swap, liquid_swap.reverse_swap']
MODULES = ['liquid_swap.full_swap']

# TODO пример определения модулей для дальнейшего улучшения
# MODULES = {
#     'liquid_swap': [
#         'swap',  # Swap только в одну сторону
#         'full_swap',  # Swap c возвратом в исходный токен
#         'reverse_swap'  # Swap из монет в TOKENS_SWAP_OUTPUT в нативный токен
#     ]
# }
