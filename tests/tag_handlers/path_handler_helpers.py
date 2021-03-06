"""Helpers to test path handlers."""
from pathlib import Path
from typing import Any, List, Optional, Type

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.fields.list_field import ListField
from marshpy.fields.string_field import StringField
from marshpy.tag_handlers.path_handler import PathHandler
from tests.helpers import check_load


def check_path_tag(
    handler_type: Type[PathHandler],
    yaml: str,
    expected_value: Any,
    allow_relative: bool = True,
    location: Optional[Path] = None,
    roots: Optional[List[Path]] = None,
) -> None:
    """Path tag hanhler inherited tags test helper."""
    result = check_load(
        yaml,
        field=ListField(StringField()),
        tag_handlers=[handler_type(allow_relative=allow_relative)],
        config=[
            PathHandler.Config(
                roots=[] if roots is None else roots,
            )
        ],
        location=str(location),
    )

    # for glob tag handler.
    if isinstance(expected_value, list):
        assert sorted(result) == sorted(expected_value)
    else:
        assert result == expected_value


def check_path_tag_error(
    handler_type: Type[PathHandler],
    yaml: str,
    expected_error: ErrorCode,
    location: Optional[str] = None,
    allow_relative: bool = True,
    roots: Optional[List[Path]] = None,
    expected_value: Any = UNDEFINED,
) -> None:
    """Path tag hanhler inherited tags error test helper."""
    result = check_load(
        yaml,
        field=ListField(StringField()),
        expected_error=expected_error,
        location=location,
        tag_handlers=[handler_type(allow_relative=allow_relative)],
        config=[PathHandler.Config(roots)],
    )

    assert result == expected_value
