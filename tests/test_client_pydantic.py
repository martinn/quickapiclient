from pydantic import BaseModel, Field
from pytest_httpx import HTTPXMock

import quickapi


class Fact(BaseModel):
    fact: str
    length: int


class RequestParams(BaseModel):
    max_length: int = 100
    limit: int = 10


class RequestBody(BaseModel):
    some_data: str | None = None


class ResponseBody(BaseModel):
    current_page: int = Field(lt=100)
    data: list[Fact] = Field(default_factory=list)


# TODO: Build real mock API to easily test various scenarios?
class PostPydanticApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    method = quickapi.BaseApiMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody


class TestGetPydanticApi:
    def test_api_call_with_default_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            url=f"{PostPydanticApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
        )

        client = PostPydanticApi()
        response = client.execute()
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

    def test_api_call_with_custom_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        httpx_mock.add_response(
            url=f"{PostPydanticApi.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            json=mock_json,
        )

        client = PostPydanticApi()
        response = client.execute(request_params=request_params)
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="fact", length=4)

    def test_api_call_with_custom_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        request_body = RequestBody(some_data="some data")
        httpx_mock.add_response(
            url=f"{PostPydanticApi.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            match_json={"some_data": request_body.some_data},
            json=mock_json,
        )

        client = PostPydanticApi()
        response = client.execute(
            request_params=request_params, request_body=request_body
        )
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="fact", length=4)
