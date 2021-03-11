"""MarshPy common definitions."""
from typing import TypeVar
from typing import Union


class Undefined:
    """Dummy type representing a failed loading, used for type hints."""


# Unique symbol used to differentiate an error from a valid None return when
# loading a field.
UNDEFINED = Undefined()

ObjectType = TypeVar('ObjectType')
LoadResult = Union[ObjectType, Undefined]
