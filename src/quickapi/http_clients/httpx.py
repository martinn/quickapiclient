import httpx

from quickapi.http_clients.base import BaseHttpClient


class HTTPxClient(BaseHttpClient):
    """A thin wrapper around HTTPx. This is the default client."""

    def __init__(self, client: type[httpx.Client] | None = None):
        self._client = client or httpx.Client()

    def get(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.get(*args, **kwargs)

    def options(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.options(*args, **kwargs)

    def head(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.head(*args, **kwargs)

    def post(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.post(*args, **kwargs)

    def put(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.put(*args, **kwargs)

    def patch(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.patch(*args, **kwargs)

    def delete(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        return self._client.delete(*args, **kwargs)
