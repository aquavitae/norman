.. module:: norman.serialise

.. testsetup::

    from norman import *


Serialisation
=============

In addition to supporting the `pickle` protocol, Norman provides a
framework for serialising and de-serializing databases to other formats
through the `norman.serialise` module.  Serialisation classes inherit
`Reader`, `Writer` or `Serialiser`, which is a subclass of the first two
provided for convenience.

.. contents::


Serialisation Framework
-----------------------

In addition to the `Reader`, `Writer` and `Serialiser` classes, a convenience
function is provided to generate uids.

.. autofunction:: uid


Readers
^^^^^^^

.. autoclass:: Reader

    .. automethod:: read(source, db)

    .. automethod:: iter_source(source, db)

    .. automethod:: isuid(field, value)

    .. automethod:: create_group(records)

    .. automethod:: create_record(table, uid, data)


Writers
^^^^^^^

.. autoclass:: Writer

    .. automethod:: write(targetname, db)

    .. automethod:: context(targetname, db)

    .. automethod:: iterdb(db)

    .. automethod:: simplify(record)

    .. automethod:: write_record(record, target)



Serialiser
^^^^^^^^^^

.. autoclass:: Serialiser


CSV
---

.. autoclass:: CSV


Sqlite
------

.. autoclass:: Sqlite
