"""Yaml object loading tests."""
from pofy import StringField
from pofy import LoadingContext
from pofy import ErrorCode

from tests.helpers import check_field_error


def test_field_validation():
    """Custom field validation should behave correctly."""
    def _validate(context: LoadingContext, _: str):
        context.error(ErrorCode.VALIDATION_ERROR, 'Test')
        return False

    class _ValidateFieldObject:

        class Schema:
            """Pofy fields."""

            validated_field = StringField(validate=_validate)

    check_field_error(
        _ValidateFieldObject,
        'validated_field',
        'value',
        ErrorCode.VALIDATION_ERROR
    )
