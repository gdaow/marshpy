"""Boolean field class module."""
from gettext import gettext as _
from typing import Any

from pofy.core.errors import ErrorCode
from pofy.core.constants import UNDEFINED
from pofy.fields.base_field import ScalarField
from pofy.core.interfaces import ILoadingContext


class BoolField(ScalarField):
    """Boolean field loader."""

    def _convert(self, context: ILoadingContext) -> Any:
        node = context.current_node()
        true_values = [
            'y', 'Y', 'yes', 'Yes', 'YES',
            'true', 'True', 'TRUE',
            'on', 'On', 'ON'
        ]
        false_values = [
            'n', 'N', 'no', 'No', 'NO',
            'false', 'False', 'FALSE'
            'off', 'Off', 'OFF'
        ]

        value = node.value
        if value in true_values:
            return True

        if value in false_values:
            return False

        context.error(
            ErrorCode.VALUE_ERROR,
            _('Boolean value should be one of {}'),
            ', '.join(true_values + false_values)
        )

        return UNDEFINED
