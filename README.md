# Pofy (Python yaml objects)

[![WTFPL license](https://img.shields.io/badge/License-WTFPL-blue.svg)](https://raw.githubusercontent.com/an-otter-world/pofy/master/COPYING)
[![Actions Status](https://github.com/an-otter-world/pofy/workflows/Checks/badge.svg)](https://github.com/an-otter-world/pofy/actions)
[![Coverage Status](https://coveralls.io/repos/github/an-otter-world/pofy/badge.svg)](https://coveralls.io/github/an-otter-world/pofy)
[![Matrix](https://img.shields.io/matrix/python-pofy:matrix.org?server_fqdn=matrix.org)](https://matrix.to/#/!SwCyFpSTQTLiPCNKTO:matrix.org?via=matrix.org)

Pofy is a tiny library on top of PyYAML, allowing to add semantic on top of YAML
and deserialize python object with data validation, custom field types, custom
deserialization behaviors with YAML tags, YAML file inclusion from other
files... Pofy was designed to allow easy declaration and utilisation of complex
configurations in python.

Pofy is distributed under the term of the WTFPL V2 (See COPYING file).

Contribution are very welcome. Don't hesitate to send pull requests. As English
isn't my native language, I'd be very happy with documentation correction or
improvements. Feel free to join [the Pofy channel on Matrix](https://matrix.to/#/!SwCyFpSTQTLiPCNKTO:matrix.org?via=matrix.org).

- [Pofy (Python yaml objects)](#pofy-python-yaml-objects)
  - [Installation](#installation)
  - [Quickstart](#quickstart)
  - [Reference](#reference)
    - [Fields](#fields)
      - [BoolField](#boolfield)
      - [StringField](#stringfield)
      - [IntField](#intfield)
      - [FloatField](#floatfield)
      - [EnumField](#enumfield)
      - [PathField](#pathfield)
      - [ObjectField](#objectfield)
      - [ListField](#listfield)
      - [DictField](#dictfield)
      - [Field Resolver](#field-resolver)
    - [Hooks](#hooks)
      - [Object Validation](#object-validation)
      - [Post Load](#post-load)
    - [Tag Handlers](#tag-handlers)
      - [env](#env)
      - [first-of](#first-of)
      - [glob](#glob)
      - [if](#if)
      - [import / try-import](#import--try-import)
      - [merge](#merge)
      - [Custom Tag Handlers](#custom-tag-handlers)
    - [Misc]
      - [ValidationContext](#validationcontext)
      - [Custom Error Handling](#custom-error-handling)

## Installation

Pofy is tested with Python 3.6 through 3.9. It can be installed through pip :

  `pip install pofy`

## Quickstart

The following minimum code declares a deserializable object and loads it from
a YAML document :

  ```python
      from pofy import StringField, load

      class Test:
          fields = {
              'some_field': StringField()
          }

      # > file.yaml :
      # some_field: value

      test = load('file.yaml', Test)
      assert test.some_field == 'value`
  ```

## Reference

### Fields

Although this behavior [can be customized](#field-resolver) to allow
deserialization of objects without adding intrusive class variable (for example,
to load classes of a third-party library), fields are be looked up by default as
a 'fields' class variable, which is expected to be a (string, field) dictionary.
Keys of the dictionary are the name of the field, i.e the name of the member
variable set on the loaded objects.

Pofy comes with predefined fields described in the following sections. You can
declare custom fields, to do so, refer to the [custom Fields][#custom-fields]
section.

#### Common Parameters

All field types accept the following parameters :

- **required (bool, optional) :** If set to true and the field is absent in the
  YAML document when the owning object is loaded, a MissingRequiredFieldError
  will be raised, or if you defined a [custom error handler](#error-handling),
  it will be called with the corresponding error code.

  ```python
    from pofy import StringField, load

    class Test:
        fields = {
          'required_field': StringField(required=True),
          'optional_field': StringField()
        }

    load('optional_field: some_value', Test) # Raises MissingRequiredFieldError
  ```

- **validate (callable, optional) :** Python callable accepting a
  ValidationContext and the value that was just deserialized, that will be
  called to perform custom validation checks on isolated field values. For more
  complex validation, involving multiple fields, validation checks can be also
  be performed on whole objects at once (see
  [Object Validation](#object-validation)).

  ```python
    from pofy import StringField, load
  
    def _validate(context, value):
  	  if value not in ['red', 'black']:
  	    context.error('Color not allowed')
  
    class Test:
      fields = {
  	    'color': StringField(validate=_validate)
      }
  
    load('color: yellow', Test) # Raises ValidationError
    load('color: black', Test) # OK
  ```

#### BoolField

BoolField loads a boolean from YAML. No additional parameter is available. The
following values are accepted when loading a boolean from YAML :

- For true : y, Y, yes, Yes, YES, true, True, TRUE, on, On, ON
- For false : n, N, no, No, NO, false, False, FALSE, off, Off, OFF

Any other value will raise a ValidationError, or call the defined
[error handler](#error-handling) with VALIDATION_ERROR as the error_code
parameter.

```python
  from pofy import BoolField, load

  class Test:
    class Schema:
      some_flag = BoolField()

  test = load('some_flag: on', Test)
  assert test.some_flag
  test = load('some_flag: NotValid', Test) # Raises ValidationError
```

#### StringField

StringField loads a string from YAML. The field constructor accept a 'pattern'
parameter, that must be a valid regular expression that deserialized values
should match. If pattern is defined and the deserialized values doesn't match
it, a ValidationError will be raised or the [error handler](#error-handling) you
defined will be called with ErrorCode.VALIDATION_ERROR as the error_code
parameter.

```python
  from pofy import StringField, load

  class Test:
    class Schema:
      string_field = StringField()
      pattern_field = StringField(pattern='[0-9]*')

  test = load('string_field: "foo bar"', Test)
  assert test.string_field == 'foo bar'
  test = load('pattern_field: NotValid', Test) # Raises ValidationError
  test = load('pattern_field: 10', Test)
  assert test.pattern_field == '10'
```

#### IntField

IntField loads an int from YAML. In addition to the common fields parameters,
it accept several parameters :

- base: An integer, giving the base to use when loading the integer. IntField
  uses the int(...) python function to get the integer, so even without this
  parameter, hexadecimal and octal notation are taken into account. Use this
  parameter if you don't want to have the 0x or 0o prefix in front of the
  number, or if you want to use an exotic base.
- minumum, maximum : Acceptable boundaries for the loaded value. If the value
  is out of bounds, a ValidationError will be raised, or the defined
  [error handler](#error-handling) will be called with
  ErrorCode.VALIDATION_ERROR as the error_code parameter.

```python
  from pofy import IntField, load

  class Test:
    class Schema:
      int_field = IntField(minimum=0, maximum=16)
      hex_field = IntField(base=16)

  assert load('int_field: 10', Test).int_field == 10
  assert load('int_field: 0xF', Test).int_field == 15
  assert load('int_field: 0o12', Test).int_field == 12
  assert load('int_field: 100', Test) # Raises ValidationError
  assert load('hex_field: F', Test).hex_field == 15
```

#### FloatField

Float Field loads a float from YAML. In addition to the common fields
parameters, it accept several specific ones :

- minumum, maximum : Acceptable boundaries for the loaded value. If the value
  is out of bounds, a ValidationError will be raised, or the defined
  [error handler](#error-handling) will be called with
  ErrorCode.VALIDATION_ERROR as the error_code parameter.

```python
  from pofy import FloatField, load

  class Test:
    class Schema:
      float_field = FloatField(minimum=.0, maximum=10.0)

  assert load('float_field: 10.0', Test).float_field == 10
  assert load('int_field: 100.0', Test) # Raises ValidationError
```

#### EnumField

Enum Field loads a python Enum from yaml. Values of the enum are refered to by
their name. In addition to the common fields parameters, it accept the following
specific one :

- enum_class (required) : The class of the python enum to deserialize.

If the value in Yaml does not match any declared value of the enum, a
ValidationError will be raised, or the defined [error handler](#error-handling)
will be called with ErrorCode.VALIDATION_ERROR as the error_code parameter.

```python
  from enum import Enum
  from pofy import EnumField, load

  class TestEnum(Enum):
    VALUE_1 = 1
    VALUE_2 = 2

  class Test:
    class Schema:
      enum_field = EnumField(TestEnum)

  assert load('enum_field: VALUE_1', Test).enum_field == TestEnum.VALUE_1
  assert load('enum_field: UNKNOWN_VALUE', Test) # Raises ValidationError
```

#### PathField

PathField will load a pathlib.Path object from the YAML. In addition to the
common fields parameters, it accept the following specific one :

- must_exist (bool) : If set to True and the deserialized path don't point to an
  existing file or folder, a ValidationError will be raised, or the defined
  [error handler](#error-handling) will be called with
  ErrorCode.VALIDATION_ERROR as the error_code parameter.

If the path in the YAML document is relative, and doesn't exists relatively to
the current working dir, Pofy will try to resolve it relatively to the current
deserialized YAML file's directory (if it's a file that's being deserialized and
not, say, a string).

```python
  from pathlib import Path
  from pofy import PathField, load

  class Test:
    class Schema:
      path_field = PathField()
      checked_field = PathField(must_exist=True)

  test = load('path_field: "/absolute/path"', Test)
  assert test.path_field == Path('/absolute/path')

  test = load('checked_field: /i/dont/exist', Test) # Raises ValidationError

  # /home/test/file.yaml : 
  #  > path_field: relative/path
  test = load('/home/test/file.yaml', Test)
  assert test.path_field == Path('/home/test/relative/path')
  # (Only if that file actually exists)

```

#### ObjectField

ObjectField will load a custom pythn object from the YAML. The deserialized
object class should provide a schema, by declaring a nested 'Schema' class in
the deserialized's object class, or by any mean you configured through the
[schema resolver](#schema-resolver) parameter of the load function. The type of
the object to deserialize can be provided in YAML, with the !type tag (see
example below), or by configuring the default type of the field in the
ObjectField constructor. If no type is defined (no object_class given to the
ObjectField constructor, and no type defined in the YAML), the field will not
be loaded. So in addition to the common fields parameters, it accepts the
following specific one :

- object_class : Type[Any] optional : Default type of the object to load, if not
  provided in YAML through the !type tag.

```python
  from pofy import ObjectField, StringField, load

  class Child:
    class Schema:
      name = StringField()

  class ChildSubClass(Child):
    class Schema:
       child_field = StringField()
  
  class Parent:
    class Schema:
      child = ObjectField(Child)

  test = load(
    'child:\n'
    '  name: 'child_name',
    Parent
  )

  assert isinstance(test.child, Child)
  assert test.child.name == 'child_name'

  test = load(
    'child: !type python.module.ChildSubClass\n'
    '  name: 'child_name'
    '  child_field: 'child_field_value',
    Parent
  )

  assert isinstance(test.child, ChildSubClass)
  assert test.child.name == 'child_name'
  assert test.child.child_field == 'child_field_value'

```

#### ListField

ListField will load a list from the YAML. In addition to the common fields
parameters, it accept the following specific one :

- item_field (Field) : The field used to load each item in the list.

Here is an example of how should be declared the schema of an object having a
list of another object as member :

```python
  from pofy import ListField, ObjectField, load

  class Child:
    class Schema:
      name = StringField()

  class Parent:
    class Schema:
      children = ListField(
        ObjectField(Child)
      )

  parent = load(
    'children:'
    '  - name: first_child'
    '  - name: second_child',
    Parent
  )

  assert isinstance(parent.child[0], Child)
  assert isinstance(parent.child[1], Child)
  assert parent.child[0].name == 'first_child'
  assert parent.child[1].name == 'second_child'

```

#### DictField

DictField will load a dictionary from the YAML. Only strings are supported as
keys for now. In addition to the common fields parameters, it accept the
following specific one :

- item_field (Field) : The field used to load each item's value in the list.

Here is an example of how should be declared the schema of an object having a
dictionary of another object as member :

```python
  from pofy import DictField, ObjectField, load

  class Child:
    class Schema:
      name = StringField()

  class Parent:
    class Schema:
      children = DictField(
        ObjectField(Child)
      )

  parent = load(
    'children:'
    '  first:
    '    name: first_child'
    '  second:',
    '    name: second_child',
    Parent
  )

  assert isinstance(parent.child['first'], Child)
  assert isinstance(parent.child['second'], Child)
  assert parent.child['first'].name == 'first_child'
  assert parent.child['second'].name == 'second_child'

```

#### Field Resolver

The default behavior to resolve schemas for a given type is to search for a
nested class called 'Schema'. This behavior can be overrided by passing a
callable to the load function as the 'schema_resolver' parameter. This callable
will be called with the type to deserialize and should return a schema for this
type, or None if not was found. This allows to deserialize types without having
to intrusively declare Schema in it, for example if you want to deserialize
objects declared in a third-party library. Here is an example of a
schema_resolver searching in a dictionnary to resolve schemas.

```python
  from pofy import load, StringField

  class Class:
    pass

  class ClassSchema:
    color = StringField()

  SCHEMA_MAPPING = {
    Class: ClassSchema
  }

  def custom_schema_resolver(type: Type[Any]) -> Type[Any]:
    return SCHEMA_MAPPING[type]

  ...

  obj = load(Class, schema_resolver=custom_schema_resolver)

```

### Hooks

#### Object Validation

When an object is loaded by Pofy, if a 'validate' class method is defined on the
Schema class, it will be called with a ValidationContext and the deserialized
object as arguments. The ValidationContext exposes the following methods :

- current_location() : If the current YAML document was loaded from a file,
  returns that file path, else returns None

- error(message_format, *args, **kwargs) : Will raise a ValidationError, or
  or the defined [error handler](#error-handling) will be called with
  ErrorCode.VALIDATION_ERROR as the error_code parameter, and the given string
  format formatted with *args and **kwargs as message.

If no error_handler is defined when loading a YAML document, an exception will
be raised, terminating the loading at the first call of error(). However, if
some custom error handling is set up, the execution will continue after the
first validation error, so be aware of that when writing validation methods.

Here is an example of the declaration of a validation method :

```python
  from pofy import StringField, ValidationContext

  class Test:
    class Schema:
      color = StringField()

      def validate(cls, context: ValidationContext, obj: Any):
        assert isinstance(obj, Test)
        if obj.color not in ['red', 'green', 'blue']:
          context.error('Color not allowed')

```

#### Post Load

In the same fashion the [validate](#object-validation) method can be declared,
a 'post_load' method will be called if it exists on the Schema class upon
object loading. The only argument will be the deserialized object :

```python
  from pofy import StringField

  class Test:
    class Schema:
      color = StringField()

      def post_load(cls, obj: Any):
        assert isinstance(obj, Test)
        obj.color = obj.color.toupper()

```

### Tag Handlers

Tag handlers are custom deserialization behaviors that are triggered when 
encountering specific YAML tags. Pofy comes with some predefined tag handlers
that are automatically registered when calling load, so the following tags are
usable out of the box :

#### env

The env tag can be set on a YAML string value, and will load the value of the
environment variable named like the tagged string. If the environment variable
isn't set, the Pofy field will not be set either, allowing to eventually
fallback on a default value (see [first-of](#first-of) for example).

If this tag is set on another value than a YAML scalar value, an
UnexpectedNodeTypeError will be raised, or the defined
[error handler](#error-handling) will be called with
ErrorCode.UNEXPECTED_NODE_TYPE as the error_code parameter.

```python
  from pofy import StringField, load

  class Test:
    class Schema:
      string_field = StringField()

  test = load('string_field: !env PATH', Test)
  assert test.string_field == '/bin:/usr/bin:/usr/local/bin'

  test = load('string_field: !env UNKNOWN_ENV_VAR', Test)
  assert not hasattr(test, 'string_field')

  # Will raise UnexpectedNodeTypeError
  test = load('string_field: !env [oops]', Test) 

```

#### first-of

The first-of tag can be set on a YAML list value, and will load the first value
of the list that is not undefined. This can be used with [the env tag](#env),
[the if tag](#if) or the [try-import tag](#import-try--import) to provide
fallback values for fields, for example.

If this tag is set on another value than a YAML list value, an
UnexpectedNodeTypeError will be raised, or the defined
[error handler](#error-handling) will be called with
ErrorCode.UNEXPECTED_NODE_TYPE as the error_code parameter.

```python

  from pofy import StringField, load

  class Test:
    class Schema:
      color = StringField()

  test = load(
    'string_field: !first-of'
    ' - !env ENV_COLOR'
    ' - default_color',
    Test
  )

  assert test.color == 'red' # if ENV_COLOR is set to red
  assert test.color == 'default_color' # if ENV_COLOR is not defined

```

#### glob

The glob tag can be set on a YAML string value, and will load all the YAML
documents that matches the tagged pattern as a YAML list. The pattern is
relatively to all configured roots (see below), and the current YAML document
directory, if the YAML is loaded from a file. The Pofy load method accepts a
'resolve_roots' arguments, as a list of path that glob and [import](#import)
tags should use as root when searching for files.

If this tag is set on another value than a YAML scalar value, an
UnexpectedNodeTypeError will be raised, or the defined
[error handler](#error-handling) will be called with
ErrorCode.UNEXPECTED_NODE_TYPE as the error_code parameter.

```python

  from pofy import StringField, ListField, ObjectField, load

  class Child:
    class Schema:
      color = StringField()

  class Parent:
    class Schema:
      children = ListField(
        ObjectField(Child)
      )

  # /root/parent.yaml
  # > children: !glob *_child.yaml

  # /root/child_1.yaml
  # > color: red

  # /include/child_2.yaml
  # > color: green

  test = load('parent.yaml', Test, resolve_roots=['/include'])

  assert isinstance(test.children[0], Child)
  assert isinstance(test.children[1], Child)
  assert test.children[0].color == 'red'
  assert test.children[1].color == 'green'

```

#### if

The 'if' tag can be set on any YAML value, and will load the tagged node only
if the given flag was defined, through the 'flags' parameter of the Pofy load
method. If the flag is not defined, the field will not be set at all. This tag
is usefull in conjonction with the [first-of](#first-of) tag.

```python

  from pofy import StringField

  class Test:
    class Schema:
      color = StringField()

  test = load('color: !if(SET_FLAG) red', Test, flags={'SET_FLAG'})
  assert test.color == 'red'

  test = load('color: !if(UNSET_FLAG) red', Test, flags={'SET_FLAG'})
  assert not hasattr(test, 'color')

```

#### import / try-import

The import and try-import tags can be set on a YAML string value, and will load
the given YAML document as the field value. The file path is evaluated
relatively to all configured roots (see below), and the current YAML document
directory, if the YAML is loaded from a file. The Pofy load method accepts a
'resolve_roots' arguments, as a list of path that import and [glob](#glob)
tags use as root when searching for files. If a file matching the given path
cannot be found relatively (if the pass is relative) to the current YAML
directory, or any of the resolve_roots items, import will raise a
ImportNotFoundError, or the defined [error handler](#error-handling) will be
called with ErrorCode.IMPORT_NOT_FOUND as the error_code parameter. Try import
will not load any value, but will not raise any error.

If this tag is set on another value than a YAML scalar value, an
UnexpectedNodeTypeError will be raised, or the defined
[error handler](#error-handling) will be called with
ErrorCode.UNEXPECTED_NODE_TYPE as the error_code parameter.

```python

  from pofy import StringField, ListField, ObjectField, load

  class Child:
    class Schema:
      color = StringField()

  class Parent:
    class Schema:
      child = ObjectField(Child)

  # /root/parent.yaml
  # > children: !import child.yaml

  # /root/child.yaml
  # > color: red

  test = load('parent.yaml', Test)

  assert isinstance(test.child, Child)
  assert test.child.color == 'red'

```

#### merge

The merge tag can be set on a YAML list value, and will merge return the merge
of all the item in the list, as a dictionnary or list.

```python

  from pofy import StringField, ListField, load

  class Parent:
    class Schema:
      colors = ListField(StringField())

  test = load(
    'colors:',
    ' - { 'blue', 'green' }
    ' - { 'red', 'green' }',
    Test
  )

  assert test.colors = ['blue', 'green', 'red', 'green']

```

#### Custom Tag Handlers

Pofy allows you to plug custom deserialization behavior when encountering some
YAML tags, matching a given regular expression. These custom behaviors are
called tag handlers, and are declared this way tag handlers are defined the
following way :

```python

from pofy import TagHandler
from pofy import ILoadingContext
from pofy import IBaseField

class ReverseHandler(TagHandler):
    tag_pattern = '^reverse$' # Regex pattern that this tag handler matches

    def load(self, context: ILoadingContext, field: IBaseField) \
            -> Any:
        # Check that the type of the node is correct, and fail if not :
        if not context.expect_scalar(
            _('!reverse must be set on a string node.')
        ):
            return UNDEFINED

        # Return the value of the current yaml node reversed.
        node = context.current_node()
        return node.value.reverse()

```

Check the API reference to see the methods available on ILoadingContext and
IBaseField, representing the currently deserialized field.

Before using it in YAML, the handler should be registered when calling the pofy
'load' methods through the 'tag_handlers' arguments :

```python

  class Test:
    class Schema:
      string_field = StringField()

  test = load(
    'string_field: !reverse Hello world',
    Test,
    tag_handlers=[ReverseHandler()]
  )
  assert test.string_field == 'dlrow olleH'

```

### Misc

#### ValidationContext

#### Custom Error Handling

By default, Pofy will raise an exception when an error is encountered. This
behavior can be overrided by passing a callable as the 'error _handler'
parameter of the load(...) function. this callable should accept a
Pofy.ErrorCode and a string giving more information on the error. The error_code
parameter can be one of the following ErrorCode enum values :

 - BAD_TYPE_TAG_FORMAT :        A malformed [!type tag](#object-field) was
                                encountered.

 - FIELD_NOT_DECLARED :         An unknown field was encountered in YAML

 - MISSING_REQUIRED_FIELD :     A required field was not set in YAML

 - UNEXPECTED_NODE_TYPE :       An unexpected type of node was encountered (for
                                example, a list when loading a string field, or
                                a scalar after a !merge tag).

 - IMPORT_NOT_FOUND:            An [!import tag](#import-try--import) couldn't
                                find the given file.

 - TYPE_RESOLVE_ERROR :         Couldn't find the type given by a
                                [!type tag](#object-field)

 - VALUE_ERROR :                A value couldn't be parsed (for example, bad
                                integer format)

 - VALIDATION_ERROR :           Validation failed (either from built-in features
                                like the [pattern parameter of
                                [StringField](#string-field), or from custom
                                [validation callbacks](#object-validation)

 - MULTIPLE_MATCHING_HANDLERS : The [tag handler](#custom-tag-handler) to choose
                                for a tag is ambiguous. This is raised at
                                parsing time, not when registering handlers, as
                                tag handlers are matched with regular
                                expressions.

 - SCHEMA_ERROR = 10 :          A schema for a type couldn't be found.

