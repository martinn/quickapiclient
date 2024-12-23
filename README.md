# Quick Api Client

[![Release](https://img.shields.io/github/v/release/martinn/quickapiclient)](https://img.shields.io/github/v/release/martinn/quickapiclient)
[![Build status](https://img.shields.io/github/actions/workflow/status/martinn/quickapiclient/main.yml?branch=main)](https://github.com/martinn/quickapiclient/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/martinn/quickapiclient/branch/main/graph/badge.svg)](https://codecov.io/gh/martinn/quickapiclient)

A library for creating fully typed declarative API clients quickly and easily.

- **Github repository**: <https://github.com/martinn/quickapiclient/>
- **Documentation** <https://martinn.github.io/quickapiclient/>

## A basic example

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


# We define an API endpoint
class GetFactsApi(quickapi.BaseApi[ResponseBody]):
    url = "/facts"
    response_body = ResponseBody


# And now our API client
class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    get_facts = quickapi.ApiEndpoint(GetFactsApi)
    # Other endpoints would follow here:
    # submit_fact = quickapi.ApiEndpoint(SubmitFactApi)
```

And you would use it like this:

```python
client = ExampleClient()
response = client.get_facts()

# `response` is fully typed and conforms to our `ResponseBody` definition
assert isinstance(response.body, ResponseBody)
assert isinstance(response.body.data[0], Fact)

# `reveal_type(response.body)` returns `Revealed type is 'ResponseBody'` too,
# which means full typing and IDE support.
```

There's also support for `attrs`, `pydantic` and `msgspec` for more complex modeling, validation or serialization support.

Scroll down [here](#a-post-request-with-validation-and-conversion-using-attrs) for examples using those.

## Features

It's still early development but so far we have support for:

- Write fully typed declarative API clients quickly and easily
  - [x] Fully typed request params / body
  - [x] Fully typed response body
  - [x] Serialization/deserialization support
  - [x] Basic error and serialization handling
  - [x] Fully typed HTTP status error codes handling
  - [ ] Nested/inner class definitions
  - [ ] Generate API boilerplate from OpenAPI specs
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
  - [x] msgspec
- API support
  - [x] REST
  - [ ] GraphQL
  - [ ] Others?
- Response types supported
  - [x] JSON
  - [ ] XML
  - [ ] Others?

## Installation

You can easily install this using `pip` or your favourite package manager:

```console
pip install quickapiclient
# Or with optional extras (choose from the list below)
pip install quickapiclient[attrs,pydantic,msgspec,requests]
# Or if using poetry
poetry add quickapiclient
poetry add quickapiclient[attrs,pydantic,msgspec,requests]
# Or if using uv
uv add quickapiclient
uv add quickapiclient[attrs,pydantic,msgspec,requests]
```

## More examples

### A GET request with query params

An example of a GET request with query parameters with overridable default values.

<details>
<summary>Click to expand</summary>

```python
# ...

@dataclass
class RequestParams:
    max_length: int = 100
    limit: int = 10


class GetFactsApi(quickapi.BaseApi[ResponseBody]):
    url = "/facts"
    request_params = RequestParams
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    get_facts = quickapi.ApiEndpoint(GetFactsApi)
```

And to use it:

```python
client = ExampleClient()
# Using default request param values
response = client.get_facts()

# Using custom request param values
request_params = RequestParams(max_length=5, limit=10)
response = client.get_facts(request_params=request_params)
```

</details>

### A POST request

An example of a POST request with some optional and required data.

<details>
<summary>Click to expand</summary>

```python
# ...

@dataclass
class RequestBody:
    required_input: str
    optional_input: str | None = None


@dataclass
class SubmitResponseBody:
    success: bool
    message: str


class SubmitFactApi(quickapi.BaseApi[SubmitResponseBody]):
    url = "/facts/new"
    method = quickapi.BaseHttpMethod.POST
    request_body = RequestBody
    response_body = SubmitResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    get_facts = quickapi.ApiEndpoint(GetFactsApi)
    submit_fact = quickapi.ApiEndpoint(SubmitFactApi)
```

And to use it:

```python
client = ExampleClient()
request_body = RequestBody(required_input="dummy")
response = client.submit_fact(request_body=request_body)
```

</details>

### A POST request with authentication

An example of a POST request with HTTP header API key.

<details>
<summary>Click to expand</summary>

```python
import httpx_auth

# ...

class SubmitFactApi(quickapi.BaseApi[SubmitResponseBody]):
    url = "/facts/new"
    method = quickapi.BaseHttpMethod.POST
    # Specify it here if you want all requests to this endpoint to have auth
    # auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="secret_api_key")
    request_body = RequestBody
    response_body = SubmitResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    # Specify it here if you want requests to all of this clients' endpoints to have auth
    # auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="secret_api_key")
    get_facts = quickapi.ApiEndpoint(GetFactsApi)
    submit_fact = quickapi.ApiEndpoint(SubmitFactApi)
```

And to use it:

```python
auth = httpx_auth.HeaderApiKey(header_name="X-Api-Key", api_key="secret_api_key")
client = ExampleClient(
  # Specify it here to have auth for all apis on this client instance only
  # auth=auth
)
request_body = RequestBody(required_input="dummy")
response = client.submit_fact(
  request_body=request_body,
  # Or here to have auth just for this api request
  auth=auth
)
```

</details>

### A POST request with error handling

An example of a POST request that handles HTTP error codes too.

<details>
<summary>Click to expand</summary>

```python
# ...

@dataclass
class ResponseError401:
    status: str
    message: str


class SubmitFactApi(quickapi.BaseApi[SubmitResponseBody]):
    url = "/facts/new"
    method = quickapi.BaseHttpMethod.POST
    response_body = ResponseBody
    # Add more types for each HTTP status code you wish to handle
    response_errors = {401: ResponseError401}


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    submit_fact = quickapi.ApiEndpoint(SubmitFactApi)
```

And to use it:

```python
client = ExampleClient()
request_body = RequestBody(required_input="dummy")

try:
    response = client.submit_fact(request_body=request_body)
except quickapi.HTTPError as e:
    match e.value.status_code:
        case 401:
            assert isinstance(e.value.body, ResponseError401)
            print(f"Received {e.value.body.status} with {e.value.body.message}")
        case _:
            print("Unhandled error occured.")
```

</details>

### A POST request with validation and conversion (Using `attrs`)

An example of a POST request with custom validators and converters (using `attrs` instead).

<details>
<summary>Click to expand</summary>

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


class SubmitApi(quickapi.BaseApi[ResponseBody]):
    url = "/submit"
    method = quickapi.BaseHttpMethod.POST
    request_body = RequestBody
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    submit = quickapi.ApiEndpoint(SubmitApi)
```

And to use it:

```python
client = ExampleClient()
request_body = RequestBody(email="invalid_email", state="on") # Will raise an error
response = client.submit(request_body=request_body)
```

Check out [attrs](https://github.com/python-attrs/attrs) for full configuration.

</details>

### A POST request with validation and conversion (Using `pydantic`)

An example of a POST request with custom validators and converters (using `pydantic` instead).

<details>
<summary>Click to expand</summary>

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


class SubmitApi(quickapi.BaseApi[ResponseBody]):
    url = "/submit"
    method = quickapi.BaseHttpMethod.POST
    request_body = RequestBody
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    submit = quickapi.ApiEndpoint(SubmitApi)
```

And to use it:

```python
client = ExampleClient()
request_body = RequestBody(email="invalid_email", state="on") # Will raise an error
response = client.submit(request_body=request_body)
```

Check out [pydantic](https://github.com/pydantic/pydantic) for full configuration.

</details>

### A POST request with validation and conversion (Using `msgspec`)

An example of a POST request with custom validators and converters (using `msgspec` instead).

<details>
<summary>Click to expand</summary>

```python
import enum
from typing import Annotated

import msgspec
import quickapi



class State(enum.Enum):
    ON = "on"
    OFF = "off"


class RequestBody(msgspec.Struct):
    state: State
    email: str = Annotated[str, msgspec.Meta(pattern=r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')]


class ResponseBody(msgspec.Struct):
    success: bool


class SubmitApi(quickapi.BaseApi[ResponseBody]):
    url = "/submit"
    method = quickapi.BaseHttpMethod.POST
    request_body = RequestBody
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient):
    base_url = "https://example.com"
    submit = quickapi.ApiEndpoint(SubmitApi)
```

And to use it:

```python
client = ExampleClient()
request_body = RequestBody(email="invalid_email", state="on") # Will raise an error
response = client.submit(request_body=request_body)
```

</details>

### Using `requests` library

An example of a GET request using the `requests` HTTP library instead of `HTTPx`.

<details>
<summary>Click to expand</summary>

```python
from dataclasses import dataclass
import quickapi



@dataclass
class ResponseBody:
    current_page: int
    data: list[Fact]


class GetFactsApi(quickapi.BaseApi[ResponseBody]):
    url = "/facts"
    response_body = ResponseBody


class ExampleClient(quickapi.BaseClient)
    base_url = "https://example.com"
    http_client = quickapi.RequestsClient()
    get_facts = quickapi.ApiEndpoint(GetFactsApi)
```

And to use it:

```python
client = ExampleClient()
response = client.get_facts()
```

</details>

## Goal

Eventually, I would like for the API client definition to end up looking more like this:

<details>
<summary>Click to expand</summary>

```python
import quickapi


@quickapi.api
class FetchApi:
    url = "/fetch"
    method = quickapi.BaseHttpMethod.GET

    class ResponseBody:
        current_page: int
        data: list[Fact]


@quickapi.api
class SubmitApi:
    url = "/submit"
    method = quickapi.BaseHttpMethod.POST

    class RequestBody:
        required_input: str
        optional_input: str | None = None

    class ResponseBody:
        success: bool
        message: str


@quickapi.client
class MyClient:
    base_url = "https://example.com"
    fetch = quickapi.ApiEndpoint(FetchApi)
    submit = quickapi.ApiEndpoint(SubmitApi)


client = MyClient(auth=...)
response = client.fetch()
response = client.submit(request_body=RequestBody(...))
```

</details>

## Contributing

Contributions are welcomed, and greatly appreciated!

The easiest way to contribute, if you found this useful or interesting,
is by giving it a star! 🌟

Otherwise, check out the
[contributing guide](./CONTRIBUTING.md) for how else to help and get started.
