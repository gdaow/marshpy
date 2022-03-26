"""Error handling tests."""
from typing import Type

from yaml import Node
from yaml.error import Mark

from marshpy.core.errors import (
    BadTypeFormatError,
    ErrorCode,
    FieldNotDeclaredError,
    ImportNotFoundError,
    MarshPyError,
    MarshPyValueError,
    MissingRequiredFieldError,
    MultipleMatchingHandlersError,
    SchemaError,
    TypeResolveError,
    UnexpectedNodeTypeError,
    ValidationError,
    get_exception_type,
)


def test_get_exception_type_is_correct() -> None:
    """Test exception type returned by get_exception_type is correct."""

    def _check(code: ErrorCode, exception: Type[MarshPyError]) -> None:
        assert get_exception_type(code) == exception

    _check(ErrorCode.BAD_TYPE_TAG_FORMAT, BadTypeFormatError)
    _check(ErrorCode.FIELD_NOT_DECLARED, FieldNotDeclaredError)
    _check(ErrorCode.MISSING_REQUIRED_FIELD, MissingRequiredFieldError)
    _check(ErrorCode.UNEXPECTED_NODE_TYPE, UnexpectedNodeTypeError)
    _check(ErrorCode.IMPORT_NOT_FOUND, ImportNotFoundError)
    _check(ErrorCode.TYPE_RESOLVE_ERROR, TypeResolveError)
    _check(ErrorCode.VALUE_ERROR, MarshPyValueError)
    _check(ErrorCode.VALIDATION_ERROR, ValidationError)
    _check(ErrorCode.MULTIPLE_MATCHING_HANDLERS, MultipleMatchingHandlersError)
    _check(ErrorCode.SCHEMA_ERROR, SchemaError)


def test_exception_format() -> None:
    """Test exception __str__ method gives usefull informations."""
    node = Node(
        "tag",
        "value",
        Mark("file_name", 0, 10, 42, None, 0),
        Mark("file_name", 0, 12, 32, None, 0),
    )

    message = "Error message"
    error = MarshPyError(node, message)

    location_string = "file_name:10:42"

    error_string = str(error)
    assert location_string in error_string
    assert message in error_string
