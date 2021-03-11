"""MarshPy deserializing function."""
from gettext import gettext as _
from inspect import isclass
from io import TextIOBase
from typing import Any
from typing import IO
from typing import Iterable
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union
from typing import cast

from yaml import compose

from marshpy.core.constants import LoadResult
from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorHandler
from marshpy.core.loading_context import LoadingContext
from marshpy.fields.base_field import BaseField
from marshpy.fields.bool_field import BoolField
from marshpy.fields.dict_field import DictField
from marshpy.fields.float_field import FloatField
from marshpy.fields.int_field import IntField
from marshpy.fields.list_field import ListField
from marshpy.fields.object_field import ObjectField
from marshpy.fields.string_field import StringField
from marshpy.tag_handlers.env_handler import EnvHandler
from marshpy.tag_handlers.glob_handler import GlobHandler
from marshpy.tag_handlers.if_handler import IfHandler
from marshpy.tag_handlers.import_handler import ImportHandler
from marshpy.tag_handlers.tag_handler import TagHandler

_ROOT_FIELDS_MAPPING = {
    bool: BoolField(),
    dict: DictField(StringField()),
    float: FloatField(),
    int: IntField(),
    list: ListField(StringField()),
    str: StringField()
}

ObjectType = TypeVar('ObjectType')


def load( # pylint: disable=too-many-locals
    source: Union[str, IO[str]],
    object_class: Optional[Type[ObjectType]] = None,
    tag_handlers: Optional[Iterable[TagHandler]] = None,
    error_handler: Optional[ErrorHandler] = None,
    root_field: Optional[BaseField] = None,
    config: Optional[List[Any]] = None
) -> LoadResult[ObjectType]:
    """Deserialize a YAML file, stream or string into an object.

    Args:
        source :            Either a string containing YAML, or a stream to a
                            YAML source.
        object_class :      Class of the object to create. It will infer the
                            root field to use from this type (Scalar, list,
                            dictionary, or object).
        tag_handlers :      Custom TagHandlers.
        error_handler :     Called with arguments (node, error_message) when an
                            error occurs. If it's not specified, a MarshPyError
                            will be raised when an error occurs.
        root_field:         The field to use to load the root node. You can
                            specify a type (list, dict, one of the scalar types
                            or an objec type as cls parameter to get it infered)
        flags:              Flags to define during loading. Those can be used
                            during deserialization to customize the loaded
                            objects.
        field_resolver:     Function returning the fields definition for the
                            given type, or None if not found. By default, it
                            will search for a class variable named 'fields' in
                            the deserialized type.
        hook_resolver:      Function returning the hook with the given name for
                            the given object, or None if not found. By default,
                            it will search for an instance method named like the
                            hook on the given object.
        config:             List of objects used to eventually configure custom
                            fields, that will be retrievable through the
                            get_config method.

    """
    # This fails with pyfakefs, no simple way to check this, so disable it for
    # now
    # assert isinstance(source, (str, TextIOBase)), \
    #     _('source parameter must be a string or Text I/O.')

    all_tag_handlers: List[TagHandler] = [
        ImportHandler(),
        GlobHandler(),
        EnvHandler(),
        IfHandler(),
    ]

    if tag_handlers is not None:
        for handler_it in tag_handlers:
            assert isinstance(handler_it, TagHandler), \
                _('tag_handlers items should be subclasses of TagHandler')
        all_tag_handlers.extend(tag_handlers)

    if error_handler is not None:
        assert callable(error_handler), \
            _('error_handler must be a callable object.')

    context = LoadingContext(
        error_handler=error_handler,
        tag_handlers=all_tag_handlers,
        config=config
    )

    if root_field is None:
        assert object_class is not None
        assert isclass(object_class), _('object_class must be a type')
        root_field = _ROOT_FIELDS_MAPPING.get(object_class)

    if root_field is None:
        assert object_class is not None
        assert isclass(object_class), _('object_class must be a type')
        root_field = ObjectField(object_class=object_class)

    node = compose(source) # type: ignore
    node_path = None
    if isinstance(source, TextIOBase) and hasattr(source, 'name'):
        node_path = source.name

    result = context.load(root_field, node, node_path)
    if result is UNDEFINED:
        return UNDEFINED

    return cast(ObjectType, result)
