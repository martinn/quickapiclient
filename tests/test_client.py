import cattrs
import pytest
from attrs import define, field
from pytest_httpx import HTTPXMock

import quickapi


@define
class Fact:
    fact: str
    length: int


@define
class RequestParams(quickapi.BaseRequestParams):
    max_length: int = 100
    limit: int = 10


@define
class RequestBody(quickapi.BaseRequestBody):
    some_data: str | None = None


@define
class ResponseBody(quickapi.BaseResponseBody):
    current_page: int
    data: list[Fact] = field(factory=list)


# TODO: Build real mock API to easily test various scenarios?
class TestErrorApi:
    def test_should_raise_error_if_no_url_specified(self):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                response_body = ResponseBody

    def test_should_raise_error_if_no_response_body_specified(self):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"

    def test_should_raise_warning_if_no_generic_type_specified(self):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi):
                url = "https://example.com/facts"
                response_body = ResponseBody


class GetApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    response_body = ResponseBody


# TODO: Build real mock API to easily test various scenarios?
class TestGetApi:
    def test_api_call(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(json=mock_json)

        client = GetApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class GetWithParamsApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    request_params = RequestParams
    response_body = ResponseBody


class TestGetWithParamsApi:
    def test_api_call_with_default_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            url=f"{GetWithParamsApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
        )

        client = GetWithParamsApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)

    def test_api_call_with_custom_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        httpx_mock.add_response(
            url=f"{GetWithParamsApi.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            json=mock_json,
        )

        client = GetWithParamsApi()
        response = client.execute(request_params=request_params)
        assert response.body == cattrs.structure(mock_json, ResponseBody)


class PostApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    method = quickapi.BaseApiMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody


class TestPostApi:
    def test_api_call_with_empty_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body = RequestBody()
        httpx_mock.add_response(
            method="POST", match_json=request_body.to_dict(), json=mock_json
        )
        client = PostApi()
        response = client.execute(request_body=request_body)
        assert response.body == cattrs.structure(mock_json, ResponseBody)

    def test_api_call_with_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = RequestBody(some_data="Test body")
        httpx_mock.add_response(
            method="POST", match_json=request_body.to_dict(), json=mock_json
        )
        client = PostApi()
        response = client.execute(request_body=request_body)
        assert response.body == cattrs.structure(mock_json, ResponseBody)
