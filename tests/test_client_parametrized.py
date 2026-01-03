"""Parametrized tests for BaseClient across all serialization libraries."""

import dataclasses
from base64 import b64encode
from typing import Any, ClassVar

import attrs
import httpx
import httpx_auth
import msgspec
import pydantic
import pytest
import responses
from pytest_httpx import HTTPXMock

import quickapi


# ============================================================================
# Model Definitions for Each Serialization Library
# ============================================================================


@dataclasses.dataclass
class DataclassFact:
    fact: str
    length: int


@dataclasses.dataclass
class DataclassRequestParams:
    max_length: int = 100
    limit: int = 10


@dataclasses.dataclass
class DataclassRequestBody:
    some_data: str | None = None


@dataclasses.dataclass
class DataclassResponseBody:
    current_page: int
    data: list[DataclassFact] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class DataclassResponseError401:
    status: str
    message: str


@dataclasses.dataclass
class DataclassAuthResponseBody:
    authenticated: bool
    user: str


@attrs.define
class AttrsFact:
    fact: str
    length: int


@attrs.define
class AttrsRequestParams:
    max_length: int = 100
    limit: int = 10


@attrs.define
class AttrsRequestBody:
    some_data: str | None = None


@attrs.define
class AttrsResponseBody:
    current_page: int = attrs.field(validator=attrs.validators.lt(100))
    data: list[AttrsFact] = attrs.field(factory=list)


@attrs.define
class AttrsResponseError401:
    status: str
    message: str


@attrs.define
class AttrsAuthResponseBody:
    authenticated: bool
    user: str


class PydanticFact(pydantic.BaseModel):
    fact: str
    length: int


class PydanticRequestParams(pydantic.BaseModel):
    max_length: int = 100
    limit: int = 10


class PydanticRequestBody(pydantic.BaseModel):
    some_data: str | None = None


class PydanticResponseBody(pydantic.BaseModel):
    current_page: int = pydantic.Field(lt=100)
    data: list[PydanticFact] = pydantic.Field(default_factory=list)


class PydanticResponseError401(pydantic.BaseModel):
    status: str
    message: str


class PydanticAuthResponseBody(pydantic.BaseModel):
    authenticated: bool
    user: str


class MsgspecFact(msgspec.Struct):
    fact: str
    length: int


class MsgspecRequestParams(msgspec.Struct):
    max_length: int = 100
    limit: int = 10


class MsgspecRequestBody(msgspec.Struct):
    some_data: str | None = None


class MsgspecResponseBody(msgspec.Struct):
    current_page: int
    data: list[MsgspecFact] = msgspec.field(default_factory=list)


class MsgspecResponseError401(msgspec.Struct):
    status: str
    message: str


class MsgspecAuthResponseBody(msgspec.Struct):
    authenticated: bool
    user: str


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================


@pytest.fixture(
    params=[
        pytest.param(
            {
                "name": "dataclasses",
                "fact": DataclassFact,
                "request_params": DataclassRequestParams,
                "request_body": DataclassRequestBody,
                "response_body": DataclassResponseBody,
                "response_error_401": DataclassResponseError401,
                "auth_response_body": DataclassAuthResponseBody,
            },
            id="dataclasses",
        ),
        pytest.param(
            {
                "name": "attrs",
                "fact": AttrsFact,
                "request_params": AttrsRequestParams,
                "request_body": AttrsRequestBody,
                "response_body": AttrsResponseBody,
                "response_error_401": AttrsResponseError401,
                "auth_response_body": AttrsAuthResponseBody,
            },
            id="attrs",
        ),
        pytest.param(
            {
                "name": "pydantic",
                "fact": PydanticFact,
                "request_params": PydanticRequestParams,
                "request_body": PydanticRequestBody,
                "response_body": PydanticResponseBody,
                "response_error_401": PydanticResponseError401,
                "auth_response_body": PydanticAuthResponseBody,
            },
            id="pydantic",
        ),
        pytest.param(
            {
                "name": "msgspec",
                "fact": MsgspecFact,
                "request_params": MsgspecRequestParams,
                "request_body": MsgspecRequestBody,
                "response_body": MsgspecResponseBody,
                "response_error_401": MsgspecResponseError401,
                "auth_response_body": MsgspecAuthResponseBody,
            },
            id="msgspec",
        ),
    ]
)
def serializer_models(request):
    """Fixture that provides model classes for each serialization library."""
    return request.param


def create_client_class(models: dict[str, Any]) -> type[quickapi.BaseClient]:
    """Create a BaseClient class with API endpoints using the provided models."""

    # Define API endpoints
    class GetApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        request_params = models["request_params"]
        response_body = models["response_body"]
        response_errors: ClassVar = {401: models["response_error_401"]}

    class PostApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.POST
        request_params = models["request_params"]
        request_body = models["request_body"]
        response_body = models["response_body"]
        response_errors: ClassVar = {401: models["response_error_401"]}

    class PutApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.PUT
        request_params = models["request_params"]
        request_body = models["request_body"]
        response_body = models["response_body"]

    class PatchApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.PATCH
        request_params = models["request_params"]
        request_body = models["request_body"]
        response_body = models["response_body"]

    class DeleteApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.DELETE
        response_body = models["response_body"]

    class OptionsApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.OPTIONS
        response_body = models["response_body"]

    class HeadApi(quickapi.BaseApi[models["response_body"]]):
        url = "/facts"
        method = quickapi.BaseHttpMethod.HEAD
        response_body = models["response_body"]

    class AuthBasicApi(quickapi.BaseApi[models["auth_response_body"]]):
        url = "/basic-auth/quickapi/secret"
        response_body = models["auth_response_body"]

    class AuthHeaderKeyApi(quickapi.BaseApi[models["auth_response_body"]]):
        url = "/bearer"
        response_body = models["auth_response_body"]

    # Create BaseClient with all endpoints
    class TestClient(quickapi.BaseClient):
        base_url = "https://example.com"
        get_facts = quickapi.ApiEndpoint(GetApi)
        post_facts = quickapi.ApiEndpoint(PostApi)
        put_facts = quickapi.ApiEndpoint(PutApi)
        patch_facts = quickapi.ApiEndpoint(PatchApi)
        delete_facts = quickapi.ApiEndpoint(DeleteApi)
        options_facts = quickapi.ApiEndpoint(OptionsApi)
        head_facts = quickapi.ApiEndpoint(HeadApi)
        auth_basic = quickapi.ApiEndpoint(AuthBasicApi)
        auth_header = quickapi.ApiEndpoint(AuthHeaderKeyApi)

    return TestClient


# ============================================================================
# Parametrized Tests for BaseClient
# ============================================================================


class TestBaseClientHttpMethods:
    """Test different HTTP methods using BaseClient."""

    def test_get_request_with_default_params(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test GET request with default request parameters."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json,
        )

        client = client_cls()
        response = client.get_facts()

        assert response.body.current_page == 1
        assert response.body.data[0].fact == "Some fact"
        assert response.body.data[0].length == 9

    def test_get_request_with_custom_params(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test GET request with custom request parameters."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "fact", "length": 4}]}
        request_params = models["request_params"](max_length=5, limit=10)
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=5&limit=10",
            json=mock_json,
        )

        client = client_cls()
        response = client.get_facts(request_params=request_params)

        assert response.body.current_page == 1
        assert response.body.data[0] == models["fact"](fact="fact", length=4)

    def test_post_request_with_empty_body(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test POST request with empty request body."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body = models["request_body"]()
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.post_facts.url}?max_length=100&limit=10",
            match_json=quickapi.DictSerializable.to_dict(request_body),
            json=mock_json,
        )

        client = client_cls()
        response = client.post_facts(request_body=request_body)

        assert response.body.current_page == 1
        assert response.body.data[0] == models["fact"](fact="Some fact", length=9)

    def test_post_request_with_body(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test POST request with request body."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = models["request_body"](some_data="Test body")
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.post_facts.url}?max_length=100&limit=10",
            match_json=quickapi.DictSerializable.to_dict(request_body),
            json=mock_json,
        )

        client = client_cls()
        response = client.post_facts(request_body=request_body)

        assert response.body.current_page == 1
        assert response.body.data[0] == models["fact"](
            fact="Some other fact", length=16
        )

    def test_put_request_with_body(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test PUT request with request body."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = models["request_body"](some_data="Test body")
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.put_facts.url}?max_length=100&limit=10",
            match_json=quickapi.DictSerializable.to_dict(request_body),
            json=mock_json,
        )

        client = client_cls()
        response = client.put_facts(request_body=request_body)

        assert response.body.current_page == 1

    def test_patch_request_with_body(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test PATCH request with request body."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {
            "current_page": 1,
            "data": [{"fact": "Some other fact", "length": 16}],
        }
        request_body = models["request_body"](some_data="Test body")
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.patch_facts.url}?max_length=100&limit=10",
            match_json=quickapi.DictSerializable.to_dict(request_body),
            json=mock_json,
        )

        client = client_cls()
        response = client.patch_facts(request_body=request_body)

        assert response.body.current_page == 1

    def test_delete_request(self, serializer_models: dict, httpx_mock: HTTPXMock):
        """Test DELETE request."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            method="DELETE",
            url=f"{client_cls.base_url}{client_cls.delete_facts.url}",
            json=mock_json,
        )

        client = client_cls()
        response = client.delete_facts()

        assert response.body.current_page == 1

    def test_options_request(self, serializer_models: dict, httpx_mock: HTTPXMock):
        """Test OPTIONS request."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            method="OPTIONS",
            url=f"{client_cls.base_url}{client_cls.options_facts.url}",
            json=mock_json,
        )

        client = client_cls()
        response = client.options_facts()

        assert response.body.current_page == 1

    def test_head_request(self, serializer_models: dict, httpx_mock: HTTPXMock):
        """Test HEAD request."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        httpx_mock.add_response(
            method="HEAD",
            url=f"{client_cls.base_url}{client_cls.head_facts.url}",
            json=mock_json,
        )

        client = client_cls()
        response = client.head_facts()

        assert response.body.current_page == 1


class TestBaseClientErrorHandling:
    """Test error handling for BaseClient."""

    def test_handled_http_error_with_custom_response_errors(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test that custom response errors are properly handled."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"status": "Failure", "message": "Unauthorized"}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json,
            status_code=401,
        )

        client = client_cls()
        with pytest.raises(quickapi.HandledHTTPError) as e:
            client.get_facts()

        assert e.value.status_code == 401
        assert e.value.body == models["response_error_401"](
            status="Failure", message="Unauthorized"
        )

    def test_handled_http_error_with_unserializable_response(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test error when response cannot be serialized to expected error type.
        
        Note: Dataclasses don't raise serialization errors for missing fields,
        so this test is skipped for that serializer.
        """
        models = serializer_models
        
        # Skip for dataclasses as it doesn't raise serialization errors
        if models["name"] == "dataclasses":
            pytest.skip("Dataclasses don't raise serialization errors for missing fields")
        
        client_cls = create_client_class(models)

        mock_json = {"invalid_key": "Failure", "invalid_key_message": "Unauthorized"}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json,
            status_code=401,
        )

        client = client_cls()
        with pytest.raises(quickapi.ResponseSerializationError):
            client.get_facts()


class TestBaseClientAuthentication:
    """Test authentication methods with BaseClient."""

    def test_basic_auth_with_correct_credentials(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test basic authentication with correct credentials."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"authenticated": True, "user": "quickapi"}
        userpass = b":".join((b"quickapi", b"secret"))
        token = b64encode(userpass).decode()
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.auth_basic.url}",
            match_headers={"Authorization": f"Basic {token}"},
            json=mock_json,
        )

        auth = httpx.BasicAuth(username="quickapi", password="secret")  # noqa: S106
        client = client_cls(auth=auth)
        response = client.auth_basic()

        assert response.body.authenticated is True
        assert response.body.user == "quickapi"

    def test_basic_auth_with_incorrect_credentials(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test basic authentication with incorrect credentials."""
        models = serializer_models
        client_cls = create_client_class(models)

        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.auth_basic.url}",
            status_code=401,
        )

        client = client_cls()
        with pytest.raises(quickapi.HTTPError):
            client.auth_basic()

    def test_header_api_key_auth_on_client(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test header API key authentication set on client."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"authenticated": True, "user": "quickapi"}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.auth_header.url}",
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        client = client_cls(auth=auth)
        response = client.auth_header()

        assert response.body.authenticated is True

    def test_header_api_key_auth_on_execute(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test header API key authentication passed to execute method."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"authenticated": True, "user": "quickapi"}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.auth_header.url}",
            match_headers={"X-Api-Key": "my_api_key"},
            json=mock_json,
        )

        auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        client = client_cls()
        response = client.auth_header(auth=auth)

        assert response.body.authenticated is True

    def test_header_api_key_auth_with_incorrect_credentials(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test header API key authentication with incorrect credentials."""
        models = serializer_models
        client_cls = create_client_class(models)

        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.auth_header.url}",
            status_code=401,
        )

        auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="my_api_key")
        client = client_cls()
        with pytest.raises(quickapi.HTTPError) as e:
            client.auth_header(auth=auth)

        assert e.value.status_code == 401


class TestBaseClientWithRequestsLibrary:
    """Test BaseClient with requests library instead of httpx."""

    def test_get_request_with_requests_client(
        self, serializer_models: dict
    ):
        """Test GET request using requests HTTP client."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}

        with responses.RequestsMock() as rsps:
            rsps.add(
                method="GET",
                url=f"{client_cls.base_url}{client_cls.get_facts.url}",
                json=mock_json,
                match=[
                    responses.matchers.query_param_matcher(
                        {"max_length": "100", "limit": "10"}
                    )
                ],
            )

            client = client_cls(http_client=quickapi.RequestsClient())
            response = client.get_facts()

            assert response.body.current_page == 1
            assert response.body.data[0].fact == "Some fact"

    def test_post_request_with_requests_client(
        self, serializer_models: dict
    ):
        """Test POST request using requests HTTP client."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json = {"current_page": 1, "data": [{"fact": "Some fact", "length": 9}]}
        request_body = models["request_body"](some_data="Test body")

        with responses.RequestsMock() as rsps:
            rsps.add(
                method="POST",
                url=f"{client_cls.base_url}{client_cls.post_facts.url}",
                json=mock_json,
                match=[
                    responses.matchers.json_params_matcher(
                        quickapi.DictSerializable.to_dict(request_body)
                    )
                ],
            )

            client = client_cls(http_client=quickapi.RequestsClient())
            response = client.post_facts(request_body=request_body)

            assert response.body.current_page == 1


class TestBaseClientSetupErrors:
    """Test BaseClient setup and configuration errors."""

    def test_invalid_api_endpoint_class(self):
        """Test that invalid API endpoint class raises ClientSetupError."""
        with pytest.raises(quickapi.ClientSetupError):

            class _(quickapi.BaseClient):
                invalid_endpoint = quickapi.ApiEndpoint(object)  # type: ignore [reportArgumentType]

    def test_api_endpoint_not_part_of_base_client(self, serializer_models: dict):
        """Test that API endpoint not attached to client raises AttributeError."""
        models = serializer_models

        class GetApi(quickapi.BaseApi[models["response_body"]]):
            url = "/facts"
            response_body = models["response_body"]

        lone_api_endpoint = quickapi.ApiEndpoint(GetApi)
        with pytest.raises(AttributeError):
            lone_api_endpoint()

    def test_api_endpoint_descriptor_set(self, serializer_models: dict):
        """Test that API endpoint descriptor cannot be set."""
        models = serializer_models
        client_cls = create_client_class(models)

        client = client_cls()
        with pytest.raises(AttributeError):
            client.get_facts = "invalid"

    def test_api_endpoint_descriptor_del(self, serializer_models: dict):
        """Test that API endpoint descriptor cannot be deleted."""
        models = serializer_models
        client_cls = create_client_class(models)

        client = client_cls()
        with pytest.raises(AttributeError):
            del client.get_facts


class TestBaseApiSetupErrors:
    """Test BaseApi setup and configuration errors."""

    def test_should_raise_error_if_no_response_body_specified(
        self, serializer_models: dict
    ):
        """Test that API without response_body raises ApiSetupError."""
        models = serializer_models
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[models["response_body"]]):
                url = "https://example.com/facts"

    def test_should_raise_error_if_invalid_method_specified(
        self, serializer_models: dict
    ):
        """Test that API with invalid method raises ApiSetupError."""
        models = serializer_models
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[models["response_body"]]):
                url = "https://example.com/facts"
                method = "INVALID"  # pyright: ignore [reportAssignmentType]
                response_body = models["response_body"]

    def test_should_raise_error_if_no_generic_type_specified(
        self, serializer_models: dict
    ):
        """Test that API without generic type raises ApiSetupError."""
        models = serializer_models
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi):
                url = "https://example.com/facts"
                response_body = models["response_body"]

    def test_should_raise_error_if_invalid_http_client(self, serializer_models: dict):
        """Test that API with invalid http_client raises ApiSetupError."""
        models = serializer_models
        with pytest.raises(quickapi.ApiSetupError):

            class _(quickapi.BaseApi[models["response_body"]]):
                url = "https://example.com/facts"
                http_client = object()  # pyright: ignore [reportAssignmentType]
                response_body = models["response_body"]


class TestSerializationErrors:
    """Test serialization and validation errors."""

    def test_error_if_response_body_attribute_incorrect_type(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test that incorrect response body type raises ResponseSerializationError."""
        models = serializer_models
        client_cls = create_client_class(models)

        mock_json_incorrect_type = {"current_page": 0, "data": "incorrect_type"}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json_incorrect_type,
        )

        client = client_cls()
        with pytest.raises(quickapi.ResponseSerializationError):
            client.get_facts()

    def test_error_if_response_body_required_attribute_missing(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test that missing required attribute raises ResponseSerializationError.
        
        Note: Dataclasses don't raise errors for missing fields, so this is skipped.
        """
        models = serializer_models
        
        # Skip for dataclasses as it doesn't raise errors for missing fields
        if models["name"] == "dataclasses":
            pytest.skip("Dataclasses don't raise errors for missing required fields")
        
        client_cls = create_client_class(models)

        mock_json_attribute_missing = {"data": []}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json_attribute_missing,
        )

        client = client_cls()
        with pytest.raises(quickapi.ResponseSerializationError):
            client.get_facts()

    def test_response_body_validator(
        self, serializer_models: dict, httpx_mock: HTTPXMock
    ):
        """Test that validator failures raise ResponseSerializationError.
        
        Note: Only attrs and pydantic have validators in our models.
        """
        models = serializer_models
        
        # Skip for serializers without validators
        if models["name"] not in ["attrs", "pydantic"]:
            pytest.skip(f"{models['name']} model doesn't have validators in test setup")
        
        client_cls = create_client_class(models)

        # Test that validator fails for value >= 100
        mock_json_validator_fail = {"current_page": 101, "data": []}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json_validator_fail,
        )

        client = client_cls()
        with pytest.raises(quickapi.ResponseSerializationError):
            client.get_facts()

        # Test that validator passes for value < 100
        mock_json_validator_pass = {"current_page": 99, "data": []}
        httpx_mock.add_response(
            url=f"{client_cls.base_url}{client_cls.get_facts.url}?max_length=100&limit=10",
            json=mock_json_validator_pass,
        )

        response = client.get_facts()
        assert response.body.current_page == 99

