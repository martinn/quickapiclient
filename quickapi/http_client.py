from contextlib import suppress
from typing import TYPE_CHECKING, TypeAlias

import httpx

from .exceptions import MissingDependencyError

if TYPE_CHECKING:
    # Optional dependency
    with suppress(ImportError):
        import requests

# TODO: Fix types
BaseHttpClientAuth: TypeAlias = (
    httpx.Auth | type["requests.auth.AuthBase"] | object | None
)
BaseHttpClientResponse: TypeAlias = httpx.Response | type["requests.Response"] | None


class BaseHttpClient:
    """Base interface for all HTTP clients."""

    def __init__(self, *args, **kwargs): ...  # type: ignore [no-untyped-def]

    def get(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def options(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def head(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def post(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def put(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def patch(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def delete(self, *args, **kwargs):  # type: ignore [no-untyped-def]
        raise NotImplementedError


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


class RequestsClient(BaseHttpClient):
    """
    A thin wrapper around requests.

    This client is only available if the requests library is installed with:
    `pip install quickapiclient[requests]`
    or `poetry add quickapiclient[requests]`.
    """

    def __init__(self, client: type["requests.sessions.Session"] | None = None):
        try:
            import requests
        except ImportError as exc:
            raise MissingDependencyError(dependency="requests") from exc

        self._client = client or requests.sessions.Session()

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
