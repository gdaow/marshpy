"""Enum field class & utilities."""
from enum import Enum
from gettext import gettext as _
from typing import Any
from typing import Optional
from typing import Type

from pofy.core.constants import UNDEFINED
from pofy.core.errors import ErrorCode
from pofy.core.interfaces import ILoadingContext
from pofy.core.validation import ValidateCallback
from pofy.fields.scalar_field import ScalarField


class EnumField(ScalarField):
    """Enum YAML object field."""

    def __init__(
        self,
        enum_class: Type[Enum],
        required: bool = False,
        validate: Optional[ValidateCallback] = None
    ):
        """Initialize string field.

        Args:
            enum_class: The type of the enum to deserialize.
            required: See BaseField constructor.
            validate: See BaseField constructor.

        """
        super().__init__(required=required, validate=validate)
        self._enum_class = enum_class

    def _convert(self, context: ILoadingContext, value: str) -> Any:
        for member in self._enum_class:
            if member.name == value:
                return member

        context.error(
            ErrorCode.VALIDATION_ERROR,
            _('Unkown value {} for enum {}.'),
            value,
            self._enum_class
        )
        return UNDEFINED
