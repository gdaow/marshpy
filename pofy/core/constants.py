"""Pofy common definitions."""
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union


class Undefined:
    """Dummy type representing a failed loading, used for type hints."""


# Unique symbol used to differentiate an error from a valid None return when
# loading a field.
UNDEFINED = Undefined()

ObjectType = TypeVar('ObjectType')
LoadResult = Union[ObjectType, Undefined]

SchemaResolver = Callable[[Type[Any]], Optional[Type[Any]]]
