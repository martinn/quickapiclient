import dataclasses
from typing import TYPE_CHECKING

import chili

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import FromDictSerializableT


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
            return chili.decode(values, klass)
        except ValueError as e:
            raise DictSerializationError(expected_type=klass.__name__) from e


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
