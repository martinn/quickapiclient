from base64 import b64encode

import attrs
import cattrs
import httpx
import httpx_auth
import pytest
from pytest_httpx import HTTPXMock

import quickapi


@attrs.define
class Fact:
    fact: str
    length: int


@attrs.define
class RequestParams(quickapi.BaseRequestParams):
    max_length: int = 100
    limit: int = 10


@attrs.define
class RequestBody(quickapi.BaseRequestBody):
    some_data: str | None = None


@attrs.define
class ResponseBody(quickapi.BaseResponseBody):
    current_page: int = attrs.field(validator=attrs.validators.lt(100))
    data: list[Fact] = attrs.field(factory=list)


# TODO: Build real mock API to easily test various scenarios?
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


@attrs.define
class AuthResponseBody(quickapi.BaseResponseBody):
    authenticated: bool
    user: str


class AuthWithBasicApi(quickapi.BaseApi[AuthResponseBody]):
    url = "https://httpbin.org/basic-auth/quickapi/secret"
    auth = httpx.BasicAuth(username="quickapi", password="secret")  # noqa: S106
    response_body = AuthResponseBody


class TestAuthWithBasicApi:
    def test_api_call_with_correct_credentials(self, httpx_mock: HTTPXMock):
        mock_json = {"authenticated": 1, "user": "quickapi"}
        userpass = b":".join((b"quickapi", b"secret"))
        token = b64encode(userpass).decode()
        httpx_mock.add_response(
            url=AuthWithBasicApi.url,
            match_headers={"Authorization": f"Basic {token}"},
            json=mock_json,
        )

        client = AuthWithBasicApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, AuthResponseBody)

    def test_api_call_with_incorrect_credentials(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=AuthWithBasicApi.url,
            status_code=401,
        )

        client = AuthWithBasicApi()
        with pytest.raises(quickapi.HTTPError):
            client.execute()


class AuthWithHeaderKeyApi(quickapi.BaseApi[AuthResponseBody]):
    url = "https://httpbin.org/bearer"
    response_body = AuthResponseBody


class TestAuthWithBearerApi:
    def test_api_call_with_correct_credentials(self, httpx_mock: HTTPXMock):
        mock_json = {"authenticated": 1, "user": "quickapi"}
        httpx_mock.add_response(
            url=AuthWithHeaderKeyApi.url,
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        client = AuthWithHeaderKeyApi()
        client.auth = httpx_auth.HeaderApiKey(
            header_name="X-Api-Key", api_key="my_api_key"
        )
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, AuthResponseBody)

    def test_api_call_with_correct_credentials_on_execute(self, httpx_mock: HTTPXMock):
        mock_json = {"authenticated": 1, "user": "quickapi"}
        httpx_mock.add_response(
            url=AuthWithHeaderKeyApi.url,
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        client = AuthWithHeaderKeyApi()
        response = client.execute(auth=auth)
        assert response.body == cattrs.structure(mock_json, AuthResponseBody)

    def test_api_call_with_incorrect_credentials(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=AuthWithHeaderKeyApi.url,
            status_code=401,
        )

        auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        client = AuthWithHeaderKeyApi()
        with pytest.raises(quickapi.HTTPError):
            client.execute(auth=auth)


class TestClientSetupError:
    def test_should_raise_error_if_no_url_specified(self, httpx_mock: HTTPXMock):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                response_body = ResponseBody

    def test_should_raise_error_if_no_response_body_specified(
        self, httpx_mock: HTTPXMock
    ):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"

    def test_should_raise_error_if_no_method_specified(self, httpx_mock: HTTPXMock):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"
                method = "INVALID"  # pyright: ignore [reportAssignmentType]
                response_body = ResponseBody

    def test_should_raise_warning_if_no_generic_type_specified(
        self, httpx_mock: HTTPXMock
    ):
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseApi):
                url = "https://example.com/facts"
                response_body = ResponseBody


class TestSerializationError:
    def test_error_if_response_body_attribute_incorrect_type(
        self, httpx_mock: HTTPXMock
    ):
        mock_json_incorrect_type = {"current_page": 0, "data": "incorrect_type"}
        httpx_mock.add_response(
            json=mock_json_incorrect_type,
        )

        with pytest.raises(quickapi.ResponseSerializationError):
            client = GetApi()
            client.execute()

    def test_error_if_response_body_required_attribute_missing(
        self, httpx_mock: HTTPXMock
    ):
        mock_json_attribute_missing = {"data": []}
        httpx_mock.add_response(
            json=mock_json_attribute_missing,
        )

        with pytest.raises(quickapi.ResponseSerializationError):
            client = GetApi()
            client.execute()

    def test_response_body_validator(self, httpx_mock: HTTPXMock):
        mock_json_validator_fail = {"current_page": 101}
        httpx_mock.add_response(
            json=mock_json_validator_fail,
        )

        with pytest.raises(quickapi.ResponseSerializationError):
            client = GetApi()
            client.execute()

        mock_json_validator_pass = {"current_page": 99}
        httpx_mock.add_response(
            json=mock_json_validator_pass,
        )

        client.execute()
