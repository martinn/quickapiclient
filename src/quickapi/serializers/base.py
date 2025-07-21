from typing import Protocol

from quickapi.serializers.types import DictSerializableT, FromDictSerializableT


class BaseSerializer(Protocol):
    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        raise NotImplementedError


class BaseDeserializer(Protocol):
    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        raise NotImplementedError
