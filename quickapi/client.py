from enum import Enum
from typing import Any, Generic, TypeVar, get_args

import cattrs
import httpx
from attrs import asdict, define

from .exceptions import ClientSetupError, HTTPError, ResponseSerializationError

ResponseBodyT = TypeVar("ResponseBodyT", bound="BaseResponseBody")


@define
class BaseRequestParams:
    def to_dict(self: "BaseRequestParams") -> dict:
        return asdict(self)


@define
class BaseRequestBody:
    def to_dict(self: "BaseRequestBody") -> dict:
        return asdict(self)


# TODO: Needs to support differebt response body types (json, text, xml, etc)
class BaseResponseBody(Generic[ResponseBodyT]):
    @classmethod
    def from_dict(cls: type[ResponseBodyT], value: dict) -> ResponseBodyT:
        try:
            return cattrs.structure(value, cls)
        except cattrs.ClassValidationError as e:
            raise ResponseSerializationError(expected_type=cls.__name__) from e


@define
class BaseResponse(Generic[ResponseBodyT]):
    client_response: httpx.Response
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
    auth: httpx.Auth | Any = httpx.USE_CLIENT_DEFAULT
    request_params: type[BaseRequestParams] | None = None
    request_body: type[BaseRequestBody] | None = None
    response_body: type[ResponseBodyT]

    _client: httpx.Client
    _request_params_cls: type[BaseRequestParams] = BaseRequestParams
    _request_body_cls: type[BaseRequestBody] = BaseRequestBody
    _response_body_cls: type[ResponseBodyT]
    _response: BaseResponse[ResponseBodyT] | None = None

    @classmethod
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._validate_subclass()

        if cls.request_params is not None:
            cls._request_params_cls = cls.request_params

        if cls.request_body is not None:
            cls._request_body_cls = cls.request_body

        cls._response_body_cls = cls.response_body  # pyright: ignore [reportGeneralTypeIssues]

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

        if getattr(cls, "__orig_bases__", None) is not None:
            response_body_generic_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore [attr-defined]
            if (
                isinstance(response_body_generic_type, TypeVar)
                and response_body_generic_type.__name__ == "ResponseBodyT"
            ):
                raise ClientSetupError(attribute="ResponseBodyT")

    def __init__(self, client: httpx.Client | None = None) -> None:
        # TODO: Add proper support for other HTTP libraries
        self._client = client or httpx.Client()

    def execute(
        self,
        request_params: BaseRequestParams | None = None,
        request_body: BaseRequestBody | None = None,
        auth: httpx.Auth | Any = httpx.USE_CLIENT_DEFAULT,
    ) -> BaseResponse[ResponseBodyT]:
        """Execute the API request and return the response."""

        request_params = request_params or self._request_params_cls()
        request_body = request_body or self._request_body_cls()
        auth = auth if auth != httpx.USE_CLIENT_DEFAULT else self.auth

        match self.method:
            case BaseApiMethod.GET:
                client_response = self._client.get(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                )
            case BaseApiMethod.OPTIONS:
                client_response = self._client.options(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                )
            case BaseApiMethod.HEAD:
                client_response = self._client.head(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                )
            case BaseApiMethod.POST:
                client_response = self._client.post(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                    json=request_body.to_dict(),
                )
            case BaseApiMethod.PUT:
                client_response = self._client.put(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                    json=request_body.to_dict(),
                )
            case BaseApiMethod.PATCH:
                client_response = self._client.patch(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                    json=request_body.to_dict(),
                )
            case BaseApiMethod.DELETE:
                client_response = self._client.delete(
                    url=self.url,
                    auth=auth,
                    params=request_params.to_dict(),
                )
            case _:
                raise NotImplementedError(f"Method {self.method} not implemented.")

        # TODO: Add support for handling different response status codes
        if client_response.status_code != 200:
            raise HTTPError(client_response.status_code)

        body = self._response_body_cls.from_dict(client_response.json())
        self._response = BaseResponse(client_response=client_response, body=body)

        return self._response
