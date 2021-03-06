"""Loading context class & utilities."""
from gettext import gettext as _
from typing import Any, Iterable, List, Optional, Tuple, Type

from yaml import MappingNode, Node, ScalarNode, SequenceNode

from marshpy.core.errors import ErrorCode, ErrorHandler, get_exception_type
from marshpy.core.interfaces import ConfigType, IBaseField, ILoadingContext
from marshpy.tag_handlers.tag_handler import TagHandler

NodeStack = List[Tuple[Node, Optional[str]]]


class LoadingContext(ILoadingContext):
    """Default and only implementation of ILoadingContext."""

    def __init__(
        self,
        error_handler: Optional[ErrorHandler],
        tag_handlers: Iterable[TagHandler],
        config: Optional[List[Any]] = None,
    ):
        """Initialize LoadingContext.

        Args:
            error_handler : Called with arguments (node, error_message) when an error
                            occurs. If it's not specified, a
                            MarshPyError will be raised when an error occurs. (see
                            errors.py)
            tag_handlers :  Tag handlers used to apply custom behaviors when
                            encountering YAML tags.
            config:         List of objects used to eventually configure fields and tag
                            handlers, that will be
                            retrievable through the get_config method.

        """
        self._error_handler = error_handler
        self._tag_handlers = list(tag_handlers)
        self._node_stack: NodeStack = []

        if config is not None:
            self._config = config
        else:
            self._config = []

    def load(
        self, field: IBaseField, node: Node, location: Optional[str] = None
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

    def get_config(self, config_type: Type[ConfigType]) -> ConfigType:
        for item in self._config:
            if isinstance(item, config_type):
                return item

        result = config_type()
        self._config.append(config_type)
        return result

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
            message = _("Expected a scalar value.")
        return self._expect_node(ScalarNode, message)

    def expect_sequence(self) -> bool:
        """Return false and raise if the current node isn't a sequence."""
        return self._expect_node(SequenceNode, _("Expected a sequence value."))

    def expect_mapping(self) -> bool:
        """Return false and raise if the current node isn't a mapping."""
        return self._expect_node(MappingNode, _("Expected a mapping value."))

    def error(
        self, code: ErrorCode, message_format: str, *args: Any, **kwargs: Any
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
        self, node_type: Type[Node], error_format: str, *args: Any, **kwargs: Any
    ) -> bool:
        current_node = self.current_node()
        if not isinstance(current_node, node_type):
            self.error(ErrorCode.UNEXPECTED_NODE_TYPE, error_format, *args, **kwargs)
            return False

        return True

    def _get_tag_handler(self, node: Node) -> Optional[TagHandler]:
        tag = node.tag
        if not tag.startswith("!"):
            return None

        found_handler = None
        for handler in self._tag_handlers:
            if not handler.match(node):
                continue

            if found_handler is not None:
                self.error(
                    ErrorCode.MULTIPLE_MATCHING_HANDLERS,
                    _("Got multiple matching handlers for tag {}"),
                    tag,
                )
                continue

            found_handler = handler

        return found_handler
