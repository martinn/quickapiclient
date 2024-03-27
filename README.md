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
from dataclasses import dataclass
import quickapi


# An example type that will be part of the API response
@dataclass
class Fact:
    fact: str
    length: int


# What the API response should look like
@dataclass
class ResponseBody:
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
assert isinstance(response.body, ResponseBody)
assert isinstance(response.body.data[0], Fact)
```

There's also support for `attrs` or `pydantic` for more complex modeling, validation or serialization support.

Scroll down [here](#a-post-request-with-validation-and-conversion-using-attrs) for examples using those.

## Features

It's still early development but so far we have support for:

- Write fully typed declarative API clients quickly and easily
  - [x] Fully typed request params / body
  - [x] Fully typed response body
  - [x] Serialization/deserialization support
  - [x] Basic error and serialization handling
  - [ ] Nested/inner class definitions
  - [ ] Improved HTTP status codes error handling
  - [ ] Sessions support and/or allow building several related APIs through a single interface
  - [ ] Generate API boilerplate from OpenAPI specs
  - [ ] Full async support
- HTTP client libraries
  - [x] httpx
  - [x] requests
  - [ ] aiohttp
- Authentication mechanisms
  - [x] Basic Auth
  - [x] Token / JWT
  - [x] Digest
  - [x] NetRC
  - [x] Any auth supported by `httpx` or [httpx_auth](https://github.com/Colin-b/httpx_auth) or `requests`, including custom schemes
- Serialization/deserialization
  - [x] attrs
  - [x] dataclasses
  - [x] pydantic
- API support
  - [x] REST
  - [ ] GraphQL
  - [ ] Others?
- Response types supported
  - [x] JSON
  - [ ] XML
  - [ ] Others?

## Goal

Eventually, I would like for the API definition to end up looking more like this (though the current approach will still be supported):

```python
import quickapi


@quickapi.define
class MyApi:
    url = "https://catfact.ninja/facts"
    method = quickapi.BaseApiMethod.POST

    class RequestBody:
        required_input: str
        optional_input: str | None = None

    class ResponseBody:
        current_page: int
        data: list[Fact]
```

And also to be able to support multiple endpoints per API client.

## Installation

You can easily install this using `pip`:

```console
pip install quickapiclient
# Or if you want to use `attrs` over `dataclasses`:
pip install quickapiclient[attrs]
# Or if you want to use `pydantic` over `dataclasses`:
pip install quickapiclient[pydantic]
# Or if you want to use `requests` over `httpx`:
pip install quickapiclient[requests]
```

Or if using `poetry`:

```console
poetry add quickapiclient
# Or if you want to use `attrs` over `dataclasses`:
poetry add quickapiclient[attrs]
# Or if you want to use `pydantic` over `dataclasses`:
poetry add quickapiclient[pydantic]
# Or if you want to use `requests` over `httpx`:
poetry add quickapiclient[requests]
```

## More examples

### A GET request with query params

An example of a GET request with query parameters with overridable default values.

```python
from dataclasses import dataclass
import quickapi


@dataclass
class RequestParams:
    max_length: int = 100
    limit: int = 10


@dataclass
class Fact:
    fact: str
    length: int


@dataclass
class ResponseBody:
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
from dataclasses import dataclass
import quickapi


@dataclass
class RequestBody:
    required_input: str
    optional_input: str | None = None


@dataclass
class Fact:
    fact: str
    length: int


@dataclass
class ResponseBody:
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
from dataclasses import dataclass
import httpx_auth
import quickapi


@dataclass
class RequestBody:
    required_input: str
    optional_input: str | None = None


@dataclass
class Fact:
    fact: str
    length: int


@dataclass
class AuthResponseBody:
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

### A POST request with validation and conversion (Using `attrs`)

An example of a POST request with custom validators and converters (using `attrs` instead).

```python
import attrs
import quickapi
import enum


class State(enum.Enum):
    ON = "on"
    OFF = "off"


@attrs.define
class RequestBody:
    state: State = attrs.field(validator=attrs.validators.in_(State))
    email: str = attrs.field(
        validator=attrs.validators.matches_re(
            r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        )
    )


@attrs.define
class ResponseBody:
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

### A POST request with validation and conversion (Using `pydantic`)

An example of a POST request with custom validators and converters (using `pydantic` instead).

```python
import enum
import pydantic
import quickapi


class State(enum.Enum):
    ON = "on"
    OFF = "off"


class RequestBody(pydantic.BaseModel):
    state: State
    email: pydantic.EmailStr


class ResponseBody(pydantic.BaseModel):
    success: bool


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

Check out [pydantic](https://github.com/pydantic/pydantic) for full configuration.

### Using `requests` library

An example of a GET request using the `requests` HTTP library instead of `HTTPx`.

```python
from dataclasses import dataclass
import quickapi


@dataclass
class ResponseBody:
    current_page: int
    data: list[Fact]


class MyApi(quickapi.BaseApi[ResponseBody]):
    url = "https://catfact.ninja/facts"
    response_body = ResponseBody
    http_client = quickapi.RequestsClient()
```

And to use it:

```python
client = MyApi()
response = client.execute()
```

## Contributing

Contributions are welcomed, and greatly appreciated!

The easiest way to contribute, if you found this useful or interesting,
is by giving it a star! 🌟

Otherwise, check out the
[contributing guide](./CONTRIBUTING.md) for how else to help and get started.
