"""Validation related class & utilities."""
from typing import Any
from typing import Optional
from typing import Callable

from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import ILoadingContext


ValidateCallback = Callable[['ValidationContext', Any], None]


class ValidationContext:
    """Wrapper around LoadingContext exposing validation usefull features."""

    def __init__(self, loading_context: ILoadingContext):
        """Initialize validation context."""
        self._has_error = False
        self._loading_context = loading_context

    def current_location(self) -> Optional[str]:
        """Return the location of the document owning the current node.

        If no path can be found, returs None.
        """
        return self._loading_context.current_location()

    def error(
        self,
        message_format: str,
        *args: Any,
        **kwargs: Any
    ) -> None:
        """Raise a validation error with the given format & args.

        Args:
            message_format: The error message format.
            *args, **kwargs: Arguments used to format message.

        """
        self._has_error = True
        self._loading_context.error(
            ErrorCode.VALIDATION_ERROR,
            message_format,
            *args,
            **kwargs
        )

    def has_error(self) -> bool:
        """Return true if the error was called at least once."""
        return self._has_error
