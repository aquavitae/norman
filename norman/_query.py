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

    def op(t):
        return set(r for r in t if func(r))

    op.__name__ = func.__name__
    q = Query(op, table, table=table)
    # If its just a table, add function should be available
    if arg2 is None:
        q._add_kwargs = {}
    return q


def _or(a, b):
    return set(a) | set(b)


def _and(a, b):
    return set(a) & set(b)


def _sub(a, b):
    return set(a) - set(b)


def _xor(a, b):
    return set(a) ^ set(b)


class _Adder(object):

    """
    Utility for adding records to a query
    """

    def __init__(self, table=None):
        self.table = None
        self.__reason = None
        self.kwargs = {}
        if table is not None:
            self.set_table(table)

    def _inherit_adder(self, other):
        self.reason = other.reason
        self.set_table(other.table)
        self.add_kwargs(**other.kwargs)
        return self

    @property
    def reason(self):
        return self.__reason

    @reason.setter
    def reason(self, value):
        if not self.__reason:
            self.__reason = value

    def inherit(self, query):
        """
        Copy construction arguments from a base query.  If conflicting
        arguments result in addition being impossible, this is noted in
        `reason`.
        """
        return self._inherit_adder(query._adder)

    def set_table(self, table):
        if table == self.table:
            pass
        elif table is None:
            raise RuntimeError("Cannot assign None to a table")
        elif self.table is None and table is not False:
            self.table = table
        else:
            self.table = False
            self.reason = 'Inconsistent or invalid tables'
        return self

    def add_kwargs(self, **kwargs):
        dups = tuple(set(self.kwargs.keys()) & set(kwargs.keys()))
        if dups:
            self.reason = "Duplicate values for '%s'" % dups
        else:
            self.kwargs.update(kwargs)
        return self

    def __call__(self, **kwargs):
        """
        Add a record
        """
        if self.table in (None, False):
            raise TypeError("Cannot add. No single table defined.")
        orig = self.kwargs.copy()
        try:
            self.add_kwargs(**kwargs)
            if self.reason:
                raise TypeError(self.reason)
            record = self.table(**self.kwargs)
        finally:
            self.kwargs = orig
        return record


class _FieldAdder(_Adder):

    def __init__(self, table, fieldname):
        super(_FieldAdder, self).__init__()
        self.table = False
        self._addtable = table
        self._fieldname = fieldname
        # Add a placeholder to kwargs
        self.add_kwargs(**{fieldname: None})

    def set_table(self, value):
        pass

    def __call__(self, arg, **kwargs):
        """
        Add a record
        """
        if self._addtable is None:
            raise TypeError("Cannot add. No single table defined.")
        orig = self.kwargs.copy()
        try:
            self.kwargs[self._fieldname] = arg
            self.add_kwargs(**kwargs)
            if self.reason:
                raise TypeError(self.reason)
            record = self._addtable(**self.kwargs)
        finally:
            self.kwargs = orig
        return record


class Query(object):

    """
    This object should never be instantiated directly, instead it should
    be created as the result of a `Field` comparison or by using the `query`
    function.  The interface allows most operations permitted on sets, such
    as unions and intersections, but returns a new `Query` object instead
    of any results.  The following operations are  supported:

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

    Queries evaluate to `True` if they contain any results, and `False`
    if they do not.

    Calling a query forces it to be re-evaluated, and the query object is
    returned.
    """

    def __init__(self, op, *args, **kwargs):
        # _op is a callable which returns an iterable, which will be assigned
        # to _results.  _op will be called with each argument in *args,
        # any Query objects in *args will be replaced with their _results.
        self._op = op
        self._args = args
        self._results = None
        if 'adder' in kwargs:
            self._adder = kwargs['adder']
        else:
            self._adder = _Adder(kwargs.get('table', None))

    @property
    def table(self):
        """
        Return the table queried.  If no single table is queried, `None` is
        returned.
        """
        if self._adder.table not in (None, False):
            return self._adder.table

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
        self._results = set(self._op(*args))
        return self

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
        if not isinstance(other, Query):
            raise TypeError("Target of '&' operation must be another query.")
        q = Query(_and, self, other)
        q._adder.inherit(self).inherit(other)
        return q

    def __or__(self, other):
        if not isinstance(other, Query):
            raise TypeError("Target of '&' operation must be another query.")
        q = Query(_or, self, other)
        q._adder.inherit(self).inherit(other)
        return q

    def __sub__(self, other):
        if not isinstance(other, Query):
            raise TypeError("Target of '&' operation must be another query.")
        q = Query(_sub, self, other)
        q._adder.inherit(self).inherit(other)
        return q

    def __xor__(self, other):
        if not isinstance(other, Query):
            raise TypeError("Target of '&' operation must be another query.")
        q = Query(_xor, self, other)
        q._adder.inherit(self).inherit(other)
        return q

    def __str__(self):
        """
        Produce an text representation of the query.  This is useful for
        debugging.
        """
        names = {'_or': ' | ',
                 '_and': ' & ',
                 '_xor': ' ^ ',
                 '_sub': ' - ',
                 'eq': ' == ',
                 'ne': ' != ',
                 'gt': ' > ',
                 'ge': ' >= ',
                 'lt': ' < ',
                 'le': ' <= ',
                 'and': ' & '}

        strargs = []
        for a in self._args:
            if isinstance(a, Query):
                strargs.append('(%s)' % str(a))
            else:
                strargs.append(str(a))
        opname = self._op.__name__
        if opname in names:
            return names[opname].join(strargs)
        else:
            return '%s(%s)' % (opname, ', '.join(strargs))

    def add(self, *args, **kwargs):
        """
        Add a record based on the query criteria, and return the new record.
        There are two modes of operation for this method, depending on the
        query.  For either mode, the query must be defined by a clear set
        of field values for a single `Table`.  This includes queries such as
        ``(MyTable.field1` == 1) & (MyTable.field2` == 2)`` but not
        ``MyTable.field1` > 1``.

        The first mode accepts keyword arguments, which are combined with
        the parameters used to construct the query and passed to the
        table constructor. For example::

            ``((MyTable.a` == 1) & (MyTable.b` == 2)).add(c=3)``

        evaluates to::

            MyTable(a=1, b=2, c=3)

        The second mode is used when the query has been created by `field`.
        In this case, a single argument is expected which is the record
        to apply to the field.  For example::

            (Table1.id == 4).field('table2').add(table2_instance)

        is the same as::

            (Table1.id == 4).add(table2=table2_instance)
        """
        record = self._adder(*args, **kwargs)
        self._results = None
        return record

    def delete(self):
        """
        Delete all records matching the query from their table.  If no
        records match, nothing is deleted.
        """
        for r in self:
            # Check if its been deleted by validate_delete
            r.__class__.delete(r)

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
                    raise AttributeError("'{}' is not a Field".format(f))
                for item in value:
                    if isinstance(item, Table):
                        result.add(item)
            return result
        q = Query(op, self, fieldname, table=False,
                  adder=_FieldAdder(self.table, fieldname))
        q._adder.inherit(self)
        return q

    def one(self, default=_Sentinal):
        """
        Return a single value from the query results.  If the query is
        empty and *default* is specified, then it is returned instead,
        otherwise an `IndexError` is raised.
        """
        try:
            return next(iter(self))
        except StopIteration:
            pass
        except:
            raise
        if default is _Sentinal:
            raise IndexError('Query has no results')
        else:
            return default
