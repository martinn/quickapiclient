from enum import Enum
from typing import Generic, TypeVar, get_args

import cattrs
import httpx
from attrs import asdict, define

from .exceptions import QuickApiException

ResponseBodyT = TypeVar("ResponseBodyT", bound="BaseResponseBody")


class ClientSetupError(QuickApiException):
    """An error setting up the BaseClient subclass."""

    def __init__(self, missing_attribute: str):
        message = (
            f"Subclass setup error. Missing required attribute `{missing_attribute}`"
        )
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


class BaseClientMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"


@define
class BaseResponse(Generic[ResponseBodyT]):
    response: httpx.Response
    body: ResponseBodyT


# TODO: Should this be BaseApi?
class BaseClient(Generic[ResponseBodyT]):
    url: str
    method: BaseClientMethod = BaseClientMethod.GET
    request_params: type[BaseRequestParams] | None = None
    request_body: type[BaseRequestBody] | None = None
    response_body: type[ResponseBodyT]

    _request_params_cls: type[BaseRequestParams] = BaseRequestParams
    _request_body_cls: type[BaseRequestBody] = BaseRequestBody
    _response_body_cls: type[ResponseBodyT]
    _response: BaseResponse[ResponseBodyT] | None = None
    _client: httpx.Client

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
    ) -> BaseResponse[ResponseBodyT]:
        request_params = request_params or self._request_params_cls()
        request_body = request_body or self._request_body_cls()

        if self.method == BaseClientMethod.GET:
            response = self._client.get(url=self.url, params=request_params.to_dict())
        elif self.method == BaseClientMethod.POST:
            response = self._client.post(
                url=self.url,
                params=request_params.to_dict(),
                json=request_body.to_dict(),
            )
        else:
            raise NotImplementedError(f"Method {self.method} not implemented")

        body = self._response_body_cls.from_dict(response.json())
        self._response = BaseResponse(response=response, body=body)

        return self._response
