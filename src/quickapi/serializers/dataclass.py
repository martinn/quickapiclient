import dataclasses
from typing import TYPE_CHECKING, Any

import chili

if TYPE_CHECKING:
    pass

from quickapi.exceptions import DictDeserializationError, DictSerializationError
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
        except (ValueError, chili.error.DecoderError) as e:
            raise DictSerializationError(expected_type=klass.__name__) from e

    @classmethod
    def to_dict(cls, instance: Any) -> dict | None:
        try:
            return dataclasses.asdict(instance)
        except TypeError as e:
            raise DictDeserializationError(expected_type="DataclassInstance") from e
