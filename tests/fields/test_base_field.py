"""Yaml object loading tests."""
from pofy.core.errors import ErrorCode
from pofy.core.validation import ValidationContext
from pofy.fields.string_field import StringField

from tests.helpers import check_field_error


def test_field_validation() -> None:
    """Custom field validation should behave correctly."""
    def _validate(context: ValidationContext, _: str) -> None:
        assert isinstance(context, ValidationContext)
        context.error('Test')

    class _Test:
        fields = {
            'field': StringField(validate=_validate)
        }

    check_field_error(
        _Test,
        'field',
        'value',
        ErrorCode.VALIDATION_ERROR
    )
