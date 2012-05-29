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


class Group(object):

    """
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
    <generator object iter at ...>
    >>> parent.children.add(name='c')
    Child('c')
    """

    def __init__(self, table, matcher=None, **kwargs):
        self._matcher = matcher
        self._kw = kwargs
        self._table = table

    def __get__(self, instance, owner):
        self._instance = instance
        return self

    @property
    def table(self):
        """
        Read-only property containing the `Table` object referred to.
        """
        return self._table

    def _getkw(self, kwargs=None):
        """
        Return the final kwargs to use.
        """
        if kwargs is None:
            kwargs = {}
        kwargs.update(self._kw)
        if self._matcher is not None:
            kw = self._matcher(self._instance)
            kwargs.update(kw)
        return kwargs

    def __iter__(self):
        return self._table.iter(**self._getkw())

    def __contains__(self, record):
        for k, v in self._getkw().items():
            if getattr(record, k) != v:
                return False
        return record in self._table

    def __len__(self):
        return len(self._table.get(**self._getkw()))

    def contains(self, **kwargs):
        """
        Return `True` if the `Group` contains records matching *kwargs*.
        """

        return self._table.contains(**self._getkw(kwargs))

    def iter(self, **kwargs):
        """
        Iterate over records in the `Group` matching *kwargs*.
        """
        return self._table.iter(**self._getkw(kwargs))

    def get(self, **kwargs):
        """
        Return a set of all records in the `Group` matching *kwargs*.
        """
        return self._table.get(**self._getkw(kwargs))

    def add(self, **kwargs):
        """
        Create a new record of the reference `table`.

        *kwargs* is updated with the keyword arguments defining this `Group`
        and the resulting dict used as the initialisation parameters of
        `table`.
        """
        return self._table(**self._getkw(kwargs))

    def delete(self, *records, **kwargs):
        """
        Delete delete all instances in *records* which match *keywords*.

        This only deletes instances in the `Group`, but it completely deletes
        them.   If *records* is omitted then the entire `Group` is searched.

        .. seealso:: Table.delete
        """
        kwargs = self._getkw(kwargs)
        for record in records:
            for k, v in kwargs.items():
                if getattr(record, k) != v:
                    raise ValueError("record not in group")
        return self._table.delete(*records, **kwargs)
