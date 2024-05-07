from aptos_sdk.account_address import AccountAddress

POOL_TYPES = ['Uncorrelated', 'Stable']

POOLS_INFO = {
    'v0': {
        'resource_address': AccountAddress.from_str(
            '0x05a97986a9d031c4567e15b797be516910cfcb4156312482efc6a19c0a30c948'
        ),
        'router_address': AccountAddress.from_str(
            '0x190d44266241744264b964a37b8f09863167a12d3e70cda39376cfb4e3561e12'
        ),
        'types': ['Uncorrelated', 'Stable']
    },
    'v0.5': {
        'resource_address': AccountAddress.from_str(
            '0x61d2c22a6cb7831bee0f48363b0eec92369357aece0d1142062f7d5d85c7bef8'
        ),
        'router_address': AccountAddress.from_str(
            '0x0163df34fccbf003ce219d3f1d9e70d140b60622cb9dd47599c25fb2f797ba6e'
        ),
        'types': ['Uncorrelated', 'Stable']
    }
}
