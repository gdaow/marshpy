"""Boolean field class module."""
from gettext import gettext as _
from typing import Any

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import ILoadingContext
from marshpy.fields.scalar_field import ScalarField


_TRUE_VALUES = [
    'y', 'Y', 'yes', 'Yes', 'YES',
    'true', 'True', 'TRUE',
    'on', 'On', 'ON'
]

_FALSE_VALUES = [
    'n', 'N', 'no', 'No', 'NO',
    'false', 'False', 'FALSE'
    'off', 'Off', 'OFF'
]


class BoolField(ScalarField):
    """Boolean field loader."""

    def _convert(self, context: ILoadingContext, value: str) -> Any:
        if value in _TRUE_VALUES:
            return True

        if value in _FALSE_VALUES:
            return False

        context.error(
            ErrorCode.VALUE_ERROR,
            _('Boolean value should be one of {}'),
            ', '.join(_TRUE_VALUES + _FALSE_VALUES)
        )

        return UNDEFINED
