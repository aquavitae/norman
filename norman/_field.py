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

import operator
from ._result import _Result

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
    """

    def __init__(self, **kwargs):
        self.unique = kwargs.get('unique', False)
        self.index = kwargs.get('index', False) or self.unique
        self.default = kwargs.get('default', NotSet)
        self.readonly = kwargs.get('readonly', False)
        self._data = {}

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner

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
        return self.owner.get(**{self.name: value})

    def __ne__(self, value):
        return _Result(self.owner, set(self.owner) - set(self.__eq__(value)))

    def _op(self, op, value):
        return _Result(self.owner, set(r for r in self.owner \
                       if op(self._data.get(r, self.default), value)))

    def __gt__(self, value):
        return self._op(operator.gt, value)

    def __lt__(self, value):
        return self._op(operator.lt, value)

    def __ge__(self, value):
        return self._op(operator.ge, value)

    def __le__(self, value):
        return self._op(operator.le, value)


class Join(object):

    """
    A special field representing a one-to-many join to another table.

    This is best explained through an example::

        >>> class Child(Table):
        ...     parent = Field()
        ...
        >>> class Parent(Table):
        ...     children = Join(Child.parent)
        ...
        >>> p = Parent()
        >>> c1 = Child(parent=p)
        >>> c2 = Child(parent=p)
        >>> p.children
        {c1, c2}

    The initialisation parameters specify the field in the foreign table which
    contains a reference to the owning table, and may be specified in one of
    two ways.  If the foreign table is already defined (as in the above
    example), then only one argument is required.  If it has not been
    defined, or is self-referential, the first agument may be the database
    instance and the second the canonical field name, including the table
    name.  So an alternate definition of the above *Parent* class would be::

        >>> db = Database()
        >>> @db.add
        ... class Parent(Table):
        ...     children = Join(db, 'Child.parent')
        ...
        >>> @db.add
        ... class Child(Table):
        ...     parent = Field()
        ...
        >>> p = Parent()
        >>> c1 = Child(parent=p)
        >>> c2 = Child(parent=p)
        >>> p.children
        {c1, c2}

    As with a `Field`, a `Join` has read-only attributes *name* and *owner*.
    """

    def __init__(self, *args):
        self._args = args

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            if len(self._args) == 1:
                field = self._args[0]
                table = field.owner
                field = field.name
            else:
                table, field = self._args[1].split('.')
                table = self._args[0][table]
            return table.get(**{field: instance})

    @property
    def name(self):
        return self._name

    @property
    def owner(self):
        return self._owner
