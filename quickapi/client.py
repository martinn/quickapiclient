from enum import Enum
from typing import Any, Generic, TypeVar, get_args

import cattrs
import httpx
from attrs import asdict, define

from .exceptions import QuickApiException

ResponseBodyT = TypeVar("ResponseBodyT", bound="BaseResponseBody")


class ClientSetupError(QuickApiException):
    """An error setting up the BaseClient subclass."""

    def __init__(self, missing_attribute: str):
        message = (
            f"Subclass setup error. Missing required attribute `{missing_attribute}`."
        )
        super().__init__(message)


class HTTPError(QuickApiException):
    """The response received a non `200` response."""

    def __init__(self, status_code: int):
        message = f"HTTP request received a non `HTTP 200 (OK)` response. The response status code was `{status_code}`."
        super().__init__(message)


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
        return cattrs.structure(value, cls)


@define
class BaseResponse(Generic[ResponseBodyT]):
    client_response: httpx.Response
    body: ResponseBodyT


class BaseApiMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"


class BaseApi(Generic[ResponseBodyT]):
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

        if getattr(cls, "url", None) is None:
            raise ClientSetupError(missing_attribute="url")

        if getattr(cls, "response_body", None) is None:
            raise ClientSetupError(missing_attribute="response_body")

        if getattr(cls, "__orig_bases__", None) is not None:
            response_body_generic_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore [attr-defined]
            if (
                isinstance(response_body_generic_type, TypeVar)
                and response_body_generic_type.__name__ == "ResponseBodyT"
            ):
                raise ClientSetupError(missing_attribute="ResponseBodyT")

        if cls.request_params is not None:
            cls._request_params_cls = cls.request_params

        if cls.request_body is not None:
            cls._request_body_cls = cls.request_body

        cls._response_body_cls = cls.response_body  # pyright: ignore [reportGeneralTypeIssues]

    def __init__(self, client: httpx.Client | None = None) -> None:
        # TODO: Add proper support for other HTTP libraries
        self._client = client or httpx.Client()

    def execute(
        self,
        request_params: BaseRequestParams | None = None,
        request_body: BaseRequestBody | None = None,
        auth: httpx.Auth | Any = httpx.USE_CLIENT_DEFAULT,
    ) -> BaseResponse[ResponseBodyT]:
        request_params = request_params or self._request_params_cls()
        request_body = request_body or self._request_body_cls()
        auth = auth if auth != httpx.USE_CLIENT_DEFAULT else self.auth

        if self.method == BaseApiMethod.GET:
            response = self._client.get(
                url=self.url,
                auth=auth,
                params=request_params.to_dict(),
            )
        elif self.method == BaseApiMethod.POST:
            response = self._client.post(
                url=self.url,
                auth=auth,
                params=request_params.to_dict(),
                json=request_body.to_dict(),
            )
        else:
            raise NotImplementedError(f"Method {self.method} not implemented")

        if response.status_code != 200:
            raise HTTPError(response.status_code)

        body = self._response_body_cls.from_dict(response.json())
        self._response = BaseResponse(client_response=response, body=body)

        return self._response
