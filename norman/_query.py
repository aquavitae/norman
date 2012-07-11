# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 David Townshend
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 675 Mass Ave, Cambridge, MA 02139, USA.

from __future__ import with_statement
from __future__ import unicode_literals


class _Sentinal:
    pass


def query(arg1, arg2=None):
    """
    Return a new `Query` for records in *table* for which *func* is `True`.

    *table* is a `Table` or `Query` object.  If *func* is missing, all
    records are assumed to pass.  If it is specified, is should accept a
    record as its argument and return `True` for passing records.
    """
    if arg2 is None:
        table = arg1
        func = lambda a: True
    else:
        table = arg2
        func = arg1
    return Query(func, table)


class Query(object):

    """
    A set-like object which represents the results of a query.

    This object should never be instantiated directly, instead it should
    be created as the result of a query on a `Table` or `Field`.

    This object allows most operations permitted on sets, such as unions
    and intersections.  Comparison operators (such as ``<``) are not
    supported, except for equality tests.

    Queries are considered `True` if they contain any results, and `False`
    if they do not.

    The following operations are supported:

    =================== =======================================================
    Operation           Description
    =================== =======================================================
    ``r in q``          Return `True` if record ``r`` is in the results of
                        query ``q``.
    ``len(q)``          Return the number of results in ``q``.
    ``iter(q)``         Return an iterator over records in ``q``.
    ``q1 == q2``        Return `True` if ``q1`` and ``q2`` contain the same
                        records.
    ``q1 != q2``        Return `True` if ``not a == b``
    ``q1 & q2``         Return a new `Query` object containing records in
                        both ``q1`` and ``q2``.
    ``q1 | q2``         Return a new `Query` object containing records in
                        either ``q1`` or ``q2``.
    ``q1 ^ q2``         Return a new `Query` object containing records in
                        either ``q1`` or ``q2``, but not both.
    ``q1 - q2``         Return a new `Query` object containing records in
                        ``q1`` which are not in ``q2``.
    =================== =======================================================
    """

    def __init__(self, op, *args):
        # _op is a callable which returns an iterable, which will be assigned
        # to _results.  _op will be called with each argument in *args,
        # any Query objects in *args will be replaced with their _results.
        self._op = op
        self._args = args
        self._results = None

    def __bool__(self):
        try:
            self.one()
        except IndexError:
            return False
        return True

    def __call__(self):
        args = []
        for a in self._args:
            if isinstance(a, Query):
                a()
                args.append(a._results)
            else:
                args.append(a)
        self._results = self._op(*args)

    def __contains__(self, record):
        return record in set(self)

    def __eq__(self, other):
        return isinstance(other, Query) and set(self) == set(other)

    def __iter__(self):
        if self._results is None:
            self()
        return iter(self._results)

    def __len__(self):
        return len(set(self))

    def __and__(self, other):
        q = Query(lambda a, b: set(a) & set(b), self, other)
        if (hasattr(self, '_addargs') and hasattr(other, '_addargs') and
            self._addargs[0] is other._addargs[0]):
            table, kw1 = self._addargs
            kw2 = other._addargs[1]
            if not set(kw1.keys()) & set(kw2.keys()):
                kw = dict(kw1)
                kw.update(kw2)
                q._addargs = (table, kw)
        return q

    def __or__(self, other):
        return Query(lambda a, b: set(a) | set(b), self, other)

    def __sub__(self, other):
        return Query(lambda a, b: set(a) - set(b), self, other)

    def __xor__(self, other):
        return Query(lambda a, b: set(a) ^ set(b), self, other)

    def add(self, **kwargs):
        """
        Add a record based on the query criteria.

        This method is only available for queries of the form
        ``field == value``, or an ``&`` combination of them.  **kwargs** is
        the same as used for creating a `Table` instance, but is
        updated to include the query criteria.
        """
        if not hasattr(self, '_addargs'):
            raise NotImplementedError
        table, kw = self._addargs
        kwargs.update(kw)
        self._results = None
        return table(**kwargs)

    def delete(self):
        """
        Delete all records matching the query.

        Records are deleted from the table.  If no records match,
        nothing is deleted.
        """
        for r in self:
            # Check if its been deleted by validate_delete
            if r.__class__._instances.get(r._key, None):
                try:
                    r.validate_delete()
                except AssertionError as err:
                    raise ValueError(*err.args)
                except:
                    raise
                else:
                    del r.__class__._instances[r._key]

    def field(self, fieldname):
        """
        Return a new `Query` containing records in a single field.

        The set of records returned by this is similar to::

            set(getattr(r, fieldname) for r in query)

        However, the returned object is another `Query` instead of a set.
        Only instances of a `Table` subclass are contained in the results,
        other values are dropped.  This is functionally similar to a SQL
        query on a foreign key.  If the target field is a `Join`, then all
        the results of each join are concatenated.
        """
        from ._table import Table
        from ._field import Field, Join

        def op(a, f):
            result = set()
            for record in a:
                field = getattr(record.__class__, f)
                value = getattr(record, f)
                if isinstance(field, Field):
                    value = [value]
                elif not isinstance(field, Join):
                    raise KeyError("'{}' is not a Field".format(f))
                for item in value:
                    if isinstance(item, Table):
                        result.add(item)
            return result
        return Query(op, self, fieldname)


    def one(self, default=_Sentinal):
        """
        Return a single value from the query results.

        If the query is empty and *default* is specified, then it is returned
        instead.  Otherwise an exception is raised.
        """
        try:
            return next(iter(self))
        except StopIteration:
            pass
        except:
            raise
        if default is _Sentinal:
            raise IndexError
        else:
            return default
