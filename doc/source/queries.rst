.. module:: norman

.. testsetup::

    from norman import *


Queries
=======

Norman features a flexible and extensible query API, the basis of which is
the `Query` class.  Queries are constructed by manipulating `Field` and other
`Query` objects; the result of each operation is another `Query`.

.. contents::


Examples
--------

The following examples explain the basic concepts behind Norman queries.

Queries are constructed as a series of field comparisons, for example::

    q1 = MyTable.age > 4
    q2 = MyTable.parent.name == 'Bill'

These can be joined together with set combination operators::

    q3 = (MyTable.age > 4) | (MyTable.parent.name == 'Bill')

Containment in an iterable can be checked using the ``&`` operator.  This
is the same usage as in `set`::

    q4 = MyTable.parent.name & ['Bill', 'Bob', 'Bruce']

Since queries are themselves iterable, another query can be used as the
container::

    q5 = MyTable.age & OtherTable.age

A custom function can be used for filtering records from a `Table` or
another `Query`::

    def isvalid(record):
        return record.parrot.endswith('notlob')

    q6 = query(isvalid, q5)

If the filter function is omitted, then all records are assumed to pass.
This is useful for creating a query of a whole table::

    q7 = query(MyTable)

The result of each of these is a `Query` object, which can be iterated over
to yield records.  The query is not evaluated until a result is requested
from it (including ``len``).  An existing query can be refreshed after the
base data has changed by calling it as a function.  The return value is the
query iteself, so to ensure that the result is up to date, you could call::

    latest_size = len(q7())


API
---

.. autofunction:: query([func], table)


.. autoclass:: Query


    .. autoattribute:: table
    
    
    .. automethod:: add([arg, **kwargs])


    .. automethod:: delete


    .. automethod:: field(fieldname)


    .. automethod:: one([default])

