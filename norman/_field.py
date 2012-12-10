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
import numbers
import operator

from ._except import ConsistencyError, ValidationError
from ._query import Query


class NotSet(object):
    def __repr__(self):
        return 'NotSet'

    def __nonzero__(self):
        return False
    __bool__ = __nonzero__


# Sentinel indicating that the field value has not yet been set.
NotSet = NotSet()


def _op(op):
    inner = lambda field, value: set(op(field.owner._store.indexes[field], value))
    inner.__name__ = op.__name__
    return inner

def _key(value):
    if isinstance(value, numbers.Real):
        return '0Real', value
    elif isinstance(value, str):
        return '1str', value
    elif isinstance(value, bytes):
        return '2bytes', value
    else:
        raise TypeError


class Field(object):

    """
    A `Field` is used in tables to define attributes.

    >>> class MyTable(Table):
    ...     name = Field()

    Fields may be created with a combination of properties as keyword arguments,
    including `default`, `key`, `readonly`, `unique` and `validators`.

    Fields can be used with comparison operators to return a `Query`
    object containing matching records.  For example::

        >>> class MyTable(Table):
        ...     oid = Field(unique=True)
        ...     value = Field()
        >>> t0 = MyTable(oid=0, value=1)
        >>> t1 = MyTable(oid=1, value=2)
        >>> t2 = MyTable(oid=2, value=1)
        >>> Table.value == 1
        Query(MyTable(oid=0, value=1), MyTable(oid=2, value=1))

    The following comparisons are supported for a `Field` object, provided
    the data stored supports them: ``==``, ``<``, ``>``, ``<=``, ``>==``,
    ``!=``.  The ``&`` operator is used to test for containment, e.g.
    `` Table.field & mylist`` returns all records where the value of
    ``field`` is in ``mylist``.


    .. changed:: 0.7

        All fields are automatically indexed, and the *index* argument
        has been removed.   *key* has been added to control how data is
        indexed.


    .. seealso::

        `validate`
            For some pre-build validators.

        :doc:`queries`
            For more information of queries in Norman.
    """

    def __init__(self, unique=False, default=NotSet,
                 readonly=False, validators=None, key=_key):
        self._unique = unique
        self._default = default
        self._readonly = readonly
        self._validators = [] if validators is None else validators
        self._key = key

    @property
    def default(self):
        """
        The value to use when nothing has been set (default: `NotSet`).
        """
        return self._default

    @default.setter
    def default(self, value):
        self.owner._store.setdefault(self, value)
        self._default = value

    @property
    def key(self):
        """
        A key function used for indexing, similar to that used by `sorted`.
        All values returned by this function should be sortable in the same
        list. For example, if the field is known to contain a mixture
        of strings and integers, `str` would be a valid function, but
        ``lambda x: x`` would not, since a list of strings and integers
        cannot be sorted.  `key` should raise `TypeError` for any value
        it cannot handle.  These will be indexed separately, so that equality
        lookups are still optimised, but comparisons will not be supported.
        As an illustrative example, consider the following case which
        orders values by length::

            >>> class T(Table):
            ...     value = Field(key=len)
            ...
            >>> t1 = T(value='abc')
            >>> t2 = T(value='defg')
            >>> t3 = T(value=42)
            >>> (T.value > 'xxx').one()  # Find values longer than 3 characters
            T(value='abc')
            >>> (T.value == 42).one()  # Find the numerical value 42
            T(value=42)
            >>> (T.value() > 42).one()  # len(42) raises TypeError
            Traceback (most recent call last)
                ...
            TypeError

        The default implementation orders data by type first, then value, for
        the following types: `numbers.Real`, `str`, `bytes`.  This might lead
        to unexpected results, since ``42 < 'text'`` will evaluate True.

        `NotSet` values are handled slightly differently, and are never passed
        through this function.  Comparison queries on `NotSet` will always
        fail.
        """
        return self._key

    @property
    def name(self):
        """
        This is the assigned name of the field and is set when the `Table` is
        created.  This attribute is readonly.
        """
        return self._name

    @property
    def owner(self):
        """
        This is the owning `Table` of the field and is set when the `Table` is
        created.  This attribute is readonly.
        """
        return self._owner

    @property
    def readonly(self):
        """
        If `True`, prohibits setting the variable, unless its value is
        `NotSet` (default: `False`).  This can be used with `default`
        to simulate a constant.

        This attribute is readonly and can only be set when the `Field` is
        created.
        """
        return self._readonly

    @property
    def unique(self):
        """
        `True` if records should be unique on this field (default: `False`).
        In database terms, this is the same as setting a primary key.  If
        more than one field have this set then records are expected to be
        unique on all of them.

        This attribute is readonly and can only be set when the `Field` is
        created.
        """
        return self._unique

    @property
    def validators(self):
        """
        A list of functions which are used as validators for the field.  Each
        function should accept and return a single value (i.e. the value to be
        set), and should raise an exception if the value is invalid.  The
        validators are called sequentially, e.g.
        ``validator3(validator2(validator1(value)))``.
        """
        return self._validators

    def __copy__(self):
        return Field(unique=self.unique,
                     default=self.default,
                     key=self.key,
                     readonly=self.readonly,
                     validators=self.validators)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self.owner._store.get(instance, self)

    def __hash__(self):
        return id(self)

    def __eq__(self, value):
        q = Query(_op(operator.eq), self, value)
        q._setaddargs(self.owner, {self.name: value})
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
        def _and(field, value):
            index = field.owner._store.indexes[field]
            return  functools.reduce(operator.or_,
                                     (set(index == v) for v in values))
        return Query(_and, self, values)

    def __str__(self):
        return '.'.join([self._owner.__name__, self.name])


class Join(object):

    """
    Joins can be created in several ways:

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

    def __init__(self, *args, **kwargs):
        self._args = args
        self._query = kwargs.get('query', None)
        self._jt_name = kwargs.get('jointable', None)
        self._jointable = None

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self.query(instance)

    @property
    def target(self):
        """
        The target of the join, or `None` if the target cannot be found.
        This attribute is read only.
        """
        if len(self._args) == 0:
            return None
        elif len(self._args) == 1:
            return self._args[0]
        else:
            db = self._args[0]
            table, field = self._args[1].split('.')
            if table in db:
                table = db[table]
                if hasattr(table, field):
                    field = getattr(table, field)
                    return field
        return None

    @property
    def jointable(self):
        """
        The join table in a *many-to-many* join.

        This is `None` if the join is not a *many-to-many* join, and is
        read only.  If a jointable does not yet exist then it is created,
        but not added to any database.  If the two joins which define it have
        conflicting information, a `ConsistencyError` is raise.
        """
        if self._jointable is None:
            # Try creating it
            target = self.target
            if not isinstance(target, Join):
                return None

            jts = set([self._jt_name, target._jt_name, None])
            jts.remove(None)
            if len(jts) == 0:
                name = '_' + ''.join(sorted(j.owner.__name__
                                            for j in (self, target)))
            elif len(jts) == 1:
                name = jts.pop()
            elif len(jts) == 2:
                raise ConsistencyError('Inconsistent join table definition')

            def delete(f, record):
                (f == record).delete()

            from .validate import istype
            from ._table import TableMeta, Table

            t1, t2 = self.owner, target.owner
            f1 = Field(validators=[istype(t1)])
            f2 = Field(validators=[istype(t2)])
            JT = TableMeta(name, (Table,), {t1.__name__: f1, t2.__name__: f2})
            t1.hooks['delete'].append(functools.partial(delete, f1))
            t2.hooks['delete'].append(functools.partial(delete, f2))

            self._jointable = JT
            target._jointable = JT
            self.query = lambda r: (f1 == r).field(f2.name)
            target.query = lambda r: (f2 == r).field(f1.name)

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
            target = self.target
            if target is None:
                raise ConsistencyError('Missing target')
            if isinstance(self.target, Join):
                # Try to create the jointable and override `query`
                if self.jointable is None:
                    raise ConsistencyError('Missing join table')
                return self._query
            return lambda v: self.target == v

    @query.setter
    def query(self, value):
        self._query = value
