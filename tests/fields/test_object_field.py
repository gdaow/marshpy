"""Object field tests."""
from typing import Any
from typing import Optional

from pofy.core.constants import UNDEFINED
from pofy.core.errors import ErrorCode
from pofy.core.validation import ValidationContext
from pofy.fields.bool_field import BoolField
from pofy.fields.object_field import ObjectField
from pofy.fields.string_field import StringField

from tests.helpers import check_field_error
from tests.helpers import check_load


class _Owned:

    fields = {
        'required_field': StringField(required=True),
        'error': BoolField()
    }

    def __init__(self) -> None:
        """Initialize object."""
        self.required_field: Optional[str] = None
        self.parent_validate_called = False
        self.parent_post_load_called = False

    def validate(self, context: ValidationContext) -> None:
        """Validate."""
        if getattr(self, 'error', False):
            context.error('Error')
            return
        self.parent_validate_called = True

    def post_load(self) -> None:
        """Postload."""
        self.parent_post_load_called = True


class _OwnedChild(_Owned):

    fields = {
        'child_field': StringField()
    }

    def __init__(self) -> None:
        """Initialize object."""
        super().__init__()
        self.child_field: Optional[str] = None
        self.child_validate_called = False
        self.child_post_load_called = False

    def validate(self, context: ValidationContext) -> None:
        """Validate."""
        super().validate(context)
        self.child_validate_called = True

    def post_load(self) -> None:
        """Postload."""
        super().post_load()
        self.child_post_load_called = True


class _Owner:

    fields = {
        'field': ObjectField(object_class=_Owned)
    }

    def __init__(self) -> None:
        """Initialize _Owner."""
        self.field: Optional[_Owned] = None
        self.post_load_called = False
        self.validate_called = False

    def validate(self, __: ValidationContext) -> None:
        """Validate loaded objects."""
        self.validate_called = True

    def post_load(self) -> None:
        """Post load."""
        self.post_load_called = True


class _ValidationError:

    @classmethod
    def validate(cls, _: Any, context: ValidationContext, __: Any) -> None:
        """Validate loaded objects."""
        context.error('Error')


class _NoFields:
    pass


class _Simple:
    fields = {
        'field': StringField()
    }


def _check_field_error(yaml_value: str, expected_error: ErrorCode) -> None:
    check_field_error(_Owner, 'field', yaml_value, expected_error)


def test_object_field() -> None:
    """Object field should load correct values."""
    result = check_load(
        'field: !type:tests.fields.test_object_field._OwnedChild\n'
        '  required_field: parent_value\n'
        '  child_field: child_value\n',
        _Owner,
    )
    assert isinstance(result, _Owner)
    assert isinstance(result.field, _OwnedChild)
    assert result.field.required_field == 'parent_value'
    assert result.field.child_field == 'child_value'
    assert result.field.parent_validate_called
    assert result.field.parent_post_load_called
    assert result.field.child_validate_called
    assert result.field.child_post_load_called

    result = check_load('field: value\n', _Simple)
    assert hasattr(result, 'field')
    assert result.field == 'value'

    result = check_load('field: !fail value\n', _Simple)
    assert not hasattr(result, 'field')

    result = check_load('!fail field: value\n', _Simple)
    assert not hasattr(result, 'field')


def test_object_field_error_handling() -> None:
    """Object field should correctly handle errors."""
    _check_field_error('scalar_value', ErrorCode.UNEXPECTED_NODE_TYPE)
    _check_field_error('[a, list]', ErrorCode.UNEXPECTED_NODE_TYPE)

    _check_field_error('!type:dont.Exists {}', ErrorCode.TYPE_RESOLVE_ERROR)
    _check_field_error('!type:os.not_a_module {}', ErrorCode.TYPE_RESOLVE_ERROR)
    # Not a class
    _check_field_error('!type:os.abort {}', ErrorCode.TYPE_RESOLVE_ERROR)

    _check_field_error('!typebad.Format {}', ErrorCode.BAD_TYPE_TAG_FORMAT)
    _check_field_error('!type:bad:Format {}', ErrorCode.BAD_TYPE_TAG_FORMAT)
    _check_field_error('!type:bad {}', ErrorCode.BAD_TYPE_TAG_FORMAT)

    _check_field_error(
        '{ required_field: value, unknown_field: value }',
        ErrorCode.FIELD_NOT_DECLARED
    )

    _check_field_error(
        '{ required_field: value, error: On }',
        ErrorCode.VALIDATION_ERROR
    )

    _check_field_error('{ }', ErrorCode.MISSING_REQUIRED_FIELD)

    obj = check_load('{ }', _NoFields, ErrorCode.SCHEMA_ERROR)
    assert obj == UNDEFINED
