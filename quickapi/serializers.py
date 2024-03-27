import dataclasses
from collections.abc import Sequence
from typing import TYPE_CHECKING, Protocol, TypeAlias, TypeVar

import attrs
import cattrs

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from .exceptions import (
    RequestSerializationError,
    ResponseSerializationError,
)

try:
    import pydantic
except ImportError:
    pydantic_installed = False
else:
    pydantic_installed = True


DictSerializableT: TypeAlias = (
    "dict | DataclassInstance | attrs.AttrsInstance | pydantic.BaseModel"
)
FromDictSerializableT = TypeVar("FromDictSerializableT")


class BaseSerializer(Protocol):
    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        raise NotImplementedError

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        raise NotImplementedError


class BaseDeserializer(Protocol):
    @classmethod
    def can_apply(cls, instance: DictSerializableT) -> bool:
        raise NotImplementedError

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        raise NotImplementedError


class DataclassSerializer:
    """
    Convert from dict to attrs model.

    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return dataclasses.is_dataclass(klass)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            # TODO: See if there's a simpler approach so we can remove this hard dependency
            return cattrs.structure(values, klass)
        except cattrs.ClassValidationError as e:
            raise ResponseSerializationError(expected_type=klass.__name__) from e


class DataclassDeserializer:
    """
    Convert from dataclass model to dict.
    """

    @classmethod
    def can_apply(cls, instance: "DataclassInstance") -> bool:
        return dataclasses.is_dataclass(instance)

    @classmethod
    def to_dict(cls, instance: "DataclassInstance") -> dict | None:
        return dataclasses.asdict(instance)


class AttrsSerializer:
    """
    Convert from dict to attrs model.

    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return attrs.has(klass)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            return cattrs.structure(values, klass)
        except cattrs.ClassValidationError as e:
            raise ResponseSerializationError(expected_type=klass.__name__) from e


class AttrsDeserializer:
    """
    Convert from attrs model to dict.
    """

    @classmethod
    def can_apply(cls, instance: "attrs.AttrsInstance") -> bool:
        return attrs.has(type(instance))

    @classmethod
    def to_dict(cls, instance: "attrs.AttrsInstance") -> dict | None:
        return attrs.asdict(instance)


class PydanticSerializer:
    """
    Convert from dict to pydantic model.
    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        # TODO: Is this correct?
        return pydantic_installed and issubclass(klass, pydantic.BaseModel)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            return klass(**values)
        except pydantic.ValidationError as e:
            raise ResponseSerializationError(expected_type=klass.__name__) from e


class PydanticDeserializer:
    """Convert from pydantic model to dict."""

    @classmethod
    def can_apply(cls, instance: "pydantic.BaseModel") -> bool:
        return pydantic_installed and isinstance(instance, pydantic.BaseModel)

    @classmethod
    def to_dict(cls, instance: "pydantic.BaseModel") -> dict | None:
        return instance.model_dump()


class DictSerializable:
    """
    Convert to/from dictionaries to the appropriate class/instance.

    @TODO: Maybe make the (de)serializer pluggable and configurable
        instead of checking which one can apply.
    """

    serializers: Sequence[type[BaseSerializer]] = (
        DataclassSerializer,
        AttrsSerializer,
        PydanticSerializer,
    )
    deserializers: Sequence[type[BaseDeserializer]] = (  # type: ignore [assignment]
        DataclassDeserializer,
        AttrsDeserializer,
        PydanticDeserializer,
    )

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        for serializer in cls.serializers:
            if serializer.can_apply(klass):
                return serializer.from_dict(klass, values)
        raise ResponseSerializationError(expected_type=klass.__name__)

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        for deserializer in cls.deserializers:
            if deserializer.can_apply(instance):
                return deserializer.to_dict(instance)
        raise RequestSerializationError(expected_type=str(DictSerializableT))
