import cattrs
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


class GetApiClient(quickapi.BaseClient):
    url: str = "https://catfact.ninja/facts"
    response_body = ResponseBody


class GetWithParamsApiClient(quickapi.BaseClient):
    url: str = "https://catfact.ninja/facts"
    request_params = RequestParams
    response_body = ResponseBody


class PostApiClient(quickapi.BaseClient):
    url: str = "https://catfact.ninja/facts"
    method = quickapi.BaseClientMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody


# TODO: Build real mock API to easily test various scenarios?
class TestCatFactsApiClient:
    def test_get_api_call_with_default_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(json=mock_json)

        client = GetApiClient()
        response = client.execute()

        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

    def test_get_api_call_with_custom_request_params(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = RequestParams(max_length=5, limit=10)
        httpx_mock.add_response(
            url=f"{GetApiClient.url}?max_length={request_params.max_length}&limit={request_params.limit}",
            json=mock_json,
        )

        client = GetWithParamsApiClient()
        response = client.execute(request_params=request_params)

        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="fact", length=4)

    def test_post_api_call_with_custom_request_body(self, httpx_mock: HTTPXMock):
        mock_json1 = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body1 = RequestBody()
        httpx_mock.add_response(
            method="POST", match_json=request_body1.to_dict(), json=mock_json1
        )

        client = PostApiClient()
        response = client.execute(request_body=request_body1)
        assert response.body == cattrs.structure(mock_json1, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

        mock_json2 = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body2 = RequestBody(some_data="Test body")
        httpx_mock.add_response(
            method="POST", match_json=request_body2.to_dict(), json=mock_json2
        )

        client = PostApiClient()
        response = client.execute(request_body=request_body2)
        assert response.body == cattrs.structure(mock_json2, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some other fact", length=16)
