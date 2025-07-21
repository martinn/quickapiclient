import dataclasses
from typing import TYPE_CHECKING

import chili

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import FromDictSerializableT


class DataclassSerializer:
    """
    Convert from dict to dataclass model and vice-versa.

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

    @classmethod
    def to_dict(cls, instance: DataclassInstance) -> dict | None:
        return dataclasses.asdict(instance)
