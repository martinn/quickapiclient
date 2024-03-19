from contextlib import suppress

from .client import (  # noqa: F401
    BaseApi,
    BaseApiMethod,
    BaseRequestBody,
    BaseRequestParams,
    BaseResponseBody,
    ClientSetupError,
    HTTPError,
    ResponseSerializationError,
)
from .exceptions import QuickApiException  # noqa: F401
from .http_client import BaseHttpClient, HTTPxClient  # noqa: F401

with suppress(ImportError):
    from .http_client import RequestsClient  # noqa: F401
