"""Base field class & utilities."""
from abc import abstractmethod
from gettext import gettext as _
from typing import Any
from typing import Optional

from pofy.core.constants import UNDEFINED
from pofy.core.interfaces import IBaseField
from pofy.core.interfaces import ILoadingContext
from pofy.core.validation import ValidateCallback
from pofy.core.validation import ValidationContext


class BaseField(IBaseField):
    """Base class for all Pofy fields."""

    def __init__(
        self,
        required: bool = False,
        validate: Optional[ValidateCallback] = None
    ) -> None:
        """Initialize the field.

        Args:
            required: If set te true and this field is not defined in yaml when
                      the owning object is loaded, a MissingFieldError error
                      will be raised, or the custom error handler will be
                      called with ErrorCode.MISSING_FIELD_ERROR.
            validate: Function accepting a ValidationContext and the field
                      value as arguments. If the value is invalid,
                      ValidationContext.error should be called with an
                      explicative message, which will raise a ValidationError
                      error, or call the custom error_handler with
                      ErrorCode.VALIDATION_ERROR code.

        """
        if validate is not None:
            assert callable(validate), _('validate must be a callable object.')
        self._required = required
        self._validate = validate

    def load(self, context: ILoadingContext) -> Any:
        """Load this field.

        Args:
            context: instance of LoadingContext, managing the current
                     deserialization state.

        Return:
            Deserialized field value, or UNDEFINED if the loading failed.

        """
        field_value = self._load(context)

        validate = self._validate
        if validate is not None:
            validation_context = ValidationContext(context)
            validate(validation_context, field_value)
            if validation_context.has_error():
                return UNDEFINED

        return field_value

    @property
    def required(self) -> bool:
        return self._required

    @abstractmethod
    def _load(self, context: ILoadingContext) -> Any:
        raise NotImplementedError
