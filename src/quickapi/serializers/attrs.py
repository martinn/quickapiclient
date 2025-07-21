from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import DictSerializableT, FromDictSerializableT

try:
    import attrs
    import cattrs
except ImportError:
    attrs_installed = False
else:
    attrs_installed = True


class AttrsSerializer:
    """
    Convert from dict to attrs model and vice-versa.

    """

    @classmethod
    def can_apply(cls, klass: type[FromDictSerializableT]) -> bool:
        return attrs_installed and attrs.has(klass)

    @classmethod
    def from_dict(
        cls, klass: type[FromDictSerializableT], values: dict
    ) -> FromDictSerializableT:
        try:
            return cattrs.structure(values, klass)
        except cattrs.ClassValidationError as e:
            raise DictSerializationError(expected_type=klass.__name__) from e

    @classmethod
    def to_dict(cls, instance: DictSerializableT) -> dict | None:
        return attrs.asdict(instance)
