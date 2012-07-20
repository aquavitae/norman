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

Tables are implemented as a class, with records as instances of the class.
Accordingly, there are many class-level operations which are only applicable
to a `Table`, and others which only apply to records.  `Table` operations
are defined in `TableMeta`, the metaclass used to create `Table`.

.. class:: TableMeta

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
        an `AssertionError` it is converted to a `ValueError`.  If no exception
        occurs, the event is considered to have passed, otherwise it fails
        and the table record rolls back to its previous state.

        These hooks are called before `Table.validate` and
        `Table.validate_delete`, and behave in the same way.


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
        ...            T(id=9, value='a')]
        >>> sorted(t.id for t in T.get())
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> T.delete(records[:4], value='b')
        >>> sorted(t.id for t in T.get())
        [1, 3, 5, 6, 7, 8, 9]

        If no records are specified, then all are used.

        >>> T.delete(value='a')
        >>> sorted(t.id for t in T.get())
        [3, 5, 6, 7, 8]

        If no keywords are given, then all records in in *records* are deleted.

        >>> T.delete(records[2:5])
        >>> sorted(t.id for t in T.get())
        [6, 7, 8]

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
        data in the record is valid.  If not, an exception should be raised.
        Internal validate (e.g. uniqueness checks) occurs before this
        method is called, and a failure will result in a `ValidationError`
        being raised.  For convenience, any `AssertionError` which is raised
        here is considered to indicate invalid data, and is re-raised as a
        `ValidationError`.  This allows all validation errors (both from this
        function and from internal checks) to be captured in a single
        *except* statement.

        Values may also be changed in the method.  The default implementation
        does nothing.


    .. method:: validate_delete

        Raise an exception if the record cannot be deleted.

        This is called just before a record is deleted and is usually
        re-implemented to check for other referring instances.  This method
        can also be used to propogate deletions and can safely modify
        this or other tables.

        Exceptions are handled in the same was as for `validate`.


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

        `validate` for some pre-build validators.


Joins
-----

A join is basically an object which dynamically creates queries for
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


.. class:: Join(*args, **kwargs)

    A join, returning a `Query`.

    Joins can be created with the following arguments:

    ``Join(query=queryfactory)``
        Explicitly set the query factory.  `!queryfactory` is a callable which
        accepts a single argument and returns a `Query`.

    ``Join(table.field)``
        This is the most common format, since most joins simply involve looking
        up a field value in another table.  This is equivalent to specifying
        the following query factory::

            def queryfactory(value):
                return table.field == value

    ``Join(db, 'table.field`)``
        This has the same affect as the previous example, but is used when the
        foreign field has not yet been created.  In this case, the query
        factory first locates ``'table.field'`` in the `Database` ``db``.

    ``Join(other.join)``
        It is possible set the target of a join to another join, creating a
        *many-to-many* relationship.  When used in this way, a join table is
        automatically created, and can be accessed from `Join.jointable`.
        If the optional keyword parameter *jointable* is used, the join table
        name is set to it.

        .. seealso::

            http://en.wikipedia.org/wiki/Many-to-many_(data_model)
                For more information on *many-to-many* joins.


    .. attribute:: jointable

        The join table in a *many-to-many* join.

        This is `None` if the join is not a *many-to-many* join, and is
        read only.  If a jointable does not yet exist then it is created,
        but not added to any database.  If the two joins which define it have
        conflicting information, a `ConsistencyError` is raise.


    .. attribute:: name

        The name of the `Join`. This is read only.


    .. attribute:: owner

        The `Table` containing the `Join`.  This is read only.


    .. attribute:: query

        A function which accepts an instance of `owner` and returns a `Query`.


Exceptions and Warnings
-----------------------

Exceptions
^^^^^^^^^^

.. class:: NormanError

    Base class for all Norman exceptions.


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
