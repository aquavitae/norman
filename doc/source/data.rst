.. module:: norman

.. testsetup::

    from norman import *


Data Structures
===============

.. contents::


Norman data structures are build on four objects:  `Database`, `Table`, `Field`
and `Join`.  In overview, a `Database` is a collections of `Table` subclasses.
`Table` subclasses represent a tabular data structure where each column is
defined by a `Field` and each row is an instance of the subclass.  A `Join`
is similar to a `Field`, but behaves as a collection of related records::

    class Branch(Table):

        # Each branch knows its parent branch
        parent = Field(index=True)

        # Children are determined on the fly by searching for matching parents.
        children = Join(parent)


`AutoTable` is a special type of `Table` which automatically creates
fields dynamically.  This is used in conjunction with `AutoDatabase`,
is is particularly useful when de-serialising from a source without knowing
details of data in the source.


Database
--------

.. autoclass:: Database


    .. automethod:: add(table)


    .. automethod:: tablenames


    .. automethod:: reset


    .. automethod:: delete
    

.. autoclass:: AutoDatabase


Tables
------

Tables are implemented as a class, with records as instances of the class.
Accordingly, there are many class-level operations which are only applicable
to a `Table`, and others which only apply to records.  The class methods shown
in `Table` are not visible to instances.

.. autoclass:: Table

    The following class methods are supported by `Table` objects, but not by
    instances.  Tables also act as a collection of records,
    and support the following sequence operations:

    =============== ==========================================================
    Operation       Description
    =============== ==========================================================
    ``len(t)``      Return the number of records in ``t``.
    ``iter(table)`` Return an iterator over all records in ``t``.
    ``r in t``      Return `True` if the record ``r`` is an instance of (i.e.
                    contained by) table ``t``.  This should always return
                    `True` unless the record has been deleted from the table,
                    which usually means that it is a dangling reference which
                    should be deleted.
    =============== ==========================================================

    Boolean operations on tables evaluate to `True` if the table contains
    any records.

    .. attribute:: _store

        A `Store` instance used as a storage backend.  This may be overridden
        when the class is created to use a custom `Store` object.  Usually
        there is no need to use this.


    .. attribute:: hooks

        A `dict` containing lists of callables to be run when an event occurs.

        Two events are supported: validation on setting a field value and
        deletion, identified by keys ``'validate'`` and ``'delete'``
        respectively.  When a triggering event occurs, each hook in the list
        is called in order with the affected table instance as a single
        argument until an exception occurs.  If the exception is
        an `AssertionError` it is converted to a `ValueError`.  If no exception
        occurs, the event is considered to have passed, otherwise it fails
        and the table record rolls back to its previous state.

        These hooks are called before `Table.validate` and
        `Table.validate_delete`, and behave in the same way.  They may be set
        at any time, but do not affect records already created until
        the record is next validated.


    .. automethod:: delete([records=None])


    .. automethod:: fields


.. autoclass:: AutoTable


Records
^^^^^^^

Table instances, or records, are created by specifying field values as
keyword arguments.  Missing fields will use the default value (see `Field`).
In addition to the defined fields, records have the following properties and
methods.

.. autoattribute:: Table._uid


.. automethod:: Table.validate


.. automethod:: Table.validate_delete


Notes on Validation and Deletion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data is validated whenever a record is added or removed, and there is the
opportunity to influence this process through validation hooks.  When a
new record is created, there are three sets of validation criteria which
must pass in order for the record to actually be created.  The first step
is to run the validators specified in `Field.validators`.  These can change
or verify the value in each field independently of context.  The second
validation check is applied whenever there are unique fields, and confirms
that the combination of values in unique fields in actually unique.  The
final stage is to run all the validation hooks in `Table.hooks`.  These affect
the entire record, and may be used to perform changes across multiple fields.
If at any stage an Exception is raised, the record will not be created.

The following example illustrates how the validation occurs.  When a new
record is created, the value is first converted to a string by the field
validator, then checked for uniqueness, and finally the `validate`
method creates the extra *parts* value.

    >>> class TextTable(Table):
    ...     'A Table of text values.'
    ...
    ...     # A text value stored in the table
    ...     value = Field(unique=True, validators=[str])
    ...     # A pre-populated, calculated value.
    ...     parts = Field()
    ...
    ...     def validate(self):
    ...         self.parts = self.value.split()
    ...
    >>> r = TextTable(value='a string')
    >>> r.value
    'a string'
    >>> r.parts
    ['a', 'string']
    >>> r = TextTable(value=3)
    >>> r.value
    '3'
    >>> r = TextTable(value='3')
    Traceback (most recent call last):
        ...
    norman._except.ValidationError: Not unique: TextTable(parts=['3'], value='3')

When deleting a record, `Table.validate_delete` is first called.  This
should be used to ensure that any dependent records are dealt with.  For
example, the following code ensures that all children are deleted when
a parent is deleted.

    >>> class Child(Table):
    ...     parent = Field()
    ...
    >>> class Parent(Table):
    ...     children = Join(Child.parent)
    ...
    ...     def validate_delete(self):
    ...         for child in self.children:
    ...             Child.delete(child)
    ...
    >>> parent = Parent()
    >>> child = Child(parent=parent)
    >>> Parent.delete(parent)
    >>> len(Child)
    0

Fields
------

Fields are defined inside a `Table` definition as class attributes, and
are used as record properties for instances of a `Table`.  If the value of
a field has not been set, then the special object `NotSet` is used to
indicate this.

.. data:: NotSet

    A sentinel object indicating that the field value has not yet been set.
    This evaluates to `False` in conditional statements.


.. autoclass:: Field

    .. autoattribute:: default

    .. autoattribute:: key

    .. autoattribute:: name

    .. autoattribute:: owner

    .. autoattribute:: readonly

    .. autoattribute:: unique

    .. autoattribute:: validators


Joins
-----

A `Join` dynamically creates :doc:`queries` for a specific record.  This is best
explained through an example::

    >>> class Child(Table):
    ...     parent = Field()
    ...
    >>> class Parent(Table):
    ...     children = Join(Child.parent)
    ...
    >>> p = Parent()
    >>> c1 = Child(parent=p)
    >>> c2 = Child(parent=p)
    >>> set(p.children) == {c1, c2}
    True

In this example, `!Parent.children` returns a `Query` for all `!Child`
records where ``child.parent == parent_instance`` for a specific
``parent_instance``.  Joins have a `~Join.query` attribute which is a `Query`
factory function, returning a `Query` for a given instance of the owning table.


.. autoclass:: Join(*args, **kwargs)


    Joins have the following attributes, all of which are read-only.

    .. autoattribute:: jointable


    .. autoattribute:: name


    .. autoattribute:: owner


    .. autoattribute:: query


    .. autoattribute:: target


Exceptions and Warnings
-----------------------

Exceptions
^^^^^^^^^^

.. autoclass:: NormanError


.. class:: ConsistencyError

    Raised on a fatal inconsistency in the data structure.


.. class:: ValidationError

    Raised when an operation resulting in table validation failing.

    For now this inherits from `NormanError`, `ValueError` and `TypeError`
    to keep it backwardly compatible.  This will change in version 0.7.0


Warnings
^^^^^^^^

.. class:: NormanWarning

    Base class for all Norman warnings.

    Currently all warnings use this class.  In the future, this behaviour
    will change, and subclasses will be used.


Advanced API
------------

Two structures, `Store` and `Index` manage the data internally.  These are
documented for completeness, but should seldom need to be used directly.

.. autoclass:: Store
    :members:

.. autoclass:: Index
    :members: