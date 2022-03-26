"""Dictionary field class & utilities."""
from typing import Any, Optional

from yaml import ScalarNode

from marshpy.core.constants import UNDEFINED
from marshpy.core.interfaces import ILoadingContext
from marshpy.core.validation import ValidateCallback
from marshpy.fields.base_field import BaseField
from marshpy.fields.container_field import ContainerField


class DictField(ContainerField):
    """Dictionary YAML object field."""

    def __init__(
        self,
        item_field: BaseField,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
    ):
        """Initialize dict field.

        Args:
            item_field: Field used to load dictionnary values.
            required: See BaseField constructor.
            validate: See BaseField constructor.

        """
        super().__init__(item_field=item_field, required=required, validate=validate)

    def _load(self, context: ILoadingContext) -> Any:
        node = context.current_node()
        if not context.expect_mapping():
            return UNDEFINED

        result = {}
        for key_node, value_node in node.value:
            assert isinstance(key_node, ScalarNode)
            key = key_node.value

            item = context.load(self._item_field, value_node)
            if item is UNDEFINED:
                continue

            result[key] = item

        return result
