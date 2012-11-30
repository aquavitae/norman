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

import abc

from ._field import NotSet


_Base = abc.ABCMeta(str('_Base'), (object,), {})


class StoreBase(_Base):

    """
    This is an abstract base class which defines how data is internally
    stored for a table.  Typical examples of how this could be implemented
    include using a numpy array, disk storage, or python builtin types.
    Each storage type has different advantages, and should be chosen depending
    on the intended behaviour of the table.

    Stores are designed to hide the implementation details and expose
    a consistent API, so that they can be switched out without any other
    changes to the table.

    Tables are exposed as an array of records, where each cell in the table
    is identified by a `Table` instance and `Field`.  Cells are unordered,
    although implementations may order them internally.

    The store has two functions, `get` and `set`, which are used to access
    the data.  To support queries, `iter_field` yields pairs of
    ``(record, value)`` for a specific field.  `NotSet` is returned for
    any values which have not been set.  `iter_record` yields all record in
    the data store.

    `set` should dynamically handle new fields and records, i.e. if it is
    called with a record argument which does not yet exist, it should add it.
    """

    @abc.abstractmethod
    def add_record(self, record):
        """
        Called whenever a new record is created.  The main purpose of this
        is to ensure that subsequent queries such as `iter_records` return
        ther correct results, even if no data has actually been set on the
        record.
        """
        return NotImplemented

    @abc.abstractmethod
    def clear(self):
        """
        Delete all records and fields in the store.
        """
        return NotImplemented

    @abc.abstractmethod
    def has_record(self, record):
        """
        Return True if the record has an entry in the data store.
        """
        return NotImplemented

    @abc.abstractmethod
    def get(self, record, field):
        """
        Return the item in a cell by *record* and *field*.  If the value
        does not exist in the data store, the field's default should be
        returned.
        """
        return NotImplemented

    @abc.abstractmethod
    def iter_field(self, name):
        """
        Iterate over pairs of (record, value) for the specified field, using
        ``field.default`` for missing values.
        """
        return NotImplemented

    @abc.abstractmethod
    def iter_records(self):
        """
        Return an iterator over all records in the data store.
        """
        return NotImplemented

    @abc.abstractmethod
    def record_count(self):
        """
        Return the number of records in the table.
        """
        return NotImplemented

    @abc.abstractmethod
    def remove_record(self, record):
        """
        Remove a record from the data store.
        """
        return NotImplemented

    @abc.abstractmethod
    def remove_field(self, name):
        """
        Remove a field.
        """
        return NotImplemented

    @abc.abstractmethod
    def set(self, key, field, value):
        """
        Set the data in a record.  If the record matching key does not exist
        then it is created.
        """
        return NotImplemented


class DefaultStore(StoreBase):

    """
    This is the default store used, and is implemented using python builtin
    objects.  It provides a balance between speed and memory footprint.
    """

    def __init__(self):
        self._data = {}

    def add_record(self, record):
        self._data.setdefault(record, {})

    def clear(self):
        self._data = {}

    def get(self, record, field):
        try:
            return self._data[record][field]
        except KeyError:
            return field.default

    def has_record(self, record):
        return record in self._data

    def iter_field(self, field):
        for i, r in self._data.items():
            yield i, r.get(field, field.default)

    def iter_records(self):
        return iter(self._data.keys())

    def record_count(self):
        return len(self._data)

    def remove_record(self, record):
        del self._data[record]

    def remove_field(self, field):
        for r in self._data.values():
            r.pop(field, None)

    def set(self, key, field, value):
        self._data.setdefault(key, {})[field] = value
