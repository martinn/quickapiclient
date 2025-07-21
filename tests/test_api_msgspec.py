from typing import Annotated

import pytest
from msgspec import Meta, Struct, field
from pytest_httpx import HTTPXMock

import quickapi
from quickapi.serializers import MsgspecDeserializer, MsgspecSerializer


class Fact(Struct):
    fact: str
    length: int


class RequestParams(Struct):
    max_length: int = 100
    limit: int = 10


class RequestBody(Struct):
    some_data: str | None = None


class ResponseBody(Struct):
    current_page: int = Annotated[int, Meta(lt=100)]
    data: list[Fact] = field(default_factory=list)


class ResponseError401(Struct):
    status: str
    message: str


# TODO: Build real mock API to easily test various scenarios?
class PostMsgspecApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    method = quickapi.BaseHttpMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody
    response_errors = {401: ResponseError401}  # noqa: RUF012
    serializer = MsgspecSerializer
    deserializer = MsgspecDeserializer


class TestPostMsgspecApi:
    def test_api_call_with_default_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            url=f"{PostMsgspecApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
        )

        client = PostMsgspecApi()
        response = client.execute()
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

    def test_api_call_with_custom_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        httpx_mock.add_response(
            url=f"{PostMsgspecApi.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            json=mock_json,
        )

        client = PostMsgspecApi()
        response = client.execute(request_params=request_params)
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="fact", length=4)

    def test_api_call_with_custom_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        request_body = RequestBody(some_data="some data")
        httpx_mock.add_response(
            url=f"{PostMsgspecApi.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            match_json={"some_data": request_body.some_data},
            json=mock_json,
        )

        client = PostMsgspecApi()
        response = client.execute(
            request_params=request_params, request_body=request_body
        )
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="fact", length=4)

    def test_api_call_with_custom_response_errors(self, httpx_mock: HTTPXMock):
        mock_json = {"status": "Failure", "message": "Unauthorized"}
        httpx_mock.add_response(
            url=f"{PostMsgspecApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
            status_code=401,
        )

        client = PostMsgspecApi()
        with pytest.raises(quickapi.HandledHTTPError) as e:
            client.execute()

        assert e.value.status_code == 401
        assert e.value.body == ResponseError401(
            status="Failure", message="Unauthorized"
        )
