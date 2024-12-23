from quickapi.exceptions import DictSerializationError
from quickapi.serializers.types import FromDictSerializableT

try:
    import pydantic
except ImportError:
    pydantic_installed = False
else:
    pydantic_installed = True


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
            raise DictSerializationError(expected_type=klass.__name__) from e


class PydanticDeserializer:
    """Convert from pydantic model to dict."""

    @classmethod
    def can_apply(cls, instance: "pydantic.BaseModel") -> bool:
        return pydantic_installed and isinstance(instance, pydantic.BaseModel)

    @classmethod
    def to_dict(cls, instance: "pydantic.BaseModel") -> dict | None:
        return instance.model_dump()
