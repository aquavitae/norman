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

import itertools
from bisect import bisect_left, bisect_right

from ._field import NotSet


class Index(object):

    """
    An index stored records as a sorted list of ``(value, key)`` pairs, where
    *value* is the data cell value and *key* is the instance.  If *value*
    is `NotSet`, then the instances are stored in a separate list, since
    ordered queries on `NotSet` values don't make sense.  A *keyfunc*
    can be set which converts *value* into a key for sorting.  This is useful
    when, for example, the field can contain numerical or string values, so
    that ``4 < '5'``.  This behaves in the same way as the *key* argument
    to `sorted`.
    """

    def __init__(self, keyfunc=None):
        key = (lambda x: x) if keyfunc is None else keyfunc
        self._keyfunc = key
        self._bins = (set(), ([], []))

    def __len__(self):
        return len(self._bins[0]) + len(self._bins[1][0])

    def clear(self):
        """
        Delete all items from the index.
        """
        self._bins = (set(), ([], []))

    def insert(self, value, record):
        """
        Insert a new item.  If equal keys are found, add to the right.
        """
        if value is NotSet:
            self._bins[0].add(record)
        else:
            keys, records = self._bins[1]
            k = self._keyfunc(value)
            i = bisect_right(keys, k)
            keys.insert(i, k)
            records.insert(i, record)

    def remove(self, value, record):
        """
        Remove first occurence of value, record.
        """
        if value is NotSet:
            self._bins[0].remove(record)
        else:
            keys, records = self._bins[1]
            key = self._keyfunc(value)
            i = bisect_left(keys, key)
            j = bisect_right(keys, key)
            index = records[i:j].index(record) + i
            del keys[index]
            del records[index]

    def iter_eq(self, k):
        """
        Iterate over all items with ``key == k``
        """
        if k is NotSet:
            return iter(self._bins[0])
        else:
            keys, records = self._bins[1]
            k = self._keyfunc(k)
            i = bisect_left(keys, k)
            j = bisect_right(keys, k)
            return iter(records[i:j])

    def iter_ne(self, k):
        """
        Iterate over all items with ``key != k``
        """
        if k is NotSet:
            return iter(self._bins[1][1])
        else:
            keys, records = self._bins[1]
            k = self._keyfunc(k)
            i = bisect_left(keys, k)
            j = bisect_right(keys, k)
            it1 = iter(self._bins[0])
            it2 = iter(records[:i])
            it3 = iter(records[j:])
            return itertools.chain(it1, it2, it3)

    def iter_le(self, k):
        """
        Iterate over all items with ``key <= k``
        """
        keys, records = self._bins[1]
        k = self._keyfunc(k)
        i = bisect_right(keys, k)
        return iter(records[:i])

    def iter_lt(self, k):
        """
        Iterate over all items with ``key < k``
        """
        keys, records = self._bins[1]
        k = self._keyfunc(k)
        i = bisect_left(keys, k)
        return iter(records[:i])

    def iter_ge(self, k):
        """
        Iterate over all items with ``key >= k``
        """
        keys, records = self._bins[1]
        k = self._keyfunc(k)
        i = bisect_left(keys, k)
        return iter(records[i:])

    def iter_gt(self, k):
        """
        Iterate over all items with ``key > k``
        """
        keys, records = self._bins[1]
        k = self._keyfunc(k)
        i = bisect_right(keys, k)
        return iter(records[i:])
