from abc import ABC, abstractmethod
from collections.abc import Sequence

from quickapi.exceptions import HTTPError
from quickapi.http_clients.types import (
    BaseHttpClientAuth,
    BaseHttpClientResponse,
    BaseHttpMethod,
)


class BaseHttpClient(ABC):
    """
    Base interface for all HTTP clients.

    You can create your own HTTP client by subclassing this class.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs): ...  # type: ignore [no-untyped-def]

    @abstractmethod
    def get(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def options(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def head(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def post(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def put(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def patch(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    @abstractmethod
    def delete(self, *args, **kwargs) -> BaseHttpClientResponse:  # type: ignore [no-untyped-def]
        raise NotImplementedError

    def send_request(
        self,
        method: BaseHttpMethod,
        url: str,
        auth: BaseHttpClientAuth,
        params: dict | None,
        json: dict | None,
    ) -> BaseHttpClientResponse:
        match method:
            case BaseHttpMethod.GET:
                client_response = self.get(
                    url=url,
                    auth=auth,
                    params=params,
                )
            case BaseHttpMethod.OPTIONS:
                client_response = self.options(
                    url=url,
                    auth=auth,
                    params=params,
                )
            case BaseHttpMethod.HEAD:
                client_response = self.head(
                    url=url,
                    auth=auth,
                    params=params,
                )
            case BaseHttpMethod.POST:
                client_response = self.post(
                    url=url,
                    auth=auth,
                    params=params,
                    json=json,
                )
            case BaseHttpMethod.PUT:
                client_response = self.put(
                    url=url,
                    auth=auth,
                    params=params,
                    json=json,
                )
            case BaseHttpMethod.PATCH:
                client_response = self.patch(
                    url=url,
                    auth=auth,
                    params=params,
                    json=json,
                )
            case BaseHttpMethod.DELETE:
                client_response = self.delete(
                    url=url,
                    auth=auth,
                    params=params,
                )
            case _:
                raise NotImplementedError(f"Method {method} not implemented.")

        return client_response

    def raise_for_errors(
        self,
        client_response: BaseHttpClientResponse,
        response_success_codes: Sequence[int] = (200, 201),
    ) -> None:
        match client_response.status_code:
            case success if success in response_success_codes:
                return
            case _:
                raise HTTPError(
                    client_response,
                    status_code=client_response.status_code,
                    body=client_response.text,
                )
