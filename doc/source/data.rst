.. module:: norman

.. testsetup::

    from norman import *


Data Structures
===============

.. contents::


Database
--------
`Database` instances act as containers of `Table` objects, and support
``__getitem__``, ``__contains__`` and ``__iter__``.  ``__getitem__``
returns a table given its name (i.e. its class name), ``__contains__``
returns whether a `Table` object is managed by the database and
``__iter__`` returns a iterator over the tables.

Tables may be added to the database when they are created by using
`Database.add` as a class decorator.  For example::

    >>> db = Database()
    >>> @db.add
    ... class MyTable(Table):
    ...     name = Field()
    >>> MyTable in db
    True

The database can be written to a file through the `serialise` module.
Currently only sqlite3 is supported.  If a `Database` instance represents
a document state, it can be saved using the following code:

.. doctest::
    :options: +SKIP

    >>> serialise.Sqlite.dump(db, 'file.sqlite')

And reloaded:

.. doctest::
    :options: +SKIP

    >>> serialise.Sqlite.load(db, 'file.sqlite')


.. class:: Database

    The main database class containing a list of tables.


    .. method:: add(table)

        Add a `Table` class to the database.

        This is the same as including the *database* argument in the
        class definition.  The table is returned so this can be used as
        a class decorator.

        >>> db = Database()
        >>> @db.add
        ... class MyTable(Table):
        ...     name = Field()


    .. method:: tablenames:

        Return an list of the names of all tables managed by the database.


    .. method:: reset

        Delete all records from all tables.


Tables
------

Tables are instances of the `TableMeta` metaclass, and records are instances
of tables.  Methods which apply to tables, therefore, are defined in
`TableMeta`.


.. class TableMeta

    Base metaclass for all tables.

    Tables support a limited sequence-like interface, with rapid lookup
    through indexed fields.  The sequence operations supported are ``__len__``,
    ``__contains__`` and ``__iter__``, and all act on instances of the table,
    i.e. records.


    .. attribute:: hooks

        A `dict` containing lists of callables to be run when an event occurs.

        Two events are supported: validation on setting a field value and
        deletion, identified by keys ``'validate'`` and ``'delete'``
        respectively.  When a triggering event occurs, each hook in the list
        is called in order with the affected table instance as a single
        argument until an exception occurs.  If the exception is
        an `AssertError` it is converted to a `ValueError`.  If no exception
        occurs, the event is considered to have passed, otherwise it fails
        and the table record rolls back to its previous state.

        These hooks are called after `validate` and `validate_delete`, but
        behave in the same way.


    .. method:: contains(**kwargs)

        Return `True` if the table contains any records with field values
        matching *kwargs*.


    .. method:: delete([records=None,] **keywords)

        Delete delete all instances in *records* which match *keywords*.

        If *records* is omitted then the entire table is searched.  For
        example:

        >>> class T(Table):
        ...     id = Field()
        ...     value = Field()
        >>> records = [T(id=1, value='a'),
        ...            T(id=2, value='b'),
        ...            T(id=3, value='c'),
        ...            T(id=4, value='b'),
        ...            T(id=5, value='b'),
        ...            T(id=6, value='c'),
        ...            T(id=7, value='c'),
        ...            T(id=8, value='b'),
        ...            T(id=9, value='a'),
        >>> [t.id for t in T.get()]
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> T.delete(records[:4], value='b')
        >>> [t.id for t in T.get()]
        [1, 3, 5, 6, 7, 8, 9]

        If no records are specified, then all are used.

        >>> T.delete(value='a')
        >>> [t.id for t in T.get()]
        [3, 5, 6, 7, 8]

        If no keywords are given, then all records in in *records* are deleted.

        >>> T.delete(records[2:4])
        >>> [t.id for t in T.get()]
        [3, 5, 8]

        If neither records nor keywords are deleted, then the entire
        table is cleared.


    .. method:: fields

        Return an iterator over field names in the table.


    .. method:: get(**kwargs)

        Return a `set` of for all records with field values matching *kwargs*.


    .. method:: iter(**kwargs)

        Iterate over records with field values matching *kwargs*.


.. class:: Table(**kwargs)

    Each instance of a Table subclass represents a record in that Table.

    This class should be subclassed to define the fields in the table.
    It may also optionally provide `validate` and `validate_delete` methods.

    `Field` names should not start with ``_``, as these names are reserved
    for internal use.  Fields may be added to a `Table` after the `Table`
    is created, provided they do not already belong to another `Table`, and
    the `Field` name is not already used in the `Table`.


    .. attribute:: _uid

        This contains an id which is unique in the session.

        It's primary use is as an identity key during serialisation.  Valid
        values are any integer except 0, or a UUID.  The default
        value is calculated using `uuid.uuid4` upon its first call.
        It is not necessarily required that it be universally unique.


    .. method:: validate

        Raise an exception if the record contains invalid data.

        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, and exception should be raised.
        Internal validate (e.g. uniqueness checks) occurs before this
        method is called, and a failure will result in a `ValueError` being
        raised.  For convenience, any `AssertionError` which is raised here
        is considered to indicate invalid data, and is re-raised as a
        `ValueError`.  This allows all validation errors (both from this
        function and from internal checks) to be captured in a single
        *except* statement.

        Values may also be changed in the method.  The default implementation
        does nothing.


    .. method:: validate_delete

        Raise an exception if the record cannot be deleted.

        This is called just before a record is deleted and is usually
        re-implemented to check for other referring instances.  For example,
        the following structure only allows deletions of *Name* instances
        not in a *Grouper*.

        >>> class Name(Table):
        ...     name = Field()
        ...     group = Field(default=None)
        ...
        ...     def validate_delete(self):
        ...         assert self.group is None, "Can't delete '{}'".format(self.group)
        ...
        >>> class Grouper(Table):
        ...     id = Field()
        ...     names = Group(Name, lambda s: {'group': s})
        ...
        >>> group = Grouper(id=1)
        >>> n1 = Name(name='grouped', group=group)
        >>> n2 = Name(name='not grouped', group=None)
        >>> Name.delete(name='not grouped')
        >>> Name.delete(name='grouped')
        Traceback (most recent call last):
            ...
        ValueError: Can't delete 'grouped'
        >>> {name.name for name in Name.get()}
        {'grouped'}

        Exceptions are handled in the same was as for `validate`.

        This method can also be used to propogate deletions and can safely
        modify this or other tables.


Fields
------

.. data:: NotSet

    A sentinel object indicating that the field value has not yet been set.

    This evaluates to `False` in conditional statements.


.. class:: Field

    A `Field` is used in tables to define attributes of data.

    When a table is created, fields can be identified by using a `Field`
    object:

    >>> class MyTable(Table):
    ...     name = Field()

    `Field` objects support *get* and *set* operations, similar to
    *properties*, but also provide additional options.  They are intended
    for use with `Table` subclasses.

    Field options are set as keyword arguments when it is initialised

    ========== ============ ===================================================
    Keyword    Default      Description
    ========== ============ ===================================================
    unique     False        True if records should be unique on this field.
                            In database terms, this is the same as setting
                            a primary key.  If more than one field have this
                            set then records are expected to be unique on all
                            of them.  Unique fields are always indexed.
    index      False        True if the field should be indexed.  Indexed
                            fields are much faster to look up.  Setting
                            ``unique = True`` implies ``index = True``
    default    None         If missing, `NotSet` is used.
    readonly   False        Prohibits setting the variable, unless its value
                            is `NotSet`.  This can be used with *default*
                            to simulate a constant.
    validate   None         If set, should be a list of functions which are
                            to be used as validators for the field.  Each
                            function should accept a and return a single value,
                            and should raise an exception if the value is
                            invalid.  The return value is the value passed
                            to the next validator.
    ========== ============ ===================================================

    Note that *unique* and *index* are table-level controls, and are not used
    by `Field` directly.  It is the responsibility of the table to
    implement the necessary constraints and indexes.

    Fields have read-only properties, *name* and *owner* which are
    set to the assigned name and the owning table respectively when
    the table class is created.

    Fields can be used with comparison operators to return a `Query`
    object containing matching records.  For example::

        >>> class MyTable(Table):
        ...     oid = Field(unique=True)
        ...     value = Field()
        >>> t0 = MyTable(oid=0, value=1)
        >>> t1 = MyTable(oid=1, value=2)
        >>> t2 = MyTable(oid=2, value=1)
        >>> Table.value == 1
        Query(MyTable(oid=0, value=1), MyTable(oid=2, value=1))

    The following comparisons are supported for a `Field` object: ``==``,
    ``<``, ``>``, ``<=``, ``>==``, ``!=``.  The ``&`` operator is used to
    test for containment, e.g. `` Table.field & mylist`` returns all records
    where the value of ``field`` is in ``mylist``.

    .. seealso::

        `validators` for some pre-build validators.


.. class:: Join(*args)

    A special field representing a one-to-many join to another table.

    This is best explained through an example::

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

    The initialisation parameters specify the field in the foreign table which
    contains a reference to the owning table, and may be specified in one of
    two ways.  If the foreign table is already defined (as in the above
    example), then only one argument is required.  If it has not been
    defined, or is self-referential, the first agument may be the database
    instance and the second the canonical field name, including the table
    name.  So an alternate definition of the above *Parent* class would be::

        >>> db = Database()
        >>> @db.add
        ... class Parent(Table):
        ...     children = Join(db, 'Child.parent')
        ...
        >>> @db.add
        ... class Child(Table):
        ...     parent = Field()
        ...
        >>> p = Parent()
        >>> c1 = Child(parent=p)
        >>> c2 = Child(parent=p)
        >>> p.children
        {c1, c2}

    As with a `Field`, a `Join` has read-only attributes *name* and *owner*.
