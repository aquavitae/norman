#!/usr/bin/env python3
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

import functools
import operator
import weakref
from collections import defaultdict

from ._query import Query


class NotSet(object):
    def __repr__(self):
        return 'NotSet'

    def __nonzero__(self):
        return False
    __bool__ = __nonzero__


# Sentinel indicating that the field value has not yet been set.
NotSet = NotSet()
NotSet.__doc__ = \
"""
A sentinel object indicating that the field value has not yet been set.

This evaluates to `False` in conditional statements.
"""


def _op(op):
    """
    Return a function for ``Table.field <op> value``
    """
    def _ops(field, value):
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
    return _ops


def _eq(field, value):
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


class Field(object):

    """
    A `Field` is used in tables to define attributes of data.

    When a table is created, fields can be identified by using a `Field`
    object:

    >>> class MyTable(Table):
    ...     name = Field()

    `Field` objects support *get* and *set* operations, similar to
    *properties*, but also provide additional options.  They are intended
    for use with `Table` subclasses.

    Field options are set as keyword arguments when it is initialised

    ========== ============ ===================================================
    Keyword    Default      Description
    ========== ============ ===================================================
    unique     False        True if records should be unique on this field.
                            In database terms, this is the same as setting
                            a primary key.  If more than one field have this
                            set then records are expected to be unique on all
                            of them.  Unique fields are always indexed.
    index      False        True if the field should be indexed.  Indexed
                            fields are much faster to look up.  Setting
                            ``unique = True`` implies ``index = True``
    default    None         If missing, `NotSet` is used.
    readonly   False        Prohibits setting the variable, unless its value
                            is `NotSet`.  This can be used with *default*
                            to simulate a constant.
    validate   None         If set, should be a list of functions which are
                            to be used as validators for the field.  Each
                            function should accept a and return a single value,
                            and should raise an exception if the value is
                            invalid.  The return value is the value passed
                            to the next validator.
    ========== ============ ===================================================

    Note that *unique* and *index* are table-level controls, and are not used
    by `Field` directly.  It is the responsibility of the table to
    implement the necessary constraints and indexes.

    Fields have read-only properties, *name* and *owner* which are
    set to the assigned name and the owning table respectively when
    the table class is created.

    Fields can be used with comparison operators to return a `_Results`
    object containing matching records.  For example::

        >>> class MyTable(Table):
        ...     oid = Field(unique=True)
        ...     value = Field()
        >>> t0 = MyTable(oid=0, value=1)
        >>> t1 = MyTable(oid=1, value=2)
        >>> t2 = MyTable(oid=2, value=1)
        >>> Table.value == 1
        _Results(MyTable(oid=0, value=1), MyTable(oid=2, value=1))

    .. seealso::

        `validators` for some pre-build validators.
    """

    def __init__(self, **kwargs):
        self.unique = kwargs.get('unique', False)
        self.index = kwargs.get('index', False) or self.unique
        self.default = kwargs.get('default', NotSet)
        self.readonly = kwargs.get('readonly', False)
        self.validators = kwargs.get('validate', [])
        self._data = {}
        if self.index:
            self._index = defaultdict(weakref.WeakSet)

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

    def __copy__(self):
        return Field(unique=self.unique,
                     index=self.index,
                     default=self.default,
                     readonly=self.readonly)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self._data.get(instance, self.default)

    def __set__(self, instance, value):
        """
        Set a value for an instance.
        """
        if (self.readonly and
            self.__get__(instance, instance.__class__) is not NotSet):
            raise TypeError('Field is read only')
        self._data[instance] = value

    def __eq__(self, value):
        q = Query(_eq, self, value)
        q._addargs = (self.owner, {self.name:value})
        return q

    def __ne__(self, value):
        return Query(_op(operator.ne), self, value)

    def __gt__(self, value):
        return Query(_op(operator.gt), self, value)

    def __lt__(self, value):
        return Query(_op(operator.lt), self, value)

    def __ge__(self, value):
        return Query(_op(operator.ge), self, value)

    def __le__(self, value):
        return Query(_op(operator.le), self, value)

    def __and__(self, values):
        return Query(_op(lambda a, b: a in b), self, values)


class Join(object):

    """

    A join, returning a `Query`.

    Joins can be created with the following arguments:

    ``Join(query=queryfactory)``
        Explicitly set the query factory.  `!queryfactory` is a callable which
        accepts a single argument and returns a `Query`.

    ``Join(table.field)``
        This is the most common format, since most joins simply involve looking
        up a field value in another table.  This is equivalent to specifying
        the following query factory::

            def queryfactory(value):
                return table.field == value

    ``Join(db, 'table.field`)``
        This has the same affect as the previous example, but is used when the
        foreign field has not yet been created.  In this case, the query
        factory first locates ``'table.field'`` in the `Database` ``db``.

    ``Join(other.join)``
        It is possible set the target of a join to another join, creating a
        *many-to-many* relationship.  When used in this way, a join table is
        automatically created, and can be accessed from `Join.jointable`.
        If the optional keyword parameter *jointable* is used, the join table
        name is set to it.

        .. seealso::

            http://en.wikipedia.org/wiki/Many-to-many_(data_model)
                For more information on *many-to-many* joins.
    """

    def __init__(self, *args, query=None):
        self._args = args
        self._query = query
        self._jointable = None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self.query(instance)

    @property
    def jointable(self):
        """
        The join table in a *many-to-many* join.

        This is `None` if the join is not a *many-to-many* join, and is
        read only.
        """
        return self._jointable

    @property
    def name(self):
        """
        The name of the `Join`. This is read only.
        """
        return self._name

    @property
    def owner(self):
        """
        The `Table` containing the `Join`.  This is read only.
        """
        return self._owner

    @property
    def query(self):
        """
        A function which accepts an instance of `owner` and returns a `Query`.
        """
        if self._query is not None:
            return self._query
        else:
            if len(self._args) == 1:
                field = self._args[0]
            else:
                table, field = self._args[1].split('.')
                table = self._args[0][table]
                field = getattr(table, field)
            return lambda v: field == v

    @query.setter
    def query(self, value):
        self._query = value
