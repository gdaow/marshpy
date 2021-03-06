"""MarshPy error handling related classes & definitions."""
from enum import Enum
from typing import Callable, Type

from yaml import Node


class ErrorCode(Enum):
    """MarshPy error codes."""

    # Raised when a !type tag isn't correctly formed.
    BAD_TYPE_TAG_FORMAT = 1

    # Raised when an unknown field is encountered in yaml.
    FIELD_NOT_DECLARED = 2

    # Raised when a required field isn't set in yaml.
    MISSING_REQUIRED_FIELD = 3

    # Raised when a node type isn't the one expected for a field.
    UNEXPECTED_NODE_TYPE = 4

    # Raised when an !import tag can't be resolved.
    IMPORT_NOT_FOUND = 5

    # Raised when a !type tags doesn't resolve to a valid python type.
    TYPE_RESOLVE_ERROR = 6

    # Raised when a value can't be parsed.
    VALUE_ERROR = 7

    # Generic error code for validation errors.
    VALIDATION_ERROR = 8

    # Raised when several handlers matches a tag
    MULTIPLE_MATCHING_HANDLERS = 9

    # Raised when an object schema is incorrect
    SCHEMA_ERROR = 10


ErrorHandler = Callable[[Node, ErrorCode, str], None]


class MarshPyError(Exception):
    """Exception raised when errors occurs during object loading."""

    def __init__(self, node: Node, message: str):
        """Initialize the error.

        Arg:
            node : The node on which the errTypeor occured.
            code : The error code of the error.
            message : The error description message.

        """
        super().__init__(MarshPyError._get_message(node, message))
        self.node = node

    @staticmethod
    def _get_message(node: Node, message: str) -> str:
        start = node.start_mark
        file_name = getattr(start, "name", "<Unkwnown>")
        return f"{file_name}:{start.line}:{start.column} : {message}"


class BadTypeFormatError(MarshPyError):
    """Exception type raised for BAD_TYPE_FORMAT error code."""


class FieldNotDeclaredError(MarshPyError):
    """Exception type raised for FIELD_NOT_DECLARED error code."""


class MissingRequiredFieldError(MarshPyError):
    """Exception type raised for MISSING_REQUIRED_FIELD error code."""


class UnexpectedNodeTypeError(MarshPyError):
    """Exception type raised for UNEXPECTED_NODE_TYPE error code."""


class ImportNotFoundError(MarshPyError):
    """Exception type raised for IMPORT_NOT_FOUND error code."""


class TypeResolveError(MarshPyError):
    """Exception type raised for TYPE_RESOLVE_ERROR error code."""


class MarshPyValueError(MarshPyError):
    """Exception type raised for VALUE_ERROR error code."""


class ValidationError(MarshPyError):
    """Exception type raised for VALIDATION_ERROR error code."""


class MultipleMatchingHandlersError(MarshPyError):
    """Exception type raised for MULTIPLE_MATCHING_HANDLER error code."""


class SchemaError(MarshPyError):
    """Exception type raised for MULTIPLE_MATCHING_HANDLER error code."""


_CODE_TO_EXCEPTION_TYPE_MAPPING = {
    ErrorCode.BAD_TYPE_TAG_FORMAT: BadTypeFormatError,
    ErrorCode.FIELD_NOT_DECLARED: FieldNotDeclaredError,
    ErrorCode.MISSING_REQUIRED_FIELD: MissingRequiredFieldError,
    ErrorCode.UNEXPECTED_NODE_TYPE: UnexpectedNodeTypeError,
    ErrorCode.IMPORT_NOT_FOUND: ImportNotFoundError,
    ErrorCode.TYPE_RESOLVE_ERROR: TypeResolveError,
    ErrorCode.VALUE_ERROR: MarshPyValueError,
    ErrorCode.VALIDATION_ERROR: ValidationError,
    ErrorCode.MULTIPLE_MATCHING_HANDLERS: MultipleMatchingHandlersError,
    ErrorCode.SCHEMA_ERROR: SchemaError,
}


def get_exception_type(error_code: ErrorCode) -> Type[MarshPyError]:
    """Get exception type that should be raised for a given error code.

    Args:
        error_code : The error code.

    """
    assert error_code in _CODE_TO_EXCEPTION_TYPE_MAPPING
    return _CODE_TO_EXCEPTION_TYPE_MAPPING[error_code]
