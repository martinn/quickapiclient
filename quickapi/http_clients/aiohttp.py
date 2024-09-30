try:
    import aiohttp
except ImportError:
    aiohttp_installed = False
else:
    aiohttp_installed = True


from quickapi.exceptions import MissingDependencyError
from quickapi.http_clients.base import BaseHttpClient
from quickapi.http_clients.types import BaseHttpMethod


class AiohttpClient(BaseHttpClient):
    def __init__(self, client: aiohttp.ClientSession | None = None):
        if not aiohttp_installed:
            raise MissingDependencyError(dependency="aiohttp")

        self._client = client or aiohttp.ClientSession()

    async def _request(self, method: str, *args, **kwargs):  # type: ignore [no-untyped-def]
        """Helper method to handle the requests using async with."""
        async with self._client as session, session.request(
            method, *args, **kwargs
        ) as response:
            return response

    async def get(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.GET, *args, **kwargs)

    async def options(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.OPTIONS, *args, **kwargs)

    async def head(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.HEAD, *args, **kwargs)

    async def post(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.POST, *args, **kwargs)

    async def put(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.PUT, *args, **kwargs)

    async def patch(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.PATCH, *args, **kwargs)

    async def delete(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return await self._request(BaseHttpMethod.DELETE, *args, **kwargs)
