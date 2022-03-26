"""Container field class & utilities."""
from abc import abstractmethod
from gettext import gettext as _
from typing import Any, Optional

from marshpy.core.interfaces import ILoadingContext
from marshpy.core.validation import ValidateCallback
from marshpy.fields.base_field import BaseField


class ContainerField(BaseField):
    """Field containing nested objects."""

    def __init__(
        self,
        item_field: BaseField,
        required: bool = False,
        validate: Optional[ValidateCallback] = None,
    ):
        """Initialize the container field.

        Arg:
            item_field: Field used to load nested items.
            required: See BaseField constructor.
            validate: See BaseField constructor.

        """
        super().__init__(required=required, validate=validate)
        assert isinstance(item_field, BaseField), _(
            "item_field must be an implementation of BaseField."
        )
        self._item_field = item_field

    @abstractmethod
    def _load(self, context: ILoadingContext) -> Any:
        raise NotImplementedError
