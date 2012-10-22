.. module:: norman.serialise

.. testsetup::

    from norman import *


Serialisation
=============

In addition to supporting the `pickle` protocol, Norman provides a
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

.. autoclass:: Serialiser(db)


    .. autoattribute:: db


    .. autoattribute:: fh


    .. autoattribute:: mode


    .. classmethod:: dump(db, filename)

        This is a convenience method for calling `write`.

        This is equivalent to ``Serialise(db).write(filename)`` and is
        provided for compatibility with the `pickle` API.


    .. classmethod:: load(db, filename)

        This is a convenience method for calling `read`.

        This is equivalent to ``Serialise(db).read(filename)`` and is
        provided for compatibility with the `pickle` API.


    .. classmethod:: uid

        Create a new uid value.  This is useful for files which do not
        natively provide a uid, and can be used to generate one in
        `iterfile`.


    .. automethod:: close

    .. automethod:: create_records(records)

    .. automethod:: finalise_read

    .. automethod:: finalise_write

    .. automethod:: initialise_read

    .. automethod:: initialise_write

    .. automethod:: isuid(field, value)

    .. automethod:: iterdb

    .. automethod:: iterfile

    .. automethod:: read(filename)

    .. automethod:: open(filename)

    .. automethod:: run_read

    .. automethod:: run_write

    .. automethod:: simplify(record)

    .. automethod:: write(filename)

    .. automethod:: write_record(record)


Sqlite
------

.. autoclass:: Sqlite


.. class:: Sqlite3

    .. deprecated:: 0.6.1

        Use `Sqlite`, which implements the `Serialiser` framework instead.


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
