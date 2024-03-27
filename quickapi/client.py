from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar, get_args

from .exceptions import (
    ClientSetupError,
    DictDeserializationError,
    DictSerializationError,
    HTTPError,
    RequestSerializationError,
    ResponseSerializationError,
)
from .http_client import (
    BaseHttpClient,
    BaseHttpClientAuth,
    BaseHttpClientResponse,
    HTTPxClient,
)
from .serializers import (
    DictSerializable,
    DictSerializableT,
)

USE_DEFAULT = object()

ResponseBodyT = TypeVar("ResponseBodyT")


@dataclass
class BaseResponse(Generic[ResponseBodyT]):
    client_response: BaseHttpClientResponse
    body: ResponseBodyT


class BaseApiMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"

    @staticmethod
    def values() -> dict[str, Enum]:
        return BaseApiMethod._value2member_map_


class BaseApi(Generic[ResponseBodyT]):
    """Base class for all API clients."""

    url: str
    method: BaseApiMethod = BaseApiMethod.GET
    auth: BaseHttpClientAuth = None
    request_params: type[DictSerializableT] | None = None
    request_body: type[DictSerializableT] | None = None
    response_body: type[ResponseBodyT]
    http_client: BaseHttpClient | None = None

    _http_client: BaseHttpClient = HTTPxClient()
    _request_params: "DictSerializableT | None" = None
    _request_body: "DictSerializableT | None" = None
    _response_body_cls: type[ResponseBodyT]
    _response: BaseResponse[ResponseBodyT] | None = None

    @classmethod
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._validate_subclass()

        if cls.request_params is not None:
            cls._request_params = cls.request_params()

        if cls.request_body is not None:
            cls._request_body = cls.request_body()

        cls._response_body_cls = cls.response_body  # pyright: ignore [reportGeneralTypeIssues]

        if cls.http_client is not None:
            cls._http_client = cls.http_client

    @classmethod
    def _validate_subclass(cls) -> None:
        if getattr(cls, "url", None) is None:
            raise ClientSetupError(attribute="url")

        if getattr(cls, "response_body", None) is None:
            raise ClientSetupError(attribute="response_body")

        if (
            getattr(cls, "method", None) is not None
            and cls.method not in BaseApiMethod.values()
        ):
            raise ClientSetupError(attribute="method")

        if getattr(cls, "http_client", None) is not None and not (
            isinstance(cls.http_client, BaseHttpClient)
        ):
            raise ClientSetupError(attribute="http_client")

        if getattr(cls, "__orig_bases__", None) is not None:
            response_body_generic_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore [attr-defined]
            if (
                isinstance(response_body_generic_type, TypeVar)
                and response_body_generic_type.__name__ == "ResponseBodyT"
            ):
                raise ClientSetupError(attribute="ResponseBodyT")

    def __init__(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> None:
        self._request_params = request_params or self._request_params
        self._request_body = request_body or self._request_body
        self._http_client = http_client or self._http_client
        self.auth = auth if auth != USE_DEFAULT else self.auth

    def execute(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> BaseResponse[ResponseBodyT]:
        """Execute the API request and return the response."""

        self._request_params = request_params or self._request_params
        self._request_body = request_body or self._request_body
        self._http_client = http_client or self._http_client
        self.auth = auth if auth != USE_DEFAULT else self.auth
        try:
            params = (
                DictSerializable.to_dict(self._request_params)
                if self._request_params
                else {}
            )
            json = (
                DictSerializable.to_dict(self._request_body)
                if self._request_body
                else {}
            )
        except DictDeserializationError as e:
            raise RequestSerializationError(expected_type=e.expected_type) from e

        match self.method:
            case BaseApiMethod.GET:
                client_response = self._http_client.get(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                )
            case BaseApiMethod.OPTIONS:
                client_response = self._http_client.options(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                )
            case BaseApiMethod.HEAD:
                client_response = self._http_client.head(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                )
            case BaseApiMethod.POST:
                client_response = self._http_client.post(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                    json=json,
                )
            case BaseApiMethod.PUT:
                client_response = self._http_client.put(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                    json=json,
                )
            case BaseApiMethod.PATCH:
                client_response = self._http_client.patch(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                    json=json,
                )
            case BaseApiMethod.DELETE:
                client_response = self._http_client.delete(
                    url=self.url,
                    auth=self.auth,
                    params=params,
                )
            case _:
                raise NotImplementedError(f"Method {self.method} not implemented.")

        # TODO: Add support for handling different response status codes
        if client_response.status_code != 200:
            raise HTTPError(client_response.status_code)

        try:
            body = DictSerializable.from_dict(
                self._response_body_cls, client_response.json()
            )
        except DictSerializationError as e:
            raise ResponseSerializationError(expected_type=e.expected_type) from e

        self._response = BaseResponse(client_response=client_response, body=body)

        return self._response
