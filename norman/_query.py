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

import operator
import functools
import itertools


class ops:

    """
    Operation functions for queries
    """

    def _f_ops(self, op, field, value):
        """
        Generic function for ``Table.field <op> value``
        """
        table = field.owner
        if field.index:
            keysets = (k for v, k in field._index.items() if op(v, value))
            try:
                keys = functools.reduce(lambda a, b: a & b, keysets)
            except TypeError:
                keys = set()
            return set(table._instances[k] for k in keys \
                       if k in table._instances)
        else:
            return set(r for r in table._instances.values()
                       if op(getattr(r, field.name), value))

    def f_eq(self, field, value):
        """
        Return a set of ``Table.field == value``
        """
        table = field.owner
        if field.index:
            keys = field._index[value]
            return set(table._instances[k] for k in keys \
                       if k in table._instances)
        else:
            return set(r for r in table._instances.values()
                       if getattr(r, field.name) == value)

    def f_ne(self, field, value):
        """
        Return a set of ``Table.field != value``
        """
        return self._f_ops(operator.ne, field, value)

    def f_gt(self, field, value):
        """
        Return a set of ``Table.field > value``
        """
        return self._f_ops(operator.gt, field, value)

    def f_lt(self, field, value):
        """
        Return a set of ``Table.field < value``
        """
        return self._f_ops(operator.lt, field, value)

    def f_ge(self, field, value):
        """
        Return a set of ``Table.field >= value``
        """
        return self._f_ops(operator.ge, field, value)

    def f_le(self, field, value):
        """
        Return a set of ``Table.field <= value``
        """
        return self._f_ops(operator.le, field, value)

    def f_and(self, field, values):
        """
        Return a set of ``Table.field & values``
        """
        in_ = lambda a, b: a in b
        return self._f_ops(in_, field, set(values))

    def q_ops(self, op, a, b):
        """
        Return a set for ``query_a._results <op> query_b._results``.
        """
        return op(set(a), set(b))

    def q_slice(self, slice, q):
        """
        Return a list of ``query[slice]``.
        """
        return list(itertools.islice(q, slice.start, slice.stop, slice.step))\

    def q_attr(self, name, q):
        return type(q)(getattr(r, name) for r in q)


ops = ops()


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
    Represent a query with a set-like interface.

    Queries are usually constructed from `Field` and other `Query` objects, but
    may also be initialised directly.  The first argument to the constructor
    is a function which acts on each of the following positional arguments
    and returns an iterable result.

    Comparison and combination operators may be used on queries and most of
    these return a new `Query` object.  For example, the statement
    ``(MyTable.value > 2) & (MyTable.name == 'a')`` is constructed as::

        Query(operator.and_,
              Query(operator.gt, MyTable.value, 2),
              Query(operator.eq, MyTable.name, 'a'))

    Queries are only evaluated the first time the results are requested or
    when `execute` is called.

    The following operations are supported:

    =================== =======================================================
    Operation           Description
    =================== =======================================================
    ``r in a``          Return `True` if record ``r`` is in the results ``a``.
    ``len(a)``          Return the length of results ``a``.
    ``iter(a)``         Return an iterator over the results.
    ``a & b``           Return a new `Query` object containing records in
                        both ``a`` and ``b``.
    ``a | b``           Return a new `Query` object containing records in
                        either ``a`` or ``b``.
    ``a ^ b``           Return a new `Query` object containing records in
                        either ``a`` or ``b``, but not both.
    ``a - b``           Return a new `Query` object containing records in
                        ``a`` which are not in ``b``.
    ``~a``              Return a new `Query` object containing records not
                        in query ``a``.  This can only be used on queries
                        containing records.
    ``a <cmp> value``   Where *cmp* is a comparison operator, this returns
                        a new `Query` object containing only results which
                        compare `True`.
    ``a.field``         Return a new `Query` object containing values from
                        ``field`` for each record in ``a``
    =================== =======================================================
    """

    def __init__(self, op, *args):
        self._op = op
        self._args = args
        self._results = None

    def __call__(self):
        args = []
        for a in self._args:
            if isinstance(a, Query):
                a()
                args.append(a._results)
            else:
                args.append(a)
        self._results = self._op(*args)

    def __and__(self, other):
        return Query(functools.partial(ops.q_ops, operator.and_), self, other)

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

    def __or__(self, other):
        return Query(functools.partial(ops.q_ops, operator.or_), self, other)

    def __sub__(self, other):
        return Query(functools.partial(ops.q_ops, operator.sub), self, other)

    def __xor__(self, other):
        return Query(functools.partial(ops.q_ops, operator.xor), self, other)
