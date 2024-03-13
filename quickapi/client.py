from enum import Enum
from typing import Generic, TypeVar, get_args

import cattrs
import httpx
from attrs import asdict, define


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
    request_params: type[BaseRequestParams]
    request_body: type[BaseRequestBody]
    response_body: type[ResponseBodyT]
    _response: BaseResponse[ResponseBodyT] | None = None
    _client: httpx.Client

    def __init__(self, client: httpx.Client | None = None) -> None:
        # TODO: Add proper support for other HTTP libraries
        self._client = client or httpx.Client()

    def execute(
        self,
        request_params: BaseRequestParams | None = None,
        request_body: BaseRequestBody | None = None,
        request_params = (
            request_params or self.request_params()
            if getattr(self, "request_params", None)
            else BaseRequestParams()
        )
        request_body = (
            request_body or self.request_body()
            if getattr(self, "request_body", None)
            else BaseRequestBody()
        )
    ) -> BaseResponse[ResponseBodyT]:

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

        body = self.response_body.from_dict(response.json())
        self._response = BaseResponse(response=response, body=body)

        return self._response
