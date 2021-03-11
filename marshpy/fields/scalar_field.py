"""Base field class & utilities."""
from abc import abstractmethod
from gettext import gettext as _
from typing import Any
from typing import Optional
from typing import Union

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.fields.base_field import BaseField
from marshpy.core.interfaces import ILoadingContext


class ScalarField(BaseField):
    """Base class for scalar value fields."""

    def _load(self, context: ILoadingContext) -> Any:
        if not context.expect_scalar():
            return UNDEFINED

        current_node = context.current_node()
        string_value = current_node.value
        return self._convert(context, string_value)

    @abstractmethod
    def _convert(self, context: ILoadingContext, value: str) -> Any:
        """Convert the string value to the target type of this field.

        Args:
            context: The loading context.
            value:   The string value to convert to the target type.

        Return:
            The converted value.

        """
        raise NotImplementedError

    @staticmethod
    def _check_in_bounds(
        context: ILoadingContext,
        value: Union[int, float],
        minimum: Optional[Union[int, float]],
        maximum: Optional[Union[int, float]]
    ) -> Any:
        if minimum is not None and value < minimum:
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _('Value is too small (minimum : {})'), minimum
            )
            return UNDEFINED

        if maximum is not None and value > maximum:
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _('Value is too big (maximum : {})'), maximum
            )
            return UNDEFINED

        return value
