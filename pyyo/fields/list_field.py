"""List field class & utilities."""
from gettext import gettext as _

from yaml import SequenceNode

from pyyo.errors import ErrorCode

from .base_field import BaseField


class ListField(BaseField):
    """List YAML object field."""

    def __init__(self, item_field: BaseField, *args, **kwargs):
        """Initialize the list field.

        Arg:
            item_field: Field used to load list items.
            *args, **kwargs: Arguments forwarded to BaseField.

        """
        super().__init__(*args, **kwargs)
        self._item_field = item_field

    def _load(self, node, context):
        if not isinstance(node, SequenceNode):
            context.error(
                node,
                ErrorCode.UNEXPECTED_NODE_TYPE,
                _('Sequence expected')
            )
            return None

        return [self._item_field.load(it, context) for it in node.value]
