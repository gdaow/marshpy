"""Schema related helpers & functions."""
from inspect import getmembers
from inspect import isclass
from typing import Any
from typing import Callable
from typing import Optional
from typing import Type
from typing import cast

from pofy.core.validation import ValidationContext


SchemaResolver = Callable[[Type[Any]], Optional[Type[Any]]]


class SchemaBase:
    """Default Schema class base, bringing some helpers."""

    @classmethod
    def validate(cls, context: ValidationContext, obj: Any) -> None:
        """Validate deserialized object.

        Will call validate directly on the deserialized object. If a parent
        class of the deserialized type has a schema inheriting from SchemaBase,
        don't call super().validate(...) from the child, as Pofy will call it
        through the parent's SchemaBase validation method.
        """
        validate = cls._find_hook(obj.__class__, 'validate')
        if validate is None:
            return

        validate(obj, context)

    @classmethod
    def post_load(cls, obj: Any) -> None:
        """Apply post_load operations on deserialized object.

        Will call post_load directly on the deserialized object. If a parent
        class of the deserialized type has a schema inheriting from SchemaBase,
        don't call super().post_load() from the child, as Pofy will call it
        through the parent's SchemaBase post_load method.
        """
        post_load = cls._find_hook(obj.__class__, 'post_load')
        if post_load is not None:
            post_load(obj)

    @classmethod
    def _find_hook(cls, obj_class: Type[Any], name: str) \
            -> Optional[Callable[..., Any]]:
        enclosing_type = cls._find_enclosing_type(obj_class)
        assert enclosing_type is not None
        if name not in enclosing_type.__dict__:
            return None

        result = getattr(enclosing_type, name)
        return cast(Callable[..., Any], result)

    @classmethod
    def _find_enclosing_type(cls, obj_class: Type[Any]) -> Optional[Type[Any]]:
        # Finds the type in which the current schema is declared as a
        # nested class
        result: Optional[Type[Any]] = None
        for _, member in getmembers(obj_class):
            if member != cls:
                continue

            return obj_class

        for base in obj_class.__bases__:
            result = cls._find_enclosing_type(base)
            if result is not None:
                return result

        return None


def default_schema_resolver(cls: Type[Any]) -> Optional[Type[Any]]:
    """Return the first inner class named 'Schema' found in given type."""
    def _filter(member: Any) -> bool:
        return isclass(member) and member.__name__ == 'Schema'

    for _, member_it in getmembers(cls, _filter):
        return cast(Type[Any], member_it)

    return None
