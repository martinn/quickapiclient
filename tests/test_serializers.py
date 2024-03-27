import dataclasses
from typing import ClassVar

import attrs
import pydantic
import pytest

from quickapi.exceptions import (
    DictDeserializationError,
    DictSerializationError,
)
from quickapi.serializers import DictSerializable


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


class TestSimpleSerializers:
    simple_model: ClassVar = {"fact": "fact", "length": 4}
    complex_model: ClassVar = {"current_page": 1, "data": [simple_model]}
    invalid_model: ClassVar = {"current_page": "not_int", "data": []}

    @pytest.mark.parametrize(
        "input_data",
        [
            DataclassFact(**simple_model),
            AttrsFact(**simple_model),
            PydanticFact(**simple_model),
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
            (object, invalid_model),
        ],
    )
    def test_from_dict_with_invalid_input(self, klass, input_data):
        with pytest.raises(DictSerializationError):
            DictSerializable.from_dict(klass, input_data)
