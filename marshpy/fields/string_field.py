"""String field class & utilities."""
from gettext import gettext as _
from re import compile as re_compile
from typing import Any, Optional, Pattern

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import ILoadingContext
from marshpy.core.validation import ValidateCallback
from marshpy.fields.scalar_field import ScalarField


class StringField(ScalarField):
    """String YAML object field."""

    def __init__(
        self,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
        pattern: Optional[str] = None,
    ):
        """Initialize string field.

        Args:
            required: See BaseField constructor.
            validate: See BaseField constructor.
            pattern: Pattern the deserialized strings should match. If defined
                     and the string doesn't match, a VALIDATION_ERROR will be
                     raised.

        """
        super().__init__(required=required, validate=validate)
        self._pattern_str: Optional[str] = None
        self._pattern: Optional[Pattern[str]] = None

        if pattern is not None:
            assert isinstance(pattern, str), _("pattern must be a string.")
            self._pattern_str = pattern
            self._pattern = re_compile(pattern)

    def _convert(self, context: ILoadingContext, value: str) -> Any:
        if self._pattern is not None and not self._pattern.match(value):
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _("Value {} doesn't match required pattern {}"),
                value,
                self._pattern_str,
            )
            return UNDEFINED

        return value
