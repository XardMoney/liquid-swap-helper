import httpx
from fake_useragent import UserAgent
from aptos_sdk.async_client import RestClient, ClientConfig
from aptos_sdk.metadata import Metadata


class AptosCustomRestClient(RestClient):
    def __init__(
            self,
            base_url: str,
            proxies: dict = None,
            client_config: ClientConfig = ClientConfig()

    ):
        self.base_url = base_url
        # Default limits
        limits = httpx.Limits()
        # Default timeouts but do not set a pool timeout, since the idea is that jobs will wait as
        # long as progress is being made.
        timeout = httpx.Timeout(60.0, pool=None)
        # Default headers
        headers = {Metadata.APTOS_HEADER: Metadata.get_aptos_header_val()}
        self.client = httpx.AsyncClient(
            http2=client_config.http2,
            limits=limits,
            timeout=timeout,
            headers=headers,
            proxies=proxies
        )
        self.client_config = client_config
        self._chain_id = None
        if client_config.api_key:
            self.client.headers["Authorization"] = f"Bearer {client_config.api_key}"


class CustomClient:
    def __init__(self, proxies: dict = None):
        limits = httpx.Limits()
        timeout = httpx.Timeout(60.0, pool=None)
        self.user_agent = UserAgent(platforms=["pc"])
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            proxies=proxies,
            http2=True
        )

    def get_random_user_agent(self):
        return self.user_agent.random

    async def get(self, url, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self.get_random_user_agent()
        return await self.client.get(url, headers=headers, **kwargs)

    async def post(self, url, data=None, **kwargs):
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self.get_random_user_agent()
        return await self.client.post(url, data=data, headers=headers, **kwargs)

    async def close(self):
        await self.client.aclose()
