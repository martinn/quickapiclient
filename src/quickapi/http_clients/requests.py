try:
    import requests
except ImportError:
    requests_installed = False
else:
    requests_installed = True

from quickapi.exceptions import MissingDependencyError
from quickapi.http_clients.base import BaseHttpClient


class RequestsClient(BaseHttpClient):
    """
    A thin wrapper around requests.

    This client is only available if the requests library is installed with:

    `pip install quickapiclient[requests]`
    or `poetry add quickapiclient[requests]`.
    """

    def __init__(self, client: type["requests.sessions.Session"] | None = None):
        if requests_installed is False:
            raise MissingDependencyError(dependency="requests")

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
