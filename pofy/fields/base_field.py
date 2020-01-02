"""Base field class & utilities."""
from abc import abstractmethod
from gettext import gettext as _
from typing import Any
from typing import Callable
from typing import Union

from yaml import ScalarNode

from pofy.errors import ErrorCode
from pofy.loading_context import LoadingContext


class BaseField:
    """Base class for YAML object fields."""

    def __init__(
        self,
        required: bool = False,
        validate: Callable = None
    ):
        """Initialize the field.

        Args:
            required: If it's true and the field is not defined in yaml, it
                      will create an error that will eventually be raised at
                      the end of deserialization.
            validate: Function accepting a Node, LoadingContext and the
                      deserialized field value, that should return True if the
                      value is valid, false otherwise, and call context.error
                      to report errors, eventually using the
                      ErrorCode.VALIDATION_ERROR code.

        """
        self.required = required
        self._validate = validate

    def load(self, context: LoadingContext) -> Any:
        """Deserialize this field.

        Args:
            node: YAML node containing field value.
            context: Loading context, handling include resolving and error
                     management.

        Return:
            Deserialized field value.

        """
        node = context.current_node()

        if node.tag == '!include':
            if not isinstance(node, ScalarNode):
                context.error(
                    ErrorCode.UNEXPECTED_NODE_TYPE,
                    _('!include tag must be on a scalar node')
                )
                return None

            location = node.value
            node = context.resolve(location)
            if node is None:
                context.error(
                    ErrorCode.INCLUDE_NOT_FOUND,
                    _("Can't resolve include {}"), location
                )
                return None

            with context.push(node):
                field_value = self._load(context)

        else:
            field_value = self._load(context)

        validate = self._validate
        if validate is not None and not validate(context, field_value):
            return None

        return field_value

    @abstractmethod
    def _load(self, context: LoadingContext) -> Any:
        """Deserialize this field using the given node.

        Args:
            node: YAML node containing field value.
            context: Loading context, handling include resolving and error
                     management.

        Return:
            Deserialized field value.

        """
        raise NotImplementedError


class ScalarField(BaseField):
    """Base class for scalar value fields."""

    def _load(self, context):
        node = context.current_node()
        if not isinstance(node, ScalarNode):
            context.error(
                ErrorCode.UNEXPECTED_NODE_TYPE,
                _('Scalar expected')
            )
            return None

        return self._convert(context)

    @abstractmethod
    def _convert(self, context: LoadingContext) -> Any:
        """Convert the string value to the target type of this field.

        Args:
            context: The loading context.

        Return:
            The converted value.

        """
        raise NotImplementedError

    @staticmethod
    def _check_in_bounds(
        context: LoadingContext,
        value: Union[int, float],
        minimum: Union[int, float],
        maximum: Union[int, float]
    ):
        if minimum is not None and value < minimum:
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _('Value is too small (minimum : {})'), minimum
            )
            return None

        if maximum is not None and value > maximum:
            context.error(
                ErrorCode.VALIDATION_ERROR,
                _('Value is too big (maximum : {})'), maximum
            )
            return None

        return value