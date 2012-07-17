.. module:: norman

.. testsetup::

    from norman import *


Norman Documentation
====================

**Norman** provides a framework for creating complex data structures using
an database-like approach.  It doesn't, however, link into any database
API (e.g. sqlite) and doesn't support SQL syntax.  It is intended to be
used as a lightweight, in-memory framework, without the restrictions imposed
by formal databases.

One of the main distinctions between this framework and a SQL database is
in the way relationships are managed.  In a SQL database, each record
has one or more primary keys, which are typically referred to in other,
related tables by foreign keys.  Here, however, keys do not exist, and
records are linked directly to each other as attributes.

The main data class is `Table`, and related tables can be grouped into a
`Database`.  A `Table` may belong to more than one `Database`, or not
belong to a `Database` at all.


Contents
--------

.. toctree::
    :maxdepth: 2

    tutorial
    changes
    data
    queries
    serialise
    tools
    validate
