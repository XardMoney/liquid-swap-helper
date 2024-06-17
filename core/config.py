import asyncio
from settings import SLEEP_RANGE_BETWEEN_ACCOUNTS, SEMAPHORE_LIMIT, NUMBER_OF_RETRIES

SEMAPHORE_LIMIT = max(int(SEMAPHORE_LIMIT), 1)

NUMBER_OF_RETRIES = max(int(NUMBER_OF_RETRIES), 1)

SLEEP_RANGE = sorted(([max(int(x), 1) for x in SLEEP_RANGE_BETWEEN_ACCOUNTS] * 2)[:2])

FILE_LOCK = asyncio.Lock()

RPC_URLS: list[str] = ["https://rpc.ankr.com/http/aptos/v1", "https://fullnode.mainnet.aptoslabs.com/v1"]

SCAN_URL = "https://explorer.aptoslabs.com/txn/"

TOKENS_INFO = {
    'APT': '0x1::aptos_coin::AptosCoin',
    'USDC': '0xf22bede237a07e121b56d91a491eb7bcdfd1f5907926a9e58338f964a01b17fa::asset::USDC',
    'stAPTDitto': '0xd11107bdf0d6d7040c6c0bfbdecb6545191fdf13e8d8d259952f53e1713f61b5::staked_coin::StakedAptos',
    'stAPTAmnis': '0x111ae3e5bc816a5e63c2da97d0aa3886519e0cd5e4b046659fa35796bd11542a::stapt_token::StakedApt'
}

OKX_TOKENS_MAPPING = {
}
