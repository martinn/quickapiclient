from enum import Enum
from typing import TypeAlias

try:
    import httpx
    import requests
except ImportError: ...

# TODO: Fix types
BaseHttpClientAuth: TypeAlias = "httpx.Auth | requests.auth.AuthBase | object | None"
BaseHttpClientResponse: TypeAlias = "httpx.Response | requests.Response"


class BaseHttpMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"

    @staticmethod
    def values() -> dict[str, Enum]:
        return BaseHttpMethod._value2member_map_
