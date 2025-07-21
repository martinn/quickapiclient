from base64 import b64encode

import attrs
import cattrs
import httpx
import httpx_auth
import pytest
import responses
from pytest_httpx import HTTPXMock

import quickapi
from quickapi.serializers import AttrsSerializer


@attrs.define
class Fact:
    fact: str
    length: int


@attrs.define
class RequestParams:
    max_length: int = 100
    limit: int = 10


@attrs.define
class RequestBody:
    some_data: str | None = None


@attrs.define
class ResponseBody:
    current_page: int = attrs.field(validator=attrs.validators.lt(100))
    data: list[Fact] = attrs.field(factory=list)


@attrs.define
class ResponseError401:
    status: str
    message: str


# TODO: Build real mock API to easily test various scenarios?
class GetApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    response_body = ResponseBody
    serializer = AttrsSerializer


class TestGetApi:
    def test_api_call(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(json=mock_json)

        client = GetApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class GetApiRequestsClient(GetApi):
    http_client = quickapi.RequestsClient()


# TODO: Switch http mock so can re-use tests across http clients
class TestGetApiRequestsClient:
    @responses.activate
    def test_api_call(self):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        responses.add(
            method=GetApiRequestsClient.method,
            url=GetApiRequestsClient.url,
            json=mock_json,
        )

        client = GetApiRequestsClient()
        response = client.execute()
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class GetWithParamsApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    request_params = RequestParams
    response_body = ResponseBody
    response_errors = {401: ResponseError401}  # noqa: RUF012
    serializer = AttrsSerializer


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

    def test_api_call_with_custom_response_errors(self, httpx_mock: HTTPXMock):
        mock_json = {"status": "Failure", "message": "Unauthorized"}
        httpx_mock.add_response(
            url=f"{GetWithParamsApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
            status_code=401,
        )

        client = GetWithParamsApi()
        with pytest.raises(quickapi.HandledHTTPError) as e:
            client.execute()

        assert e.value.status_code == 401
        assert e.value.body == ResponseError401(
            status="Failure", message="Unauthorized"
        )

    def test_api_call_with_custom_response_errors_unserializable(
        self, httpx_mock: HTTPXMock
    ):
        mock_json = {"invalid_key": "Failure", "invalid_key_message": "Unauthorized"}
        httpx_mock.add_response(
            url=f"{GetWithParamsApi.url}?max_length={RequestParams().max_length}&limit={RequestParams().limit}",
            json=mock_json,
            status_code=401,
        )

        client = GetWithParamsApi()
        with pytest.raises(quickapi.ResponseSerializationError):
            client.execute()


class OptionsApi(GetApi):
    method = quickapi.BaseHttpMethod.OPTIONS


# TODO: Reduce code duplication in tests
class TestOptionsApi:
    def test_api_call(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(method=OptionsApi.method, json=mock_json)

        client = OptionsApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class HeadApi(GetApi):
    method = quickapi.BaseHttpMethod.HEAD


class TestHeadApi:
    def test_api_call(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(method=HeadApi.method, json=mock_json)

        client = HeadApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class DeleteApi(GetApi):
    method = quickapi.BaseHttpMethod.DELETE


class TestDeleteApi:
    def test_api_call(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(method=DeleteApi.method, json=mock_json)

        client = DeleteApi()
        response = client.execute()
        assert response.body == cattrs.structure(mock_json, ResponseBody)
        assert response.body.data[0] == Fact(fact="Some fact", length=9)


class PostApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/facts"
    method = quickapi.BaseHttpMethod.POST
    request_params = RequestParams
    request_body = RequestBody
    response_body = ResponseBody
    serializer = AttrsSerializer


class TestPostApi:
    def test_api_call_with_empty_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body = RequestBody()
        httpx_mock.add_response(
            method=PostApi.method,
            match_json=AttrsSerializer.to_dict(request_body),
            json=mock_json,
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
            method=PostApi.method,
            match_json=AttrsSerializer.to_dict(request_body),
            json=mock_json,
        )
        client = PostApi()
        response = client.execute(request_body=request_body)
        assert response.body == cattrs.structure(mock_json, ResponseBody)


class PostApiRequestsClient(PostApi):
    http_client = quickapi.RequestsClient()


class TestPostApiRequestsClient:
    @responses.activate
    def test_api_call_with_empty_request_body(self):
        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body = RequestBody()
        responses.add(
            method=PostApiRequestsClient.method,
            url=PostApiRequestsClient.url,
            json=mock_json,
            match=[
                responses.matchers.json_params_matcher(
                    AttrsSerializer.to_dict(request_body)
                )
            ],
        )

        client = PostApiRequestsClient()
        response = client.execute(request_body=request_body)
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some fact", length=9)

    @responses.activate
    def test_api_call_with_request_body(self):
        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = RequestBody(some_data="Test body")
        responses.add(
            method=PostApiRequestsClient.method,
            url=PostApiRequestsClient.url,
            json=mock_json,
            match=[
                responses.matchers.json_params_matcher(
                    AttrsSerializer.to_dict(request_body)
                )
            ],
        )

        client = PostApiRequestsClient()
        response = client.execute(request_body=request_body)
        assert response.body.current_page == 1
        assert response.body.data[0] == Fact(fact="Some other fact", length=16)


class PutApi(PostApi):
    method = quickapi.BaseHttpMethod.PUT


class TestPutApi:
    def test_api_call_with_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = RequestBody(some_data="Test body")
        httpx_mock.add_response(
            method=PutApi.method,
            match_json=AttrsSerializer.to_dict(request_body),
            json=mock_json,
        )
        client = PutApi()
        response = client.execute(request_body=request_body)
        assert response.body == cattrs.structure(mock_json, ResponseBody)


class PatchApi(PostApi):
    method = quickapi.BaseHttpMethod.PATCH


class TestPatchApi:
    def test_api_call_with_request_body(self, httpx_mock: HTTPXMock):
        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = RequestBody(some_data="Test body")
        httpx_mock.add_response(
            method=PatchApi.method,
            match_json=AttrsSerializer.to_dict(request_body),
            json=mock_json,
        )
        client = PatchApi()
        response = client.execute(request_body=request_body)
        print(response.body)
        assert response.body == cattrs.structure(mock_json, ResponseBody)


@attrs.define
class AuthResponseBody:
    authenticated: bool
    user: str


class AuthWithBasicApi(quickapi.BaseApi[AuthResponseBody]):
    url = "https://httpbin.org/basic-auth/quickapi/secret"
    auth = httpx.BasicAuth(username="quickapi", password="secret")  # noqa: S106
    response_body = AuthResponseBody
    serializer = AttrsSerializer


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
    serializer = AttrsSerializer


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
        with pytest.raises(quickapi.HTTPError) as e:
            client.execute(auth=auth)

        assert e.value.status_code == 401


class TestApiSetupError:
    def test_should_raise_error_if_no_response_body_specified(
        self, httpx_mock: HTTPXMock
    ):
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"

    def test_should_raise_error_if_no_method_specified(self, httpx_mock: HTTPXMock):
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"
                method = "INVALID"  # pyright: ignore [reportAssignmentType]
                response_body = ResponseBody

    def test_should_raise_warning_if_no_generic_type_specified(
        self, httpx_mock: HTTPXMock
    ):
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi):
                url = "https://example.com/facts"
                response_body = ResponseBody

    def test_should_raise_error_if_invalid_http_client(self, httpx_mock: HTTPXMock):
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[ResponseBody]):
                url = "https://example.com/facts"
                http_client = object()  # pyright: ignore [reportAssignmentType]
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
