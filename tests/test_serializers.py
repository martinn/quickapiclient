import dataclasses
from typing import Any, ClassVar
from unittest.mock import MagicMock

import attrs
import msgspec
import pydantic
import pytest

from quickapi import (
    BaseApi,
    BaseClient,
    ApiEndpoint,
    DictDeserializationError,
    DictSerializable,
    DictSerializationError,
)
from quickapi.serializers.base import BaseSerializer, BaseDeserializer
from quickapi.serializers.types import DictSerializableT, FromDictSerializableT


@dataclasses.dataclass
class DataclassFact:
    fact: str
    length: int


@dataclasses.dataclass
class DataclassComplexModel:
    current_page: int
    data: list[DataclassFact] = dataclasses.field(default_factory=list)


@attrs.define
class AttrsFact:
    fact: str
    length: int


@attrs.define
class AttrsComplexModel:
    current_page: int = attrs.field(validator=attrs.validators.lt(100))
    data: list[AttrsFact] = attrs.field(factory=list)


class PydanticFact(pydantic.BaseModel):
    fact: str
    length: int


class PydanticComplexModel(pydantic.BaseModel):
    current_page: int = pydantic.Field(lt=100)
    data: list[PydanticFact] = pydantic.Field(default_factory=list)


class MsgspecFact(msgspec.Struct):
    fact: str
    length: int


class MsgspecComplexModel(msgspec.Struct):
    current_page: int
    data: list[MsgspecFact] = msgspec.field(default_factory=list)


class TestSerializers:
    simple_model: ClassVar = {"fact": "fact", "length": 4}
    complex_model: ClassVar = {"current_page": 1, "data": [simple_model]}
    invalid_model: ClassVar = {"current_page": "not_int", "data": 9}

    @pytest.mark.parametrize(
        "input_data",
        [
            DataclassFact(**simple_model),
            AttrsFact(**simple_model),
            PydanticFact(**simple_model),
            MsgspecFact(**simple_model),
        ],
    )
    def test_to_and_from_simple_model(self, input_data):
        assert DictSerializable.to_dict(input_data) == self.simple_model
        assert (
            DictSerializable.from_dict(type(input_data), self.simple_model)
            == input_data
        )

    @pytest.mark.parametrize(
        "input_data",
        [
            DataclassComplexModel(current_page=1, data=[DataclassFact(**simple_model)]),
            AttrsComplexModel(current_page=1, data=[AttrsFact(**simple_model)]),
            PydanticComplexModel(current_page=1, data=[PydanticFact(**simple_model)]),
            MsgspecComplexModel(current_page=1, data=[MsgspecFact(**simple_model)]),
        ],
    )
    def test_to_and_from_complex_model(self, input_data):
        assert DictSerializable.to_dict(input_data) == self.complex_model
        assert (
            DictSerializable.from_dict(type(input_data), self.complex_model)
            == input_data
        )

    @pytest.mark.parametrize(
        "instance",
        [
            object(),
            # All other serializers will require a valid instance to start with
        ],
    )
    def test_to_dict_with_invalid_input(self, instance):
        with pytest.raises(DictDeserializationError):
            DictSerializable.to_dict(instance)

    @pytest.mark.parametrize(
        "klass, input_data",
        [
            (DataclassComplexModel, invalid_model),
            (AttrsComplexModel, invalid_model),
            (PydanticComplexModel, invalid_model),
            (MsgspecComplexModel, invalid_model),
            (object, invalid_model),
        ],
    )
    def test_from_dict_with_invalid_input(self, klass, input_data):
        with pytest.raises(DictSerializationError):
            DictSerializable.from_dict(klass, input_data)


@dataclasses.dataclass
class TestData:
    value: str


# Mock Serializers for testing configurability
class MockSerializer(BaseSerializer):
    can_apply_mock = MagicMock(return_value=True)
    from_dict_mock = MagicMock(return_value=TestData(value="serialized_by_mock"))

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return cls.can_apply_mock(klass)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        return cls.from_dict_mock(klass, values)


class MockDeserializer(BaseDeserializer):
    can_apply_mock = MagicMock(return_value=True)
    to_dict_mock = MagicMock(return_value={"value": "deserialized_by_mock"})

    @classmethod
    def can_apply(cls, instance: DictSerializableT) -> bool:
        return cls.can_apply_mock(instance)

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        return cls.to_dict_mock(instance)


class FailingSerializer(BaseSerializer):
    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return True

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        raise ValueError("FailingSerializer failed as expected")


class FailingDeserializer(BaseDeserializer):
    @classmethod
    def can_apply(cls, instance: DictSerializableT) -> bool:
        return True

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        raise ValueError("FailingDeserializer failed as expected")


class TestConfigurableSerializers:
    @pytest.fixture(autouse=True)
    def reset_mocks(self):
        MockSerializer.can_apply_mock.reset_mock()
        MockSerializer.from_dict_mock.reset_mock()
        MockDeserializer.can_apply_mock.reset_mock()
        MockDeserializer.to_dict_mock.reset_mock()

    def test_client_defined_serializer_used_for_response(self):
        class TestClientApi(BaseApi[TestData]):
            response_body = TestData
            url = "/test"

        class MyClient(BaseClient):
            base_url = "http://example.com"
            default_serializer = MockSerializer
            test_endpoint = ApiEndpoint(TestClientApi)

        client = MyClient()
        # We are testing DictSerializable directly, not the full HTTP call
        # So we call _parse_response_body which uses from_dict
        api_instance = client.test_endpoint._api
        api_instance._parse_response_body(TestData, {"value": "test"})

        MockSerializer.can_apply_mock.assert_called_once_with(TestData)
        MockSerializer.from_dict_mock.assert_called_once_with(TestData, {"value": "test"})

    def test_client_defined_deserializer_used_for_request(self):
        class TestClientApi(BaseApi[TestData]):
            request_body = TestData # For to_dict
            response_body = TestData
            url = "/test"

        class MyClient(BaseClient):
            base_url = "http://example.com"
            default_serializer = MockDeserializer # For to_dict
            test_endpoint = ApiEndpoint(TestClientApi)

        client = MyClient()
        api_instance = client.test_endpoint._api
        test_data_instance = TestData(value="test_request")
        api_instance._parse_request_body(test_data_instance)

        MockDeserializer.can_apply_mock.assert_called_once_with(test_data_instance)
        MockDeserializer.to_dict_mock.assert_called_once_with(test_data_instance)

    def test_api_defined_serializer_overrides_client_response(self):
        class MockSerializerClient(BaseSerializer): # Different mock
            can_apply_mock = MagicMock(return_value=True)
            from_dict_mock = MagicMock()
            @classmethod
            def can_apply(cls, k: type[FromDictSerializableT]) -> bool: return cls.can_apply_mock(k)
            @classmethod
            def from_dict(cls, k: type[FromDictSerializableT], v: dict) -> FromDictSerializableT: return cls.from_dict_mock(k,v)

        class TestApiOverridesClient(BaseApi[TestData]):
            response_body = TestData
            url = "/test"
            default_serializer = MockSerializer # API's own serializer

        class MyClientWithSerializer(BaseClient):
            base_url = "http://example.com"
            default_serializer = MockSerializerClient # Client's serializer
            test_endpoint = ApiEndpoint(TestApiOverridesClient)

        client = MyClientWithSerializer()
        api_instance = client.test_endpoint._api
        api_instance._parse_response_body(TestData, {"value": "override_test"})

        MockSerializer.can_apply_mock.assert_called_once_with(TestData)
        MockSerializer.from_dict_mock.assert_called_once_with(TestData, {"value": "override_test"})
        MockSerializerClient.can_apply_mock.assert_not_called()
        MockSerializerClient.from_dict_mock.assert_not_called()

    def test_api_defined_deserializer_overrides_client_request(self):
        class MockDeserializerClient(BaseDeserializer): # Different mock
            can_apply_mock = MagicMock(return_value=True)
            to_dict_mock = MagicMock()
            @classmethod
            def can_apply(cls, i: DictSerializableT) -> bool: return cls.can_apply_mock(i)
            @classmethod
            def to_dict(cls, i: DictSerializableT) -> dict | None: return cls.to_dict_mock(i)

        class TestApiOverridesClient(BaseApi[TestData]):
            request_body = TestData
            response_body = TestData
            url = "/test"
            default_serializer = MockDeserializer # API's own deserializer

        class MyClientWithSerializer(BaseClient):
            base_url = "http://example.com"
            default_serializer = MockDeserializerClient # Client's deserializer
            test_endpoint = ApiEndpoint(TestApiOverridesClient)

        client = MyClientWithSerializer()
        api_instance = client.test_endpoint._api
        test_data_instance = TestData(value="override_request")
        api_instance._parse_request_body(test_data_instance)

        MockDeserializer.can_apply_mock.assert_called_once_with(test_data_instance)
        MockDeserializer.to_dict_mock.assert_called_once_with(test_data_instance)
        MockDeserializerClient.can_apply_mock.assert_not_called()
        MockDeserializerClient.to_dict_mock.assert_not_called()

    def test_fallback_to_global_serializer_if_none_set(self):
        # Uses DataclassSerializer by default for TestData
        class TestApiFallback(BaseApi[TestData]):
            response_body = TestData
            url = "/test"

        api = TestApiFallback()
        # Spy on DataclassSerializer.from_dict
        with MagicMock( wraps=DictSerializable.serializers[0].from_dict ) as mock_dataclass_from_dict:
            # Temporarily replace the original method with the mock
            original_from_dict = DictSerializable.serializers[0].from_dict
            DictSerializable.serializers[0].from_dict = mock_dataclass_from_dict

            try:
                result = api._parse_response_body(TestData, {"value": "fallback_test"})
                assert result == TestData(value="fallback_test")
                mock_dataclass_from_dict.assert_called_once_with(TestData, {"value": "fallback_test"})
            finally:
                # Restore original method
                DictSerializable.serializers[0].from_dict = original_from_dict

        MockSerializer.can_apply_mock.assert_not_called()
        MockSerializer.from_dict_mock.assert_not_called()

    def test_fallback_to_global_deserializer_if_none_set(self):
        class TestApiFallback(BaseApi[TestData]):
            request_body = TestData
            response_body = TestData
            url = "/test"

        api = TestApiFallback()
        test_data_instance = TestData(value="fallback_request")
        # Spy on DataclassDeserializer.to_dict
        with MagicMock( wraps=DictSerializable.deserializers[0].to_dict ) as mock_dataclass_to_dict:
            original_to_dict = DictSerializable.deserializers[0].to_dict
            DictSerializable.deserializers[0].to_dict = mock_dataclass_to_dict
            try:
                result = api._parse_request_body(test_data_instance)
                assert result == {"value": "fallback_request"}
                mock_dataclass_to_dict.assert_called_once_with(test_data_instance)
            finally:
                DictSerializable.deserializers[0].to_dict = original_to_dict

        MockDeserializer.can_apply_mock.assert_not_called()
        MockDeserializer.to_dict_mock.assert_not_called()

    def test_fallback_if_preferred_serializer_cannot_apply(self):
        MockSerializer.can_apply_mock.return_value = False # Key setup for this test

        class TestApiFallbackCanApply(BaseApi[TestData]):
            response_body = TestData
            url = "/test"
            default_serializer = MockSerializer

        api = TestApiFallbackCanApply()
        with MagicMock( wraps=DictSerializable.serializers[0].from_dict ) as mock_dataclass_from_dict:
            original_from_dict = DictSerializable.serializers[0].from_dict
            DictSerializable.serializers[0].from_dict = mock_dataclass_from_dict
            try:
                result = api._parse_response_body(TestData, {"value": "fallback_can_apply"})
                assert result == TestData(value="fallback_can_apply")
                mock_dataclass_from_dict.assert_called_once_with(TestData, {"value": "fallback_can_apply"})
            finally:
                DictSerializable.serializers[0].from_dict = original_from_dict

        MockSerializer.can_apply_mock.assert_called_once_with(TestData)
        MockSerializer.from_dict_mock.assert_not_called() # Should not be called

    def test_fallback_if_preferred_deserializer_cannot_apply(self):
        MockDeserializer.can_apply_mock.return_value = False

        class TestApiFallbackCanApply(BaseApi[TestData]):
            request_body = TestData
            response_body = TestData
            url = "/test"
            default_serializer = MockDeserializer

        api = TestApiFallbackCanApply()
        test_data_instance = TestData(value="fallback_can_apply_req")
        with MagicMock( wraps=DictSerializable.deserializers[0].to_dict ) as mock_dataclass_to_dict:
            original_to_dict = DictSerializable.deserializers[0].to_dict
            DictSerializable.deserializers[0].to_dict = mock_dataclass_to_dict
            try:
                result = api._parse_request_body(test_data_instance)
                assert result == {"value": "fallback_can_apply_req"}
                mock_dataclass_to_dict.assert_called_once_with(test_data_instance)
            finally:
                DictSerializable.deserializers[0].to_dict = original_to_dict

        MockDeserializer.can_apply_mock.assert_called_once_with(test_data_instance)
        MockDeserializer.to_dict_mock.assert_not_called()

    def test_error_if_preferred_serializer_fails(self):
        class TestApiFailing(BaseApi[TestData]):
            response_body = TestData
            url = "/test"
            default_serializer = FailingSerializer

        api = TestApiFailing()
        with pytest.raises(DictSerializationError) as excinfo:
            api._parse_response_body(TestData, {"value": "fail_test"})
        assert "FailingSerializer failed as expected" in str(excinfo.value.__cause__)
        assert "using FailingSerializer" in str(excinfo.value)


    def test_error_if_preferred_deserializer_fails(self):
        class TestApiFailing(BaseApi[TestData]):
            request_body = TestData
            response_body = TestData
            url = "/test"
            default_serializer = FailingDeserializer

        api = TestApiFailing()
        with pytest.raises(DictDeserializationError) as excinfo:
            api._parse_request_body(TestData(value="fail_test_req"))
        assert "FailingDeserializer failed as expected" in str(excinfo.value.__cause__)
        assert "using FailingDeserializer" in str(excinfo.value)

```python
# Helper for spy tests - to ensure we are checking the correct default serializer
# quickapi.serializers.DataclassSerializer is the first in the list
import quickapi.serializers.dataclass as quickapi_dataclass_serializers

assert DictSerializable.serializers[0] is quickapi_dataclass_serializers.DataclassSerializer
assert DictSerializable.deserializers[0] is quickapi_dataclass_serializers.DataclassDeserializer
```
# The above assertion block is just for my development reference, not part of the test code.
# It confirms that `DictSerializable.serializers[0]` is indeed the DataclassSerializer.
# This is important for the spy tests to be valid.
