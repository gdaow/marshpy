"""Schema utilities tests."""
from typing import List
from typing import Optional

from pofy.core.schema import SchemaBase
from pofy.core.validation import ValidationContext

from tests.helpers import check_load


class _NoSchemaParent:
    pass


class _Parent(_NoSchemaParent):

    def __init__(self) -> None:
        super().__init__()
        self.calls: List[str] = []
        self.validation_context: Optional[ValidationContext] = None

    class Schema(SchemaBase):
        """Pofy fields."""

    def validate(self, context: ValidationContext) -> None:
        """Validate this object."""
        assert isinstance(context, ValidationContext)
        self.calls.append('parent_validate')
        self.validation_context = context

    def post_load(self) -> None:
        """Do post loading operation."""
        self.calls.append('parent_post_load')


class _Child(_Parent):

    class Schema(SchemaBase):
        """Pofy fields."""

    def validate(self, context: ValidationContext) -> None:
        """Validate this object."""
        assert isinstance(context, ValidationContext)
        self.calls.append('child_validate')

    def post_load(self) -> None:
        """Do post loading operation."""
        self.calls.append('child_post_load')


# Used to test complex hierarchy setups
class _NoSchemaSibling:
    pass


class _ChildNoHooks(_NoSchemaSibling, _Child):

    class Schema(SchemaBase):
        """Pofy fields."""


def test_hooks_called() -> None:
    """Validate and post load methods should be called on object."""
    obj = check_load("{}", _ChildNoHooks)
    assert obj.calls == [
        'parent_validate',
        'child_validate',
        'parent_post_load',
        'child_post_load'
    ]
