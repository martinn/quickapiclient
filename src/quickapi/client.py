from typing import Any, Generic, NoReturn, overload

from typing_extensions import Self

from quickapi.api import USE_DEFAULT, BaseApi, BaseResponse, ResponseBodyT
from quickapi.exceptions import ClientSetupError
from quickapi.http_clients import BaseHttpClient, BaseHttpClientAuth, HTTPxClient
from quickapi.serializers import DictSerializableT


class BaseClient:
    """
    Base class for all API clients.

    Subclass from `BaseClient` and define appropriate attributes from
    the list below to create your own API client.

    By default, all API client endpoints will share the same auth mechanism
    and HTTP client. This can be overridden on a per-endpoint basis if needed.

    Attributes:
        base_url: The base URL that all API endpoints will use.
        auth: Optional authentication to be used across all API endpoints.
            Can be any class supported by the HTTP client.
        http_client: Optional HTTP client to be used across all API endpoints
            if not using the default (HTTPx). Or if wanting to customize the
            default client.

    Raises:
        ClientSetupError: If the class attributes are not correctly defined.

    Examples:
        A very basic example of an API client definition:

        ```python
        import quickapi


        @dataclass
        class ResponseBody:
            current_page: int
            data: list[str]


        class GetFactsApi(quickapi.BaseApi[ResponseBody]):
            url = "/facts"
            response_body = ResponseBody


        class MyClient(quickapi.BaseClient):
            base_url = "https://example.com"
            get_facts = quickapi.ApiEndpoint(GetFactsApi)
        ```

        Which can be used like this:

        ```python
        client = MyClient()
        response = api.get_facts()
        assert isinstance(response.body, ResponseBody)
        ```
    """

    base_url: str | object | None = None
    auth: BaseHttpClientAuth = None
    http_client: BaseHttpClient | None = HTTPxClient()

    def __init__(
        self,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
        base_url: str | object = USE_DEFAULT,
    ):
        self.http_client = http_client or self.http_client
        self.auth = auth if auth != USE_DEFAULT else self.auth
        self.base_url = base_url if base_url != USE_DEFAULT else self.base_url


class ApiEndpoint(Generic[ResponseBodyT]):
    """
    Descriptor for defining API endpoints on a client.

    Allows us to share state (like auth or HTTP client) between API endpoints
    of the same client.

    See `BaseClient` for an example of how to use this.
    """

    def __init__(self, cls: type[BaseApi[ResponseBodyT]]):
        self._api: BaseApi[ResponseBodyT] | None = None
        self._api_cls = cls

        if self._api_cls is not None and not (issubclass(self._api_cls, BaseApi)):
            raise ClientSetupError(attribute="cls")

    def __set_name__(self, owner: type[BaseClient] | None, field_name: str) -> None:
        self._field_name = field_name

    @overload
    def __get__(
        self, instance: None, owner: type[BaseClient] | None
    ) -> type[BaseApi[ResponseBodyT]]: ...

    @overload
    def __get__(self, instance: BaseClient, owner: type[BaseClient] | None) -> Self: ...

    def __get__(self, instance, owner):  # type: ignore [no-untyped-def]
        if instance is None:
            # Client has not been initialized, return the API class.
            return self._api_cls

        if self._api is None:
            # If client has been initialized, also initialize the API class.
            self._api = self._api_cls(
                base_url=instance.base_url,
                http_client=instance.http_client,
                auth=instance.auth,
            )

        return self

    def __call__(
        self,
        request_params: "DictSerializableT | None" = None,
        request_body: "DictSerializableT | None" = None,
        http_client: BaseHttpClient | None = None,
        auth: BaseHttpClientAuth = USE_DEFAULT,
    ) -> BaseResponse[ResponseBodyT]:
        if self._api is None:
            raise AttributeError("API endpoint not part of a `BaseClient` instance.")  # noqa: TRY003

        return self._api.execute(
            request_params=request_params,
            request_body=request_body,
            http_client=http_client,
            auth=auth,
        )

    def __set__(self, instance: BaseClient, value: Any) -> NoReturn:
        raise AttributeError(  # noqa: TRY003
            f"`{self._field_name}` is read-only and cannot be modified.",
            name=self._field_name,
        )

    def __delete__(self, instance: BaseClient) -> NoReturn:
        raise AttributeError(  # noqa: TRY003
            f"`{self._field_name}` is read-only and cannot be deleted.",
            name=self._field_name,
        )
