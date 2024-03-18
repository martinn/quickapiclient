class QuickApiException(Exception):
    """A QuickApi exception has occurred."""


class ClientSetupError(QuickApiException):
    """An error setting up the BaseClient subclass."""

    def __init__(self, attribute: str):
        message = f"Subclass setup error. Missing or invalid required attribute `{attribute}`."
        super().__init__(message)


class HTTPError(QuickApiException):
    """The response received a non `200` response status code."""

    def __init__(self, status_code: int):
        message = f"HTTP request received a non `HTTP 200 (OK)` response. The response status code was `{status_code}`."
        super().__init__(message)


class ResponseSerializationError(QuickApiException):
    """The response received was not serializable to the configured `response_body` type."""

    def __init__(self, expected_type: str):
        message = f"HTTP response body did not match expected type `{expected_type}`."
        super().__init__(message)
