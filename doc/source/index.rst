.. module:: dtlibs.database

.. testsetup::

    from dtlibs.database import *
    

Database
========

This framework provides a bases for creating database-like structures.
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

The main class is `Table` which defines the structure of a specific
type of record.

.. autoclass:: Database
    :members:
    
.. autoclass:: Table
    :members:
    
.. autodata:: NotSet

.. autoclass:: Field
    :members:
    
.. testcleanup::
    
    import os
    try:
        os.unlink('file.sqlite')
    except OSError:
        pass
        