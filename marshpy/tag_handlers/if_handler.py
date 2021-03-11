"""Handler loading a value only if some flag is defined."""
from copy import copy
from typing import Any
from typing import Iterable
from typing import Optional

from marshpy.core.constants import UNDEFINED
from marshpy.core.interfaces import IBaseField
from marshpy.core.interfaces import ILoadingContext
from marshpy.tag_handlers.tag_handler import TagHandler


class IfHandler(TagHandler):
    """Tag loading a value only if some flag is defined.

    Flags are set through the flags parameter of the marshpy.load method.
    """

    tag_pattern = r'^if\((?P<flag>[\w|_]*)\)$'

    class Config:
        """Shared configuration for all path handlers."""

        def __init__(self, flags: Optional[Iterable[str]] = None) -> None:
            """Initialize the config."""
            self._flags = set(flags) if flags is not None else set()

        def is_defined(self, flag: str) -> bool:
            """Check that the given flag is defined."""
            return flag in self._flags

    def load(self, context: ILoadingContext, field: IBaseField) \
            -> Any:
        node = context.current_node()
        tag = node.tag[1:] # Remove trailing !
        match = self._compiled_pattern.match(tag)

        # The pattern should match already if we're here
        assert match is not None

        config = context.get_config(IfHandler.Config)
        flag = match.group('flag')

        if not config.is_defined(flag):
            return UNDEFINED

        # We need to return a copy of the node and erase the tag to avoid
        # the infinite recursion that would happen if we return a node with
        # an if tag still defined on it
        node_copy = copy(node)
        node_copy.tag = ''

        return context.load(field, node_copy)
