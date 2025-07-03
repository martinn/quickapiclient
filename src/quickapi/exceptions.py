from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from quickapi.http_clients.types import BaseHttpClientResponse
    from quickapi.serializers.types import DictSerializableT


class QuickApiException(Exception):
    """A QuickApi exception has occurred."""


class ClientSetupError(QuickApiException):
    """An error setting up the `BaseClient` subclass."""

    def __init__(self, attribute: str):
        message = (
            f"Client setup error. Missing or invalid required attribute `{attribute}`."
        )
        super().__init__(message)


class ApiSetupError(QuickApiException):
    """An error setting up the `BaseApi` subclass."""

    def __init__(self, attribute: str):
        message = (
            f"Api setup error. Missing or invalid required attribute `{attribute}`."
        )
        super().__init__(message)


class HTTPError(QuickApiException):
    """The response received a non `200` response status code."""

    status_code: int
    body: "str"

    def __init__(
        self,
        client_response: "BaseHttpClientResponse",
        status_code: int,
        body: "str",
    ):
        message = f"HTTP request received a non `HTTP 200 (OK)` response. The response status code was `{status_code}`."
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class HandledHTTPError(QuickApiException):
    """The response received a non `200` response status code that we can handle."""

    status_code: int
    body: "DictSerializableT"

    def __init__(
        self,
        client_response: "BaseHttpClientResponse",
        status_code: int,
        body: "DictSerializableT",
    ):
        message = f"HTTP request received a non `HTTP 200 (OK)` response. The response status code was `{status_code}`."
        self.status_code = status_code
        self.body = body
        super().__init__(message)


class DictSerializationError(QuickApiException):
    """Dict serialization failed."""

    expected_type = ""
    specific_serializer: Any | None = None

    def __init__(self, expected_type: str, specific_serializer: Any = None):
        self.expected_type = expected_type
        self.specific_serializer = specific_serializer
        message = f"Could not serialize to {expected_type}"
        if specific_serializer:
            message += f" using {specific_serializer.__name__}"
        super().__init__(message)


class DictDeserializationError(QuickApiException):
    """Dict deserialization failed."""

    expected_type = ""
    specific_deserializer: Any | None = None

    def __init__(self, expected_type: str, specific_deserializer: Any = None):
        self.expected_type = expected_type
        self.specific_deserializer = specific_deserializer
        message = f"Could not deserialize {expected_type} to dict"
        if specific_deserializer:
            message += f" using {specific_deserializer.__name__}"
        super().__init__(message)


class ResponseSerializationError(QuickApiException):
    """The response received was not serializable to the configured `response_body` type."""

    def __init__(self, expected_type: str):
        message = f"HTTP response body did not match expected type `{expected_type}`."
        super().__init__(message)


class RequestSerializationError(QuickApiException):
    """The request was not serializable to the configured type."""

    def __init__(self, expected_type: str):
        message = (
            f"HTTP request params/body did not match expected type `{expected_type}`."
        )
        super().__init__(message)


class MissingDependencyError(QuickApiException):
    """Trying to use an optional dependency without installing it first."""

    def __init__(self, dependency: str):
        message = (
            f"Using an optional dependecy without installing it first `{dependency}`."
            f"Please install the dependency using `pip install quickapiclient[{dependency}]`."
        )
        super().__init__(message)
