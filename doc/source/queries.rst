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

The result of each of these is a `Query` object, which is a set-like
iterable of records.

An existing query can be refreshed after the base data has changed by
calling it as a function.  The return value is the query iteself, so
to ensure that the result is up to date, you could call::

    latest_size = len(q7())


API
---

.. autofunction:: query([func], table)


.. autoclass:: Query

    .. method:: add([arg, **kwargs])

        Add a record based on the query criteria.

        This method is only available for queries of the form
        ``field == value``, a ``&`` combination of them, or a `field`
        query created from a query of this form.  *kwargs* is
        the same as used for creating a `Table` instance, but is
        updated to include the query criteria. *arg* is only used for
        queries created by `field`, and is a record to add to the field.
        See `field` for more information.

    .. automethod:: delete


    .. automethod:: field(fieldname)


    .. automethod:: one([default])


Groups
------

.. deprecated:: 0.6
    Use a `Join` or `Query` instead.


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
        <set_iterator object at ...>
        >>> parent.children.add(name='c')
        Child('c')


    .. attribute:: table

        Read-only property containing the `Table` object referred to.


    .. method:: add(**kwargs)

        Create a new record of the reference `table`.

        *kwargs* is updated with the keyword arguments defining this `Group`
        and the resulting dict used as the initialisation parameters of
        `table`.


    .. method:: contains(**kwargs)

        Return `True` if the `Group` contains records matching *kwargs*.


    .. method:: delete([records=None,] **keywords)

        Delete delete all instances in *records* which match *keywords*.

        This only deletes instances in the `Group`, but it completely deletes
        them.   If *records* is omitted then the entire `Group` is searched.

        .. seealso:: Table.delete


    .. method:: get(**kwargs)

        Return a set of all records in the `Group` matching *kwargs*.


    .. method:: iter(**kwargs)

        Iterate over records in the `Group` matching *kwargs*.
