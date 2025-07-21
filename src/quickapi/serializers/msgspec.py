from typing import Any

from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import DictSerializableT, FromDictSerializableT

try:
    import msgspec
except ImportError:
    msgspec_installed = False
else:
    msgspec_installed = True


class MsgspecSerializer:
    """
    Convert from dict to msgspec.Struct and vice-versa.
    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return msgspec_installed and issubclass(klass, msgspec.Struct)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            return msgspec.convert(values, klass)
        except msgspec.ValidationError as e:
            raise DictSerializationError(expected_type=klass.__name__) from e

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> Any:
        return msgspec.to_builtins(instance, builtin_types=[dict])
