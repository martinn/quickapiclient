import dataclasses
from typing import ClassVar

import attrs
import msgspec
import pydantic
import pytest

from quickapi.serializers.attrs import AttrsSerializer
from quickapi.serializers.base import BaseSerializer
from quickapi.serializers.dataclass import DataclassSerializer
from quickapi.serializers.msgspec import MsgspecSerializer
from quickapi.serializers.pydantic import PydanticSerializer


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
        "serializer_cls, input_data",
        [
            (DataclassSerializer, DataclassFact(**simple_model)),
            (AttrsSerializer, AttrsFact(**simple_model)),
            (PydanticSerializer, PydanticFact(**simple_model)),
            (MsgspecSerializer, MsgspecFact(**simple_model)),
        ],
    )
    def test_to_and_from_simple_model(
        self,
        serializer_cls: BaseSerializer,
        input_data,
    ):
        assert serializer_cls.to_dict(input_data) == self.simple_model
        assert (
            serializer_cls.from_dict(type(input_data), self.simple_model) == input_data
        )

    @pytest.mark.parametrize(
        "serializer_cls, input_data",
        [
            (
                DataclassSerializer,
                DataclassComplexModel(
                    current_page=1, data=[DataclassFact(**simple_model)]
                ),
            ),
            (
                AttrsSerializer,
                AttrsComplexModel(current_page=1, data=[AttrsFact(**simple_model)]),
            ),
            (
                PydanticSerializer,
                PydanticComplexModel(
                    current_page=1, data=[PydanticFact(**simple_model)]
                ),
            ),
            (
                MsgspecSerializer,
                MsgspecComplexModel(current_page=1, data=[MsgspecFact(**simple_model)]),
            ),
        ],
    )
    def test_to_and_from_complex_model(
        self,
        serializer_cls: BaseSerializer,
        input_data,
    ):
        assert serializer_cls.to_dict(input_data) == self.complex_model
        assert (
            serializer_cls.from_dict(type(input_data), self.complex_model) == input_data
        )

    #
    # @pytest.mark.parametrize(
    #     "instance",
    #     [
    #         object(),
    #         # All other serializers will require a valid instance to start with
    #     ],
    # )
    # def test_to_dict_with_invalid_input(self, instance):
    #     with pytest.raises(DictDeserializationError):
    #         DictSerializable.to_dict(instance)
    #
    # @pytest.mark.parametrize(
    #     "klass, input_data",
    #     [
    #         (DataclassComplexModel, invalid_model),
    #         (AttrsComplexModel, invalid_model),
    #         (PydanticComplexModel, invalid_model),
    #         (MsgspecComplexModel, invalid_model),
    #         (object, invalid_model),
    #     ],
    # )
    # def test_from_dict_with_invalid_input(self, klass, input_data):
    #     with pytest.raises(DictSerializationError):
    #         DictSerializable.from_dict(klass, input_data)
