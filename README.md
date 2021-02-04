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
    - [Schemas](#schemas)
      - [Object Validation](#object-validation)
      - [Post Load Hook](#post-load-hook)
      - [SchemaBase](#schemabase)
      - [Schema Resolver](#schema-resolver)
    - [Fields](#fields)
      - [Common Parameters](#common-parameters)
      - [BoolField](#boolfield)
      - [StringField](#stringfield)
      - [IntField](#intfield)
      - [FloatField](#floatfield)
      - [EnumField](#enumfield)
      - [PathField](#pathfield)
      - [ObjectField](#objectfield)
      - [ListField](#listfield)
      - [DictField](#dictfield)
    - [Tag Handlers](#tag-handlers)
      - [env](#env)
      - [first-of](#first-of)
      - [glob](#glob)
      - [if](#if)
      - [import / try-import](#import--try-import)
      - [merge](#merge)
      - [Custom Tag Handlers](#custom-tag-handlers)
    - [Custom Error Handling](#custom-error-handling)
    - [Creating Custom Fields](#creating-custom-fields)

## Installation

Pofy is tested with Python 3.6 through 3.9. It can be installed through pip :

  `pip install pofy`

## Quickstart

Pofy fields are defined in a Schema class, which is by default an inner class of
the object you want to deserialize, called 'Schema'. The schema resolution can
be customized through the [schema resolver](#schema-resolver) parameter of the
load method, allowing to declare schema for existing classes without being
intrusive.

Once you declare the schema, you can load objects with the 'load' method :

  ```python
      from pofy import StringField, load

      class Test:
          class Schema:
              field = StringField()

      test = load(SomeObject, 'field: value')
      assert test.field == 'value`
  ```

## Reference

### Schemas

Schemas are python classe declaring how a python type should be deserialized
from YAML. They can contain a list of [fields](#fields) as class members, as
showed in the [quickstart section](#quickstart). They can declare hook methods
that can be used for object validation and post-load operations. By default, the
Schema for a python class is looked up by searching for a nested class named
'Schema'. This behavior is customizable through the
[schema_resolver](#schema-resolver) argument passed to the load() method.

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

#### SchemaBase

Pofy provides a SchemaBase class, but it's usage is facultative. It sole purpose
is to call the [validate](#object-validation) and [post_load](#post-load)
methods directly on the deserialized object, rather than on the schema class :

```python
  from pofy import StringField, ValidationContext, SchemaBase

  class Test:
    class Schema(SchemaBase):
      color = StringField()

    def validate(self, context: ValidationContext):
      assert isinstance(obj, Test)
      if not color in ['red', 'green', 'blue']:
        context.error('Color not allowed')
    
    def post_load(self):
      assert isinstance(obj, Test)
      obj.color = obj.color.toupper()

```

Notice that in the case your objects inherits from another deserializable object
with a Schema inheriting from SchemaBase, you don't have to call
super().validate(...) and super.post_load(), as the Schema at each level of
inheritance will already do it :


```python
  from pofy import StringField, ValidationContext, SchemaBase

  class Parent:
    class Schema(SchemaBase):
      color = StringField()

    def validate(self, context: ValidationContext):
      ...
    
    def post_load(self):
      ...

  class Child:
    class Schema(SchemaBase):
      child_color = StringField()

    def validate(self, context: ValidationContext):
      # don't call super().validate(context) here, it will already be called by 
      # Parent.Schema
      ...
    
    def post_load(self):
      # don't call super().post_load() here, it will already be called by 
      # Parent.Schema
      ...

```

#### Schema Resolver

### Fields

Pofy comes with predefined fields described below. You can declare custom
fields, to do so, refer to the [custom Fields][#custom-fields] section.

#### Common Parameters

All field types accept a 'required' boolean parameter. If it's set and the field
is absent in the YAML document, a MissingRequiredFieldError will be raised, or
the [error handler](#error-handling) you defined will be called with
ErrorCode.MISSING_REQUIRED_FIELD as the error_code parameter :

```python
  from pofy import StringField, load

  class Test:
    class Schema:
      required_field = StringField(required=True)
      optional_field = StringField()

  load('optional_field: some_value', Test) # Raises MissingRequiredFieldError
```

All field types accept a 'validate' parameter. It must be a python callable
object accepting a ILoadingContext , the field deserialized value, and must
return a boolean if the field is valid, false other wise. See
[object validation](#object-validation) for details about ILoadingContext, and
on how to add informations to validation failure. If the validation fails, pofy
will raise a ValidationError or the [error handler](#error-handling) you defined
will be called with ErrorCode.VALIDATION_ERROR as the error_code parameter.
Whole loaded objects can also be validated at once using the
[object validation](#object-validation) system.

```python
  from pofy import StringField, load

  def _validate(context, value):
    if value not in ['red', 'green', 'blue']:
      return False

    return True

  class Test:
    class Schema:
      color = StringField(validate=_validate)

  load('color: yellow', Test) # Raises ValidationError
  load('color: blue', Test) # Raises ValidationError
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

#### glob

#### if

#### import / try-import

#### merge

The import and try import tags allows to import another YAML file as a field of
the currently deserialized object :

#### Custom tag handlers

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

### Custom Error Handling

### Creating Custom Fields

A field should always return object of the same type (MergeHandler expects this)
