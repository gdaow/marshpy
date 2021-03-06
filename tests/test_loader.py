"""Yaml object loading tests."""
from io import StringIO
from pathlib import Path
from typing import Any, Dict, Optional

from yaml import Node

from marshpy.core.constants import UNDEFINED
from marshpy.core.errors import ErrorCode
from marshpy.core.interfaces import IBaseField, ILoadingContext
from marshpy.fields.list_field import ListField
from marshpy.fields.object_field import ObjectField
from marshpy.fields.string_field import StringField
from marshpy.loader import load
from marshpy.tag_handlers.path_handler import PathHandler
from tests.helpers import FailTagHandler


def test_resolve_root_works(datadir: Path) -> None:
    """Resolve root should be forwarded to glob and import tag handler."""

    class _Owned:
        fields = {"test_field": StringField()}

        test_field: Optional[str] = None

    class _Owner:
        fields = {
            "object_field": ObjectField(object_class=_Owned),
            "object_list": ListField(ObjectField(object_class=_Owned)),
        }

        def __init__(self) -> None:
            self.object_field = None
            self.object_list = None

    test = load(
        "object_field: !import object.yaml\n",
        _Owner,
        config=[PathHandler.Config(roots=[datadir])],
    )
    assert isinstance(test, _Owner)
    assert isinstance(test.object_field, _Owned)
    assert test.object_field.test_field == "test_value"

    test = load(
        "object_list: !glob glob_directory/*.yaml\n",
        _Owner,
        config=[PathHandler.Config(roots=[datadir])],
    )

    assert isinstance(test, _Owner)
    assert len(test.object_list) == 2
    assert isinstance(test.object_list[0], _Owned)
    assert isinstance(test.object_list[1], _Owned)
    assert test.object_list[0].test_field == "test_value"
    assert test.object_list[1].test_field == "test_value"


def test_root_field_is_correctly_inferred() -> None:
    """Root field should be inferred from object_class."""
    assert load("on", bool)
    assert load("10", int) == 10
    assert load("10.0", float) == 10.0
    assert load("string_value", str) == "string_value"
    test_list = load("- item_1\n" "- item_2", list)

    assert test_list == ["item_1", "item_2"]

    test_dict = load("key_1: value_1\n" "key_2: value_2\n", dict)

    assert test_dict == {"key_1": "value_1", "key_2": "value_2"}


def test_tag_handler_fails_on_root_node_returns_none() -> None:
    """Nothing shoud be deserialized when loading root node fails."""
    result = load("!fail some_value", str, tag_handlers=[FailTagHandler()])
    assert result is UNDEFINED


def test_load_handles_stream(datadir: Path) -> None:
    """It should be correct to give a stream as source parameter for load."""
    with open(datadir / "object.yaml", encoding="utf-8") as yaml_file:
        test = load(yaml_file, dict)
        assert test == {"test_field": "test_value"}

    test = load(StringIO("test_field: test_value"), dict)
    assert test == {"test_field": "test_value"}


def test_load_defines_node_path(datadir: Path) -> None:
    """Calling load with a stream should set the location of the root node."""
    file_path = datadir / "object.yaml"
    validate_called = False

    class _TestObject:

        fields = {"test_field": StringField()}

        @classmethod
        def validate(cls, context: ILoadingContext) -> None:
            """Validate that context as correct current_node_path."""
            nonlocal validate_called
            validate_called = True
            assert context.current_location() == str(file_path)

    with open(file_path, encoding="utf-8") as yaml_file:
        load(yaml_file, _TestObject)
        assert validate_called


def test_error_hanlder_is_called() -> None:
    """The given error_handler should be called when defined."""
    handler_called = False

    def _handler(_: Node, __: ErrorCode, ___: str) -> None:
        nonlocal handler_called
        handler_called = True

    load("[a, list]", str, error_handler=_handler)
    assert handler_called


def test_schema_resolver_is_called() -> None:
    """The given schema_resolver should be called when defined."""
    resolver_called = False

    class _Object:
        def __init__(self) -> None:
            self.string_field = "default value"

    def _field_resolver(obj: Any) -> Dict[str, IBaseField]:
        nonlocal resolver_called
        if obj.__class__ == _Object:
            resolver_called = True
            return dict(string_field=StringField())
        return {}

    result = load(
        "string_field: value",
        object_class=_Object,
        config=[ObjectField.Config(fields_resolver=_field_resolver)],
    )

    assert resolver_called
    assert isinstance(result, _Object)
    assert result.string_field == "value"
