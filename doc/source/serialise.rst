.. module:: norman.serialise

.. testsetup::

    from norman import *


Serialisation
=============

In addition to supporting the `pickle` protocol, `norman` provides a
framework for serialising and de-serializing databases to other formats
through the `norman.serialise` module.  Serialisation classes inherit
`Serialiser`, and should reimplement at least `~Serialiser.iterfile`
and `~Serialiser.write_record`.  `Serialiser` has the following methods,
grouped by functionality:

*   General

    *   `~Serialiser.open`
    *   `~Serialiser.close`

*   Loading (Reading)

    *   `~Serialiser.load` (Class method)
    *   `~Serialiser.create_records`
    *   `~Serialiser.finalise_read`
    *   `~Serialiser.initialise_read`
    *   `~Serialiser.isuid`
    *   `~Serialiser.iterfile`
    *   `~Serialiser.read`
    *   `~Serialiser.run_read`

*   Dumping (Writing)

    *   `~Serialiser.dump` (Class method)
    *   `~Serialiser.finalise_write`
    *   `~Serialiser.initialise_write`
    *   `~Serialiser.iterdb`
    *   `~Serialiser.run_write`
    *   `~Serialiser.simplify`
    *   `~Serialiser.write`
    *   `~Serialiser.write_record`


.. contents::


Serialiser framework
--------------------

.. class:: Serialiser(db)

    An abstract base class providing a framework for serialisers.

    Subclasses are instantiated with a `~norman.Database` object, and
    serialisation and de-serialisation is done through the `write` and `read`
    methods.  Class methods `dump` and `load` may also be used.

    Subclasses are required to implement `iterfile` and its counterpart,
    `write_record`, but may re-implement any other methods to customise
    behaviour.


    .. attribute:: db

        The database handled by the serialiser.


    .. attribute:: fh

        An open file (or database connection), or `None`.

        This is set to the result of `open`.  If a file is not currently
        open, then this is `None`.


    .. attribute:: mode

        Indicates the current operation.

        This is set to ``'w'`` during *dump* operations and ``'r'`` during
        *load*.  At other times it is `None`.


    .. classmethod:: dump(db, filename)

        This is a convenience method for calling `write`.

        This is equivalent to ``Serialise(db).write(filename)`` and is
        provided for compatibility with the `pickle` API.


    .. classmethod:: load(db, filename)

        This is a convenience method for calling `read`.

        This is equivalent to ``Serialise(db).read(filename)`` and is
        provided for compatibility with the `pickle` API.


    .. method:: close

        Close the currently opened file.

        The default behaviour is to call the file object's `!close` method.
        This method is always called once a file has been opened, even if an
        exception occurs during writing.


    .. method:: create_records(records)

        Create one or more new records.

        This is called for every group of cyclic records.  For example,
        if records *a* references record *b*, which references record *c*, and
        record *c* references record *a*, then records *a*, *b*, and *c*
        form a cycle.  If record *d* references record *e* but record *e*
        doesn't reference any other record, each of them are considered to
        be isolated.

        *records* is an iterator yielding tuples of
        ``(table, uid, data, cycles)`` for each record in the cycle, or only
        one record if there is no cycle.  The first three values are the same
        as those returned by `iterfile`, except that foreign uids in data
        have been dereferenced.  *cycles* is a set of field names which
        contain the cyclic data.

        The default behaviour is to remove the cyclic fields from *data*
        for each record, create the records using ``table(**data)``
        and assign the created records to the cyclic fields.  The *uid*
        of each record is also assigned to its *_uid* attribute.

        The return value is an iterator over ``(uid, record)`` pairs.


    .. method:: finalise_read

        Finalise the file after reading data.

        This is called after `run_read` but before `close`, and can be
        re-implemented to for implementation-specific finalisation.

        The default implementation does nothing.


    .. method:: finalise_write

        Finalise the file after writing data.

        This is called after `run_write` but before `close`, and can be
        re-implemented to for implementation-specific finalisation.

        The default implementation does nothing.


    .. method:: initialise_read

        Prepare the file for reading data.

        This is called before `run_read` but after `open`, and can be
        re-implemented to for implementation-specific setup.

        The default implementation does nothing.


    .. method:: initialise_write

        Prepare the file for writing data.

        This is called before `run_write` but after `open`, and can be
        re-implemented to for implementation-specific setup.

        The default implementation does nothing.


    .. method:: isuid(field, value)

        Return `True` if *value*, for the specified *field*, could be a *uid*.

        *field* is a `~norman.Field` object.

        This only needs to check whether the value could possibly represent
        another field.  It is only actually considered a *uid* if there is
        another record which matches it.

        By default, this returns `True` for all strings which match a UUID
        regular expression, e.g. ``'a8098c1a-f86e-11da-bd1a-00112444be1e'``.


    .. method:: iterdb

        Return an iterator over records in the database.

        Records should be returned in the order they are to be written.  The
        default implementation is a generator which iterates over records in
        each table.


    .. method:: iterfile

        Return an iterator over records read from the file.

        Each item returned by the iterator should be a tuple of
        ``(table, uid, data)`` where  *table* is the `~norman.Table`
        containing the record, *uid* is a globally unique value identifying
        the record and *data* is a dict of field values for the record,
        possibly containing other uids.

        This is commonly implemented as a generator.


    .. method:: read(filename)

        Load data into `db` from *filename*.

        *fieldname* is used only to open the file using `open`, so, depending
        on the implementation could be anything (e.g. a URL) which `open`
        recognises.  It could even be omitted entirely if, for example,
        the serialiser reads from stdin.


    .. method:: open(filename)

        Open *filename* for the current `mode`.

        The return value should be a handle to the open file.  The default
        behaviour is to open the file as binary using the builtin *open*
        function.


    .. method:: run_read

        Read data from the currently opened file.

        This is called between `initialise_read` and `finalise_read`, and
        converts each value returned by `iterfile` into a record using
        `create_records`.  It also attempts to re-map nested records by
        searching for matching uids.

        Cycles in the data are detected, and all records involved in
        in a cycle are created in `create_records`.


    .. method:: run_write

        Called by `dump` to write data.

        This is called after `initialise_write` and before `finalise_write`,
        and simply calls `write_record` for each value yielded by `iterdb`.


    .. method:: simplify(record)

        Convert a record to a simple python structure.

        The default implementation converts *record* to a `dict` of
        field values, omitting `~norman.NotSet` values and replacing other
        records with their *_uid* properties.  The return value of this
        implementation is a tuple of ``(tablename, record._uid, record_dict)``.


    .. method:: write(filename)

        Write the database to *filename*.

        *fieldname* is used only to open the file using `open`, so, depending
        on the implementation could be anything (e.g. a URL) which `open`
        recognises.  It could even be omitted entirely if, for example,
        the serialiser dumps the database as formatted text to stdout.


    .. method:: write_record(record)

        Write *record* to the current file.

        This is called by `run_write` for every record yielded by `iterdb`.
        *record* is the values returned by `simplify`.


Sqlite
------

.. class:: Sqlite3

    .. deprecated:: 0.6.1

        Use the new `Serialiser` framework instead.


    .. method:: dump(db, filename)

        Dump the database to a sqlite database.

        Each table is dumped to a sqlite table, without any constraints.
        All values in the table are converted to strings and foreign objects
        are stored as an integer id (referring to another record). Each
        record has an additional field, '_oid_', which contains a unique
        integer.


    .. method:: load(db, filename)

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


.. testcleanup::

    import os
    try:
        os.unlink('file.sqlite')
    except OSError:
        pass
