.. module:: norman

.. testsetup::

    from norman import *
    

Norman Documentation
====================

**Norman** provides a framework for creating database-like structures.
It doesn't, however, link into any database API (e.g. sqlite) and
doesn't support SQL syntax.  It is intended to be used as a lightweight,
in-memory framework allowing complex data structures, but without
the restrictions imposed by formal databases.  It should not be seen as
in any way as a replacement for, e.g., sqlite or postgreSQL, since it
services a different requirement.

One of the main distinctions between this framework and a SQL database is
in the way relationships are managed.  In a SQL database, each record
has one or more primary keys, which are typically referred to in other,
related tables by foreign keys.  Here, however, keys do not exist, and
records are linked directly to each other as attributes.

The main containing class is `Database`, and an instance of this should be
created before creating any tables it contains.  Tables are subclassed
from the `Table` class and fields added to it by creating `Field` class
attributes.


Example
-------

Here is a brief, but complete example of a database structure::
    
    db = Database()
    
    class Person(Table, database=db):
        custno = Field(unique=True)
        name = Field(index=True)
        age = Field(default=20)
        address = Field(index=True)
    
        def validate(self):
            if not isinstance(self.age, int):
                self.age = tools.int2(self.age, 0)
            assert isinstance(self.address, Address)
    
    class Address(Table, database=db):
        street = Field(unique=True)
        town = Field(unique=True)
    
        @property
        def people(self):
            return Person.get(address=self)
    
        def validate(self):
            assert isinstance(self.town, Town)
    
    class Town(Table, database=db):
        name = Field(unique=True)


Database
--------

.. class:: Database

    The main database class containing a list of tables.

    Tables may be added to the database when they are created by giving
    the class a *database* keyword argument.  For example

    >>> db = Database()
    >>> class MyTable(Table, database=db):
    ...     name = Field()
    >>> MyTable in db
    True

    The `add` method can also be used as a class decorator to add the `Table`
    to a database.
    
    `Database` instances act as containers of `Table` objects, and support
    ``__getitem__``, ``__contains__`` and ``__iter__``.  ``__getitem__``
    returns a table given its name (i.e. its class name), ``__contains__``
    returns whether a `Table` object is managed by the database and
    ``__iter__`` returns a iterator over the tables.
    
    The database can be written to a sqlite database as file storage.  So
    if a `Database` instance represents a document state, it can be saved
    using the following code:

    >>> db.tosqlite('file.sqlite')

    And reloaded thus:

    >>> db.fromsqlite('file.sqlite')

    :note:
        The sqlite database created does not contain any constraints
        at all (not even type constraints).  This is because the sqlite
        database is meant to be used purely for file storage.

    In the sqlite database, all values are saved as strings (determined
    from ``str(value)``.  Keys (foreign and primary) are globally unique
    integers > 0.  *None* is stored as *NULL*, and *NotSet* as 0.
    

    .. method:: add(table)
    
        Add a `Table` class to the database.  This is the same as including
        the *database* argument in the class definition.  The table is 
        returned so this can be used as a class decorator 
        
        >>> db = Database()
        >>> @db.add
        ... class MyTable(Table):
        ...     name = Field()
        
        
    .. method:: tablenames:
    
        Return an list of the names of all tables managed by the database.
        

    .. method:: reset
    
        Delete all records from all tables.


    .. method:: tosqlite(filename)
        
        Dump the database to a sqlite database.

        Each table is dumped to a sqlite table, without any constraints.
        All values in the table are converted to strings and foreign objects
        are stored as an integer id (referring to another record). Each
        record has an additional field, '_oid_', which contains a unique
        integer.


    .. method:: fromsqlite(filename)
    
        The database supplied is read as follows:

        1.  Tables are searched for by name, if they are missing then
            they are ignored.

        2.  If a table is found, but does not have an "oid" field, it is
            ignored

        3.  Values in "oid" should be unique within the database, e.g.
            a record in "units" cannot have the same "oid" as a record
            in "cycles".

        4.  Records which cannot be added, for any reason, are ignored
            and a message logged.


Tables
------

.. class TableMeta

    Base metaclass for all tables.
    
    The methods provided by this metaclass are essentially those which apply
    to the table (as opposed to those which apply records).
    
    Tables support a limited sequence-like interface, with rapid lookup 
    through indexed fields.  The sequence operations supported are ``__len__``,
    ``__contains__`` and ``__iter__``, and all act on instances of the table,
    i.e. records.  


    .. method:: iter(**kwargs)
    
        A generator which iterates over records with field values matching 
        *kwargs*.  
        

    .. method:: contains(**kwargs)
        
        Return `True` if the table contains any records with field values
        matching *kwargs*.


    .. method:: get(**kwargs)
        
        Return a set of all records with field values matching *kwargs*.


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


.. class:: Table(**kwargs)

    Each instance of a Table subclass represents a record in that Table.
    
    This class should be inherited from to define the fields in the table.
    It may also optionally provide a `validate` method.
 
 
    .. method:: validate
    
        Raise an exception if the record contains invalid data.
        
        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, and exception should be raised.
        Internal validate (e.g. uniqueness checks) occurs before this
        method is called, and a failure will result in a `ValueError` being
        raised.  For convience, any `AssertionError` which is raised here
        is considered to indicate invalid data, and is re-raised as a 
        `ValueError`.  This allows all validation errors (both from this 
        function and from internal checks) to be captured in a single
        `except` statment.
          
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
        
                
Fields
------

.. data:: NotSet

    A sentinel object indicating that the field value has not yet been set.
    This evaluates to False in conditional statements.
    
    
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
    ========== ============ ===================================================
    
    Note that *unique* and *index* are table-level controls, and are not used
    by `Field` directly.  It is the responsibility of the table to
    implement the necessary constraints and indexes.


Groups
------

.. class:: Group(table[, matcher=None], **kwargs)

    This is a collection class which represents a collection of records.
    
    :param table:   The table which contains records returned by this `Group`.
    :param matcher: A callable which returns a dict. This can be used
                    instead of *kwargs* if it needs to be created dynamically. 
    :param kwargs:  Keyword arguments used to filter records.
    
    If *matcher* is specified, it is called with a single argument 
    to update *kwargs*.  The argument passed to it is the instance of the 
    owning table, so this can only be used where `Group` is in a class.
    
    `Group` is a set-like container, closely resembling a `Table`
    and supports ``__len__``, ``__contains__`` and ``__iter__``.
    
    This is typically used as a field type in a `Table`, but may be used 
    anywhere where a dynamic subset of a `Table` is needed.
    
    The easiest way to demonstrating usage is through an example.  This 
    represents a collection of *Child* objects contained in a *Parent*.
    
    .. doctest::
    
        >>> class Child(Table):
        ...     name = Field()
        ...     parent = Field()
        ...     
        ...     def __repr__(self):
        ...         return "Child('{}')".format(self.name)
        ...         
        >>> class Parent(Table):
        ...     children = Group(Child, lambda self: {'parent': self})
        ...
        >>> parent = Parent()
        >>> a = Child(name='a', parent=parent)
        >>> b = Child(name='b', parent=parent)
        >>> len(parent.children)
        2
        >>> parent.children.get(name='a')
        {Child('a')}
        >>> parent.children.iter(name='b')
        <generator object iter at ...>
        >>> parent.children.add(name='c')
        Child('c')


    .. attribute:: table
    
        Read-only property containing the `Table` object referred to by 
        this collection.
        
    
    .. method:: iter(**kwargs)
    
        A generator which iterates over records in the `Group` with 
        field values matching *kwargs*.  
        

    .. method:: contains(**kwargs)
        
        Return `True` if the `Group` contains any records with field values
        matching *kwargs*.


    .. method:: get(**kwargs)
        
        Return a set of all records with field values matching *kwargs*.


    .. method:: add(**kwargs)
    
        Create a new record of the reference table using *kwargs*, updated
        the keyword arguments defining this `Group`.
        
        
    .. method:: delete([records=None,] **keywords)
        
        Delete delete all instances in *records* which match *keywords*.
        This only deletes instances in the `Group`, but it completely deletes 
        them.   If *records* is omitted then the entire `Group` is searched. 
        
        .. seealso:: Table.delete
        

.. module:: norman.tools

Tools
-----

.. testsetup:: tools

    from norman.tools import *
    
    
Some useful tools for use with Norman are provided in `norman.tools`.

.. function:: float2(s[, default=0.0])
    
    Convert *s* to a float, returning *default* if it cannot be converted.
    
    .. doctest:: tools
    
        >>> float2('33.4', 42.5)
        33.4
        >>> float2('cannot convert this', 42.5)
        42.5
        >>> float2(None, 0)
        0
        >>> print(float2('default does not have to be a float', None))
        None


.. function:: int2(s[, default=0])
    
    Convert *s* to an int, returning *default* if it cannot be converted.
    
    .. doctest:: tools
        
        >>> int2('33', 42)
        33
        >>> int2('cannot convert this', 42)
        42
        >>> print(int2('default does not have to be an int', None))
        None
       
    
.. testcleanup::
    
    import os
    try:
        os.unlink('file.sqlite')
    except OSError:
        pass
        