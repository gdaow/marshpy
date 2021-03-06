"""Import handler tests."""
from pathlib import Path

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.tag_handlers.import_handler import ImportHandler
from tests.tag_handlers.path_handler_helpers import check_path_tag, check_path_tag_error


def test_import_tag_handler(datadir: Path) -> None:
    """Import tag should load file if set correctly."""
    check_path_tag(ImportHandler, "!import file_1.yaml", ["file_1"], roots=[datadir])

    check_path_tag(
        ImportHandler, "!try-import file_1.yaml", ["file_1"], roots=[datadir]
    )

    root_1 = datadir / "test_ignore_dir" / "root_1"
    root_2 = datadir / "test_ignore_dir" / "root_2"
    check_path_tag(
        ImportHandler, "!import file_2.yaml", ["file_2"], roots=[root_1, root_2]
    )

    # Shouldn't emit an error
    check_path_tag(ImportHandler, "!try-import doesnt_exists", UNDEFINED)

    check_path_tag(
        ImportHandler,
        "!import file_1.yaml",
        ["file_1"],
        allow_relative=True,
        location=datadir / "parent_file.yaml",
    )

    check_path_tag_error(
        ImportHandler,
        "!import file_1.yaml",
        ErrorCode.IMPORT_NOT_FOUND,
        allow_relative=False,
        location=str(datadir / "parent_file.yaml"),
    )

    check_path_tag(ImportHandler, f"!import {datadir / 'file_1.yaml'}", ["file_1"])


def test_import_tag_handler_error_handling(datadir: Path) -> None:
    """Import tag handler shoud correctly handle errors."""
    check_path_tag_error(ImportHandler, "!import []", ErrorCode.UNEXPECTED_NODE_TYPE)

    check_path_tag_error(ImportHandler, "!import {}", ErrorCode.UNEXPECTED_NODE_TYPE)

    check_path_tag_error(
        ImportHandler,
        "!import doest_exists",
        ErrorCode.IMPORT_NOT_FOUND,
        roots=[datadir],
    )

    check_path_tag_error(
        ImportHandler, "!import yaml_error.yaml", ErrorCode.VALUE_ERROR, roots=[datadir]
    )
