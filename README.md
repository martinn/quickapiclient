# Quick Api Client

[![Release](https://img.shields.io/github/v/release/martinn/quickapiclient)](https://img.shields.io/github/v/release/martinn/quickapiclient)
[![Build status](https://img.shields.io/github/actions/workflow/status/martinn/quickapiclient/main.yml?branch=main)](https://github.com/martinn/quickapiclient/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/martinn/quickapiclient/branch/main/graph/badge.svg)](https://codecov.io/gh/martinn/quickapiclient)

A library for creating fully typed declarative API clients quickly and easily.

- **Github repository**: <https://github.com/martinn/quickapiclient/>
- **Documentation** <https://martinn.github.io/quickapiclient/>

## A quick example

An API definition for a simple service could look like this:

```python
import attrs
import quickapi


# An example type that will be part of the API response
@attrs.define
class Fact:
    fact: str
    length: int


# What the API response should look like
@attrs.define
class ResponseBody(quickapi.BaseResponseBody):
    current_page: int
    data: list[Fact]


# Now we can define our API
class MyApi(quickapi.BaseApi[ResponseBody]):
    url = "https://catfact.ninja/facts"
    response_body = ResponseBody
```

And you would use it like this:

```python
api_client = MyApi()
response = api_client.execute()

# That's it! Now `response` is fully typed and conforms to our `ResponseBody` definition
assert isinstance(response.body, ResponseBody) == True
assert isinstance(response.body.data[0], Fact) == True
```

## Features

It's still early development and this is currently tightly coupled with `httpx` and `attrs`,
but could expand to support others in the future if there's interest.

- Write fully typed declarative API clients quickly and easily
  - [x] Fully typed request params / body
  - [x] Fully typed response body
  - [x] Built in serialization/deserialization with `attrs`
  - [x] Basic error and serialization handling
  - [ ] Nested/inner class definitions
  - [ ] Improved HTTP status codes error handling
  - [ ] Sessions support and/or allow building several related APIs through a single interface
  - [ ] Generate API boilerplate from OpenAPI specs?
- HTTP client libraries
  - [x] httpx
  - [ ] requests
  - [ ] aiohttp
- Authentication mechanisms
  - [x] Basic Auth
  - [x] Token / JWT
  - [x] Digest
  - [x] NetRC
  - [x] Any auth supported by `httpx` or [httpx_auth](https://github.com/Colin-b/httpx_auth), including custom schemes
- Serialization/deserialization
  - [x] attrs
  - [ ] dataclasses
  - [ ] pydantic
- API support
  - [x] REST
  - [ ] GraphQL
  - [ ] Maybe others?
- Response types supported
  - [x] JSON
  - [ ] XML
  - [ ] Others?

## Installation

You can easily install this using `pip`:

```console
pip install quickapiclient
```

Or if using `poetry`:

```console
poetry add quickapiclient
```

## More examples

### A GET request with query params

An example of a GET request with query parameters with overridable default values.

```python
import attrs
import quickapi


@attrs.define
class RequestParams(quickapi.BaseRequestParams):
    max_length: int = 100
    limit: int = 10


@attrs.define
class Fact:
    fact: str
    length: int


@attrs.define
class ResponseBody(quickapi.BaseResponseBody):
    current_page: int
    data: list[Fact]


class MyApi(quickapi.BaseApi[ResponseBody]):
    url = "https://catfact.ninja/facts"
    request_params = RequestParams
    response_body = ResponseBody
```

And to use it:

```python
client = MyApi()
# Using default request param values
response = client.execute()

# Using custom request param values
request_params = RequestParams(max_length=5, limit=10)
response = client.execute(request_params=request_params)
```

### A POST request

An example of a POST request with some optional and required data.

```python
import attrs
import quickapi


@attrs.define
class RequestBody(quickapi.BaseRequestBody):
    required_input: str
    optional_input: str | None = None


@attrs.define
class Fact:
    fact: str
    length: int


@attrs.define
class ResponseBody(quickapi.BaseResponseBody):
    current_page: int
    data: list[Fact]


class MyApi(quickapi.BaseApi[ResponseBody]):
    url = "https://catfact.ninja/facts"
    method = quickapi.BaseApiMethod.POST
    request_body = RequestBody
    response_body = ResponseBody
```

And to use it:

```python
client = MyApi()
request_body = RequestBody(required_input="dummy")
response = client.execute(request_body=request_body)
```

### A POST request with authentication

An example of a POST request with HTTP header API key.

```python
import attrs
import httpx_auth
import quickapi


@attrs.define
class RequestBody(quickapi.BaseRequestBody):
    required_input: str
    optional_input: str | None = None


@attrs.define
class Fact:
    fact: str
    length: int


@attrs.define
class AuthResponseBody(quickapi.BaseResponseBody):
    authenticated: bool
    user: str


class MyApi(quickapi.BaseApi[AuthResponseBody]):
    url = "https://httpbin.org/bearer"
    method = quickapi.BaseApiMethod.POST
    # You could specify it here if you wanted
    # auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="secret_api_key")
    response_body = AuthResponseBody
```

And to use it:

```python
client = MyApi()
request_body = RequestBody(required_input="dummy")
auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="secret_api_key")
response = client.execute(request_body=request_body, auth=auth)
```

### A POST request with validation and conversion

An example of a POST request with custom validators and converters (from `attrs`).

```python
import attrs
import quickapi
import enum


class State(enum.Enum):
    ON = "on"
    OFF = "off"


@attrs.define
class RequestBody(quickapi.BaseRequestBody):
    state: State = attrs.field(validator=attrs.validators.in_(State))
    email: str = attrs.field(
        validator=attrs.validators.matches_re(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        )
    )


@attrs.define
class ResponseBody(quickapi.BaseResponseBody):
    success: bool = attrs.field(converter=attrs.converters.to_bool)


class MyApi(quickapi.BaseApi[ResponseBody]):
    url = "https://example.com/"
    method = quickapi.BaseApiMethod.POST
    request_body = RequestBody
    response_body = ResponseBody
```

And to use it:

```python
client = MyApi()
request_body = RequestBody(email="invalid_email", state="on") # Will raise an error
response = client.execute(request_body=request_body)
```

Check out [attrs](https://github.com/python-attrs/attrs) for full configuration.

## Contributing

Contributions are welcomed, and greatly appreciated!

If you want to contribute, check out the
[contributing guide](./CONTRIBUTING.md) to get started.
