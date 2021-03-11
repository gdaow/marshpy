"""Path field class & utilities."""
from gettext import gettext as _
from pathlib import Path
from typing import Any
from typing import Optional

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import ILoadingContext
from marshpy.core.validation import ValidateCallback
from marshpy.fields.scalar_field import ScalarField


class PathField(ScalarField):
    """Path YAML object field."""

    def __init__(
        self,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
        must_exist: bool = True
    ):
        """Initialize the Path field.

        Args:
            required: See BaseField constructor.
            validate: See BaseField constructor.
            must_exist: If true, a VALIDATION_ERROR will be emmited if the file
                        doesn't exist when the field is deserialized.

        """
        super().__init__(required=required, validate=validate)
        self._must_exist = must_exist

    def _convert(self, context: ILoadingContext, value: str) -> Any:
        path = Path(value)

        if not path.is_absolute() and not path.exists():
            location_str = context.current_location()
            if location_str is not None:
                location = Path(location_str)
                parent = location.parent
                path = parent / path

        if self._must_exist and not path.exists():
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _('Cannot find path {}.'),
                path
            )
            return UNDEFINED

        return path
