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
created before creating any tables.  Tables are subclassed from the `Table`
class and fields added to it by creating `Field` class attributes.


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

    Tables are added to the database when they are created by giving
    the class a *database* keyword argument.  For example

    >>> db = Database()
    >>> class MyTable(Table, database=db):
    ...     name = Field()
    >>> MyTable in db.tables()
    True

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
    
        Raise an exception of the record contains invalid data.
        
        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, and exception should be raised.
        Values may also be changed in the method.  The default implementation
        does nothing.


    .. method:: validate_delete
    
        Raise an exception if the record cannot be deleted.
        
        This is called just before a record is deleted and is usually 
        re-implemented to check for other referring instances.  For example,
        the following structure only allows deletions of *Name* instances
        not in a *Group*.
        
        >>> class Name(Table):                
        ...  name = Field()
        ...  group = Field(default=None)
        ...  
        ...  def validate_delete(self):
        ...      assert self.group is None, "Can't delete '{}'".format(self.name)
        ...      
        >>> class Group(Table)
        ...  id = Field()
        ...  @property
        ...  def names(self):
        ...      return Name.get(group=self)
        ...      
        >>> group = Group(id=1)
        >>> n1 = Name(name='grouped', group=group)
        >>> n2 = Name(name='not grouped')
        >>> Name.delete(name='not grouped')
        >>> Name.delete(name='grouped')
        Traceback (most recent call last):
            ...
        AssertionError: Can't delete "grouped"
        >>> {name.name for name in Name.get()}
        {'grouped'}
        
                
Fields
------


.. data:: NotSet

    A sentinel object indicating that the field value has not yet been set.
    This evaluates to False in conditional statements.
    
    
.. class:: Field
    
    A `Field` is used in tables to define attributes of data.
    
    When a table is created, fields can be identified by using a `Field` 
    object:
    
    >>> class Table:
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


.. module:: norman.tools

Tools
-----

Some useful tools for use with Norman are provided in `norman.tools`.

.. function:: float2(s[, default=0.0])
    
    Convert *s* to a float, returning *default* if it cannot be converted.
    
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
        