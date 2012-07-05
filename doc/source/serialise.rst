.. module:: norman.serialise

.. testsetup::

    from norman import *


Serialisation
=============

In addition to supporting the `pickle` protocol, `norman` provides a basic
interface for serialising and de-serializing databases to other formats
through the `norman.serialise` module.  Currently, only sqlite is supported,
but other formats will be added in the future.


.. class:: Sqlite3

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
