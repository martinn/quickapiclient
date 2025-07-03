::: quickapi.serializers.base

## Configuring a Default (De)serializer

By default, `quickapi` iterates through a list of available (de)serializers (Dataclass, Attrs, Pydantic, Msgspec) to find one that can handle your data model for request and response bodies.

You can now configure a specific (de)serializer to be used by setting the `default_serializer` attribute on either a `BaseClient` or a `BaseApi` class.

- If set on `BaseClient`, all API endpoints under that client will attempt to use this (de)serializer first.
- If set on `BaseApi`, it will use that specific (de)serializer, overriding any configuration from the client.

The `default_serializer` attribute should be set to a (de)serializer *class*, for example:

```python
from quickapi import BaseClient, BaseApi, ApiEndpoint
from quickapi.serializers.dataclass import DataclassSerializer, DataclassDeserializer
# or from quickapi.serializers.pydantic import PydanticSerializer, PydanticDeserializer
# etc.

# Example Data Model
import dataclasses

@dataclasses.dataclass
class MyData:
    id: int
    name: str

# Option 1: Configure on the Client
class MyApiClient(BaseClient):
    base_url = "https://api.example.com"
    # Use DataclassSerializer for responses (from_dict)
    # and DataclassDeserializer for requests (to_dict)
    # If your chosen serializer handles both, you can just pass that one.
    # For this example, let's assume we want to be specific:
    # default_serializer = DataclassSerializer # If only for responses
    # default_serializer = DataclassDeserializer # If only for requests
    # For QuickAPI, you'd typically pass the one relevant to the operation.
    # The BaseApi will determine whether to use it as a serializer or deserializer.
    # For simplicity, if a serializer can also deserialize or vice-versa,
    # you might only need to ensure the correct type is passed.
    # However, the system expects BaseSerializer for from_dict (responses)
    # and BaseDeserializer for to_dict (requests).
    # For example, if this client primarily handles GET requests where response
    # deserialization is key, you might set a default BaseSerializer.
    # If it primarily handles POST/PUT, a BaseDeserializer might be more relevant.
    # If an endpoint under this client needs the other type, it can specify it.
    default_serializer = DataclassSerializer # For response bodies (from_dict)


class GetMyDataApi(BaseApi[MyData]):
    url = "/mydata/{id}"
    response_body = MyData

MyApiClient.get_data = ApiEndpoint(GetMyDataApi)

# Option 2: Configure on the API (takes precedence)
class UpdateMyDataApi(BaseApi[MyData]):
    url = "/mydata/{id}"
    method = "PUT"
    request_body = MyData
    response_body = MyData
    # This API will use DataclassDeserializer for its request_body (to_dict operation),
    # overriding any client-level default_serializer.
    # For its response_body (from_dict operation), if this was different or if
    # DataclassDeserializer couldn't also handle from_dict, it would fall back or error
    # if no suitable serializer is found. (Note: current built-in (de)serializers are separate)
    default_serializer = DataclassDeserializer # For request bodies (to_dict)

class MyOtherClient(BaseClient):
    base_url = "https://api.example.com"
    # Client might have its own default or no default
    update_data = ApiEndpoint(UpdateMyDataApi)

```

If the configured `default_serializer` `can_apply` to the data model but fails during the actual (de)serialization process, an error will be raised immediately. If it `can_apply` returns `False` (e.g. you provided a `BaseSerializer` type but a `BaseDeserializer` was needed for the operation, or vice-versa), `quickapi` will fall back to iterating through its standard list of (de)serializers.

The `ConfigurableSerializer` type is `Union[Type[BaseSerializer], Type[BaseDeserializer]]`.
When (de)serializing:
- For request parameters and bodies (converting an object to a `dict`), the system checks if the `default_serializer` is a subclass of `BaseDeserializer`.
- For response bodies (converting a `dict` to an object), the system checks if the `default_serializer` is a subclass of `BaseSerializer`.

You must provide the correct type of (de)serializer class for the operation you intend to customize. For instance, to customize how response dictionaries are turned into objects, provide a `BaseSerializer` subclass (like `DataclassSerializer`). To customize how request objects are turned into dictionaries, provide a `BaseDeserializer` subclass (like `DataclassDeserializer`).


# Dataclasses

::: quickapi.serializers.dataclass

# Attrs

::: quickapi.serializers.attrs

# Pydantic

::: quickapi.serializers.pydantic

# Msgspec

::: quickapi.serializers.msgspec
