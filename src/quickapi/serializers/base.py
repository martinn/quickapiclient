from collections.abc import Sequence
from typing import Protocol, Type, Union

from quickapi.exceptions import DictDeserializationError, DictSerializationError
from quickapi.serializers.attrs import AttrsDeserializer, AttrsSerializer
from quickapi.serializers.dataclass import DataclassDeserializer, DataclassSerializer
from quickapi.serializers.msgspec import MsgspecDeserializer, MsgspecSerializer
from quickapi.serializers.pydantic import PydanticDeserializer, PydanticSerializer
from quickapi.serializers.types import DictSerializableT, FromDictSerializableT


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


ConfigurableSerializer = Union[Type[BaseSerializer], Type[BaseDeserializer]]


class DictSerializable:
    """
    Convert to/from dictionaries to the appropriate class/instance.

    Currently, it will try to (de)serialize the following types:

    1. dict
    2. dataclasses
    3. attrs (if installed)
    4. pydantic (if installed)
    5. msgspec (if installed)

    In the future, you will be able to plug in your own (de)serializers instead.
    """

    # TODO: Maybe make the (de)serializer pluggable and configurable instead
    serializers: Sequence[type[BaseSerializer]] = (
        DataclassSerializer,
        AttrsSerializer,
        PydanticSerializer,
        MsgspecSerializer,
    )
    deserializers: Sequence[type[BaseDeserializer]] = (  # type: ignore [assignment]
        DataclassDeserializer,
        AttrsDeserializer,
        PydanticDeserializer,
        MsgspecDeserializer,
    )

    @classmethod
    def from_dict(
        cls,
        klass: type[FromDictSerializableT],
        values: dict,
        preferred_serializer: Type[BaseSerializer] | None = None,
    ) -> FromDictSerializableT:
        if preferred_serializer:
            if preferred_serializer.can_apply(klass):
                try:
                    return preferred_serializer.from_dict(klass, values)
                except Exception as e:
                    # If preferred serializer is chosen but fails, raise immediately
                    raise DictSerializationError(
                        expected_type=klass.__name__, specific_serializer=preferred_serializer
                    ) from e
            # If preferred_serializer cannot apply, fall through to iterating available ones

        for serializer in cls.serializers:
            if serializer.can_apply(klass):
                return serializer.from_dict(klass, values)
        raise DictSerializationError(expected_type=klass.__name__)

    @classmethod
    def to_dict(
        cls,
        instance: DictSerializableT,
        preferred_deserializer: Type[BaseDeserializer] | None = None,
    ) -> dict | None:
        if preferred_deserializer:
            if preferred_deserializer.can_apply(instance):
                try:
                    return preferred_deserializer.to_dict(instance)
                except Exception as e:
                    # If preferred deserializer is chosen but fails, raise immediately
                    raise DictDeserializationError(
                        expected_type=str(type(instance)), specific_deserializer=preferred_deserializer
                    ) from e
            # If preferred_deserializer cannot apply, fall through to iterating available ones

        for deserializer in cls.deserializers:
            if deserializer.can_apply(instance):
                return deserializer.to_dict(instance)
        raise DictDeserializationError(expected_type=str(DictSerializableT))
