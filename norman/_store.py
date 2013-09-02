# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 David Townshend
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

import collections
from bisect import bisect_left, bisect_right
from ._field import NotSet


class Index(object):

    """
    An index stores records as sorted lists of ``(keyvalue, record)`` pairs,
    where *keyvalue* is a key based on the data cell value, determined by
    the return value of `Field.key`, which should always return the same,
    sortable type.  If a return value cannot be sorted, then it is stored
    separately by its hash, and comparisons (except for equality checks)
    cannot be used with it.  It is is not hashable, then it is stored by `id`,
    so equality checks will actually return identity matches.
    Note that `NotSet` is handled separately, and is never evaluated with
    `Field.key`.  The default `Field.key` returns a tuple of
    ``(type, keyvalue)`` for recognised types.  The implementation is::

        def key(value):
            if isinstance(value, numbers.Real):
                return '0Real', value
            elif isinstance(value, str):
                return '1str', value
            elif isinstance(value, bytes):
                return '2bytes', value
            else:
                raise TypeError

    The following examples show a few example of how this can be used:

        >>> import re
        >>> from norman import Table, Field
        >>> class MyTable(Table):
        ...    numbers = Field(key=lambda x: re.findall('\d+', x))
        ...
        >>> r1 = MyTable(numbers='number 1, numbers 2 and 3')
        >>> r2 = MyTable(numbers='45 and 46')
        >>> r3 = MyTable(numbers='a, b, c = 5, 6, 7')
        >>> r4 = MyTable(numbers='no numbers here')
        >>> set(MyTable.numbers > 'number 3') == set((r2, r3))
        True
        >>> set(MyTable.numbers < '1 or 2') == set((r4,))
        True
    """

    def __init__(self, field):
        self.field = field
        self.clear()

    def __len__(self):
        return (len(self._ordered[0]) +
                sum(len(d) for d in self._unordered.values()))

    def clear(self):
        """
        Delete all items from the index.
        """
        self._ordered = ([], [])
        self._unordered = collections.defaultdict(list)

    def insert(self, value, record):
        """
        Insert a new item.  If equal keys are found, add to the right.
        """
        if value is NotSet:
            self._unordered[NotSet].append((NotSet, record))
        else:
            try:
                key = self.field.key(value)
                i = bisect_right(self._ordered[0], key)
            except (TypeError, ValueError):
                try:
                    key = hash(value)
                except TypeError:
                    key = id(value)
                self._unordered[key].append((value, record))
            else:
                self._ordered[0].insert(i, key)
                self._ordered[1].insert(i, record)

    def remove(self, value, record):
        """
        Remove first occurrence of ``(value, record)``.
        """
        if value is NotSet:
            self._unordered[NotSet].remove((NotSet, record))
            if len(self._unordered[NotSet]) == 0:
                del self._unordered[NotSet]
        else:
            try:
                key = self.field.key(value)
                i = bisect_left(self._ordered[0], key)
                j = bisect_right(self._ordered[0], key)
            except (TypeError, ValueError):
                try:
                    key = hash(value)
                except TypeError:
                    key = id(value)
                self._unordered[key].remove((value, record))
                if len(self._unordered[key]) == 0:
                    del self._unordered[key]
            else:
                index = self._ordered[1][i:j].index(record) + i
                del self._ordered[0][index]
                del self._ordered[1][index]

    def __eq__(self, value):
        """
        Iterate over all items with ``key == value``
        """
        if value is NotSet:
            return (r for v, r in self._unordered[NotSet])
        try:
            key = self.field.key(value)
            i = bisect_left(self._ordered[0], key)
            j = bisect_right(self._ordered[0], key)
        except (TypeError, ValueError):
            try:
                key = hash(value)
            except TypeError:
                key = id(value)
            return (r for v, r in self._unordered[key] if v == value)
        else:
            return iter(self._ordered[1][i:j])

    def __ne__(self, value):
        """
        Iterate over all items with ``key != value``.
        """
        try:
            key = self.field.key(value)
            i = bisect_left(self._ordered[0], key)
            j = bisect_right(self._ordered[0], key)
        except (TypeError, ValueError):
            try:
                key = hash(value)
            except TypeError:
                key = id(value)
            for l in self._unordered.values():
                for d in l:
                    if d[0] != value:
                        yield d[1]
            for r in self._ordered[1]:
                yield r
        else:
            for l in self._unordered.values():
                for r in l:
                    yield r[1]
            for r in self._ordered[1][:i]:
                yield r
            for r in self._ordered[1][j:]:
                yield r

    def __le__(self, value):
        """
        Iterate over all items with ``key <= k``
        """
        key = self.field.key(value)
        i = bisect_right(self._ordered[0], key)
        return iter(self._ordered[1][:i])

    def __lt__(self, value):
        """
        Iterate over all items with ``key < k``
        """
        key = self.field.key(value)
        i = bisect_left(self._ordered[0], key)
        return iter(self._ordered[1][:i])

    def __ge__(self, value):
        """
        Iterate over all items with ``key >= k``
        """
        key = self.field.key(value)
        i = bisect_left(self._ordered[0], key)
        return iter(self._ordered[1][i:])

    def __gt__(self, value):
        """
        Iterate over all items with ``key > k``
        """
        key = self.field.key(value)
        i = bisect_right(self._ordered[0], key)
        return iter(self._ordered[1][i:])

    def __str__(self):
        return str(self.field)


class Store(object):

    """
    Stores are designed to hide the implementation details and expose
    a consistent API, so that they can be switched out without any other
    changes to the table.

    Tables are exposed as an array of cells, where each cell is identified
    by `Table` and `Field` instances.  Cells are unordered, although
    implementations may order them internally.

    The Store is tolerant of missing values.  `get` will return defaults if
    the record requested does not exist.  `set` will add a new record
    if the record does not exist.
    """

    def __init__(self):
        self.indexes = {}
        self.fields = {}
        self.clear()

    def add_field(self, field):
        """
        Called whenever a new field is added to the table.
        """
        self.indexes[field] = Index(field)
        self.fields[field.name] = field

    def add_record(self, record):
        """
        Called whenever a new record is created.
        """
        self._data.setdefault(record, {})
        for field in self.fields.values():
            self.indexes[field].insert(field.default, record)

    def clear(self):
        """
        Delete all records in the store.
        """
        self._data = {}
        for i in self.indexes.values():
            i.clear()

    def get(self, record, field):
        """
        Return the value in a cell specified by *record* and *field*.  This
        should respect any field defaults.  If this is called with a record
        that has not been added, it will be added.
        """
        return self._data.get(record, {}).get(field, field.default)

    def has_record(self, record):
        """
        Return True if the record has an entry in the data store.
        """
        return record in self._data

    def iter_field(self, field):
        """
        Iterate over pairs of ``(record, value)`` for the specified field.
        This should respect any field defaults.  If this is called with a
        field that has not been added, the behaviour is unspecified.
        """
        for record, data in self._data.items():
            yield record, data.get(field, field.default)

    def iter_records(self):
        """
        Return an iterator over all records in the data store.
        """
        return iter(self._data.keys())

    def record_count(self):
        """
        Return the number of records in the table.
        """
        return len(self._data)

    def remove_record(self, record):
        """
        Remove a record.
        """
        for field in self.fields.values():
            value = self.get(record, field)
            self.indexes[field].remove(value, record)
        del self._data[record]

    def remove_field(self, field):
        """
        Remove a field.
        """
        for r in self._data.values():
            r.pop(field, None)

    def set(self, record, field, value):
        """
        Set the data in a record.
        """
        old = self.get(record, field)
        if old is not value:
            self._data[record][field] = value
            index = self.indexes[field]
            index.remove(old, record)
            index.insert(value, record)

    def setdefault(self, field, value):
        """
        Called when the default value of a field in changed.
        """
        if value != field.default:
            index = self.indexes[field]
            unset = set(r for r, d in self._data.items() if field not in d)
            for r in (index == field.default):
                if r in unset:
                    index.remove(self._default, r)
                    index.insert(value, r)
