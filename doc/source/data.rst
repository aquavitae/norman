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
is similar to a `Field`, but behaves as a collection of related records.
A tree-like structure would make extensive used of `Join`\ s::

    class Branch(Table):

        # Each branch knows its parent branch
        parent = Field(index=True)

        # Children are determined on the fly by searching for matching parents.
        children = Join(parent)


Database
--------

.. autoclass:: Database


    .. automethod:: add(table)


    .. automethod:: tablenames


    .. automethod:: reset


Tables
------

Tables are implemented as a class, with records as instances of the class.
Accordingly, there are many class-level operations which are only applicable
to a `Table`, and others which only apply to records.  The class methods shown
in `Table` are not visible to instances.

.. autoclass:: Table


Table objects
^^^^^^^^^^^^^

The following class methods are supported by `Table` objects, but not by
instances (i.e. records).  Tables also act as a collection of records,
and support limited sequence-like interface, with rapid lookup through
indexed fields.  ``len(table)`` returns the number of records in the
table, and ``iter(table)`` returns an iterator over all records in the table.
``record in table`` is also supported and returns `True` if the instance
*record* is in the table.  This is usually used as a sanity check, since
records should always be contained in the table.  To avoid problems, use
`Table.validate_delete` to automatically clean dangling references.


.. attribute:: Table._store

    A `Store` instance used as a storage backend.  This may be overridden
    when the class is created to use a customised `Store` object.


.. attribute:: Table.hooks

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
    `Table.validate_delete`, and behave in the same way.


.. automethod:: Table.delete([records=None])


.. automethod:: Table.fields


Records
^^^^^^^

Table instances, or records, are created by specifying field values as
keyword arguments.  Missing fields will use the default value (see `Field`).
In addition to the defined fields, records have the following properties and
methods.

.. autoattribute:: Table._uid


.. automethod:: Table.validate


.. automethod:: Table.validate_delete


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


Joins
-----

A `Join` is basically an object which dynamically creates queries for
a specific record.  This is best explained through an example::

    >>> class Child(Table):
    ...     parent = Field()
    ...
    >>> class Parent(Table):
    ...     children = Join(Child.parent)
    ...
    >>> p = Parent()
    >>> c1 = Child(parent=p)
    >>> c2 = Child(parent=p)
    >>> p.children
    {c1, c2}

Here, `!Parent.children` is a factory which returns a `Query` for all
`!Child` records where ``child.parent == parent_instance`` for a specific
`!parent_instance`.  Joins have a `~Join.query` attribute which is a `Query`
factory, returning a `Query` for a given instance of the owning table.


.. autoclass:: Join(*args, **kwargs)

Joins have the following attributes.

.. autoattribute:: Join.jointable


.. autoattribute:: Join.name


.. autoattribute:: Join.owner


.. autoattribute:: Join.query


.. autoattribute:: Join.target


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
============

Two structures, `Store` and `Index` manage the data internally.  These are
documented for completeness, but should seldom need to be used directly.

.. autoclass:: Store
    :members:

.. autoclass:: Index
    :members: