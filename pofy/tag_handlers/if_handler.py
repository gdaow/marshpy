"""Handler loading a value only if some flag is defined."""
from copy import copy
from typing import Any

from pofy.common import UNDEFINED
from pofy.interfaces import IBaseField
from pofy.interfaces import ILoadingContext
from pofy.tag_handlers.tag_handler import TagHandler


class IfHandler(TagHandler):
    """Tag loading a value only if some flag is defined.

    Flags are set through the flags parameter of the pofy.load method.
    """

    tag_pattern = r'^if\((?P<flag>[\w|_]*)\)$'

    def load(self, context: ILoadingContext, field: IBaseField) \
            -> Any:
        node = context.current_node()
        tag = node.tag[1:] # Remove trailing !
        match = self._compiled_pattern.match(tag)

        # The pattern should match already if we're here
        assert match is not None

        flag = match.group('flag')

        if not context.is_defined(flag):
            return UNDEFINED

        # We need to return a copy of the node and erase the tag to avoid
        # the infinite recursion that would happen if we return a node with
        # an if tag still defined on it
        node_copy = copy(node)
        node_copy.tag = ''

        return context.load(field, node_copy)
