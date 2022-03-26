"""List field class & utilities."""
from typing import Any, Optional

from marshpy.core.constants import UNDEFINED
from marshpy.core.interfaces import ILoadingContext
from marshpy.core.validation import ValidateCallback
from marshpy.fields.base_field import BaseField
from marshpy.fields.container_field import ContainerField


class ListField(ContainerField):
    """List YAML object field."""

    def __init__(
        self,
        item_field: BaseField,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
    ):
        """Initialize the list field.

        Arg:
            item_field: Field used to load list items.
            required: See BaseField constructor.
            validate: See BaseField constructor.

        """
        super().__init__(item_field=item_field, required=required, validate=validate)

    def _load(self, context: ILoadingContext) -> Any:
        if not context.expect_sequence():
            return UNDEFINED

        node = context.current_node()
        result = []
        for item_node in node.value:
            item = context.load(self._item_field, item_node)
            if item is UNDEFINED:
                continue

            result.append(item)

        return result
