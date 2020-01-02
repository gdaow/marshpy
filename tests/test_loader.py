"""Yaml object loading tests."""
from pofy import ErrorCode
from pofy import ListField
from pofy import ObjectField
from pofy import StringField
from pofy import load

from .fixtures import expect_load_error


def test_unknown_field_raise_error():
    """Test an undeclared field in YAML raises an error."""
    class _EmptyObject:
        class Schema:
            """Pyfo fields."""

    expect_load_error(
        ErrorCode.FIELD_NOT_DECLARED,
        'uknown_field: 10',
        _EmptyObject,
    )


def test_unset_required_field_raise_error():
    """Test an unset required field in YAML raise an error."""
    class _RequiredFieldObject:
        class Schema:
            """Pofy fields."""

            required = StringField(required=True)
            not_required = StringField()

    expect_load_error(
        ErrorCode.MISSING_REQUIRED_FIELD,
        'not_required: some_value',
        _RequiredFieldObject,
    )

    test = load(
        'required: setted\n'
        'not_required: yodeldi',
        _RequiredFieldObject,
    )
    assert test.required == 'setted'
    assert test.not_required == 'yodeldi'


def test_load_subclass():
    """Test fields declared in parent classes are loaded."""
    class _Parent:
        class Schema:
            """Pyfo fields."""

            parent_field = StringField()

    class _Child(_Parent):
        class Schema:
            """Pyfo fields."""

            child_field = StringField()

    test = load(
        'parent_field: parent_value\n' +
        'child_field: child_value',
        _Child,
    )

    assert test.parent_field == 'parent_value'
    assert test.child_field == 'child_value'


def test_error_on_bad_node():
    """Test load raises an error on bad node."""
    class _DummyObject:
        class Schema:
            """Pyfo fields."""

            some_field = StringField()

    expect_load_error(
        ErrorCode.UNEXPECTED_NODE_TYPE,
        '- item1\n'
        '- item2',
        _DummyObject,
    )


def test_resolve_root_works(datadir):
    """Test giving a path as resolve_root instanciates default tag handlers."""
    class _Owned:
        class Schema:
            """Pyfo fields."""

            test_field = StringField()

    class _Owner:
        class Schema:
            """Pyfo fields."""

            object_field = ObjectField(object_class=_Owned)
            object_list = ListField(
                ObjectField(object_class=_Owned)
            )

    test = load(
        'object_field: !import object.yaml\n',
        _Owner,
        resolve_roots=[datadir]
    )

    assert isinstance(test.object_field, _Owned)
    assert test.object_field.test_field == 'test_value'

    test = load(
        'object_list: !glob glob_directory/*.yaml\n',
        _Owner,
        resolve_roots=[datadir]
    )

    assert len(test.object_list) == 2
    assert isinstance(test.object_list[0], _Owned)
    assert isinstance(test.object_list[1], _Owned)
    assert test.object_list[0].test_field == 'test_value'
    assert test.object_list[1].test_field == 'test_value'


def test_object_validation_works():
    """Test object validation methods are executed."""

    class _ValidatedObject:
        class Schema:
            """Pofy fields."""

            dont_set_me = StringField()

            @classmethod
            def validate(cls, context, obj):
                """Validate loaded objects."""
                if obj.dont_set_me is not None:
                    context.error(ErrorCode.VALIDATION_ERROR, 'Error')
                return False

        def __init__(self):
            """Initialize."""
            self.dont_set_me = None

    class _ValidatedObjectChild(_ValidatedObject):
        class Schema:
            """Pofy fields."""

            @classmethod
            def validate(cls, __, ___):
                """Validate loaded objects."""
                return True

    expect_load_error(
        ErrorCode.VALIDATION_ERROR,
        'dont_set_me: Wathever',
        _ValidatedObjectChild,
    )
