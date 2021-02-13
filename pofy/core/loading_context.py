"""Loading context class & utilities."""
from gettext import gettext as _
from typing import Any
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple
from typing import Type
from typing import cast

from yaml import MappingNode
from yaml import Node
from yaml import ScalarNode
from yaml import SequenceNode

from pofy.core.errors import ErrorCode
from pofy.core.errors import get_exception_type
from pofy.core.interfaces import ConfigType
from pofy.core.interfaces import IBaseField
from pofy.core.interfaces import ILoadingContext
from pofy.tag_handlers.tag_handler import TagHandler


ErrorHandler = Optional[Callable[[Node, ErrorCode, str], Any]]
FieldResolver = Callable[[Type[Any]], Dict[str, 'IBaseField']]
HookResolver = Callable[[Any, str], Optional[Callable[..., None]]]
NodeStack = List[Tuple[Node, Optional[str]]]


class LoadingContext(ILoadingContext):
    """Default and only implementation of ILoadingContext."""

    def __init__(
        self,
        error_handler: ErrorHandler,
        tag_handlers: Iterable[TagHandler],
        flags: Optional[Set[str]] = None,
        field_resolver: Optional[FieldResolver] = None,
        hook_resolver: Optional[HookResolver] = None,
        user_config: Optional[List[Any]] = None
    ):
        """Initialize LoadingContext.

        Args:
            error_handler :     Called with arguments (node, error_message) when
                                an error occurs. If it's not specified, a
                                PofyError will be raised when an error occurs.
                                (see errors.py)
            tag_handlers :      Tag handlers used to apply custom behaviors when
                                encountering YAML tags.
            flags:              Flags to define during loading, that can be used
                                with the !if tag (see IfTagHandler).
            field_resolver:     Function returning the fields definition for the
                                given type, or None if not found. By default, it
                                will search for a class variable named 'fields'
                                in the deserialized type.
            hook_resolver:      Function returning the hook with the given name
                                for the given object, or None if not found. By
                                default, it will search for an instance method
                                named like the hook on the given object.
            user_config:        List of objects used to eventually configure
                                custom fields, that will be retrievable through
                                the get_user_config method.

        """
        self._error_handler = error_handler
        self._tag_handlers = list(tag_handlers)
        self._node_stack: NodeStack = []
        self._flags = flags if flags is not None else set()
        if field_resolver is not None:
            self._field_resolver = field_resolver
        else:
            self._field_resolver = _default_field_resolver

        if hook_resolver is not None:
            self._hook_resolver = hook_resolver
        else:
            self._hook_resolver = _default_hook_resolver

        if user_config is not None:
            self._user_config = user_config
        else:
            self._user_config = []

    def load(
        self,
        field: IBaseField,
        node: Node,
        location: Optional[str] = None
    ) -> Any:
        """Push a node in the context.

        This is solely used to know which node is currently loaded when calling
        error function, to avoid having to pass around node objects.

        Args:
            field: Field describing this node.
            node: Currently loaded node.
            location: The path from which this node was loaded. Every node
                       pushed subsequently will be considered having the
                       same path, except until another child path is pushed.

        """
        if len(self._node_stack) > 0:
            assert self._node_stack[-1][0] != node

        self._node_stack.append((node, location))

        try:
            tag_handler = self._get_tag_handler(node)
            if tag_handler is not None:
                result = tag_handler.load(self, field)
            else:
                result = field.load(self)
        finally:
            self._node_stack.pop()

        return result

    def is_defined(self, flag: str) -> bool:
        return flag in self._flags

    def get_fields(self, cls: Type[Any]) -> Dict[str, IBaseField]:
        return self._field_resolver(cls)

    def get_hook(self, obj: Any, name: str) -> Optional[Callable[..., None]]:
        return self._hook_resolver(obj, name)

    def get_user_config(self, config_type: Type[ConfigType]) -> ConfigType:
        for item in self._user_config:
            if isinstance(item, config_type):
                return item

        assert False, "No user configuration object of the given type was found"
        return None

    def current_node(self) -> Node:
        nodes = self._node_stack
        assert len(nodes) > 0
        return nodes[-1][0]

    def current_location(self) -> Optional[str]:
        for __, location in reversed(self._node_stack):
            if location is not None:
                return location

        return None

    def expect_scalar(self, message: Optional[str] = None) -> bool:
        """Return false and raise an error if the current node isn't scalar."""
        if message is None:
            message = _('Expected a scalar value.')
        return self._expect_node(
            ScalarNode,
            message
        )

    def expect_sequence(self) -> bool:
        """Return false and raise if the current node isn't a sequence."""
        return self._expect_node(
            SequenceNode,
            _('Expected a sequence value.')
        )

    def expect_mapping(self) -> bool:
        """Return false and raise if the current node isn't a mapping."""
        return self._expect_node(
            MappingNode,
            _('Expected a mapping value.')
        )

    def error(
        self,
        code: ErrorCode,
        message_format: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Register an error in the current loading context.

        If errors occured in the scope of a context, an error will be raised
        at the end of the object loading.

        Args:
            code: Code of the error.
            message_format: The error message format.
            *args, **kwargs: Arguments used to format message.

        """
        assert len(self._node_stack) > 0
        node, __ = self._node_stack[-1]
        message = message_format.format(*args, **kwargs)
        if self._error_handler is not None:
            self._error_handler(node, code, message)
        else:
            exception_type = get_exception_type(code)
            raise exception_type(node, message)

    def _expect_node(
        self,
        node_type: Type[Node],
        error_format: str,
        *args: Any,
        **kwargs: Any
    ) -> bool:
        current_node = self.current_node()
        if not isinstance(current_node, node_type):
            self.error(
                ErrorCode.UNEXPECTED_NODE_TYPE,
                error_format,
                *args,
                **kwargs
            )
            return False

        return True

    def _get_tag_handler(self, node: Node) -> Optional[TagHandler]:
        tag = node.tag
        if not tag.startswith('!'):
            return None

        found_handler = None
        for handler in self._tag_handlers:
            if not handler.match(node):
                continue

            if found_handler is not None:
                self.error(
                    ErrorCode.MULTIPLE_MATCHING_HANDLERS,
                    _('Got multiple matching handlers for tag {}'), tag
                )
                continue

            found_handler = handler

        return found_handler


def _default_field_resolver(cls: Type[Any]) -> Dict[str, IBaseField]:
    if not hasattr(cls, 'fields'):
        return {}

    schema = getattr(cls, 'fields')
    return cast(Dict[str, IBaseField], schema)


def _default_hook_resolver(obj: Any, hook_name: str)\
        -> Optional[Callable[..., None]]:
    if not hasattr(obj, hook_name):
        return None

    hook = getattr(obj, hook_name)

    if not callable(hook):
        return None

    return cast(Callable[..., Any], hook)
