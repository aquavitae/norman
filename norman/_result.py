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


class _Result(object):

    """
    A set-like object which represents the results of a query.

    This object should never be instantiated directly, instead it should
    be created as the result of a query on a `Table` or `Field`.

    This object allows most operations permitted on sets, such as unions
    and intersections.  Comparison operators (such as ``<``) are not
    supported, except for equality tests.  If these are needed, then it is
    best to convert the `_Result` to a set.

    The following operations are supported:

    =================== =======================================================
    Operation           Description
    =================== =======================================================
    ``r in a``          Return `True` if record ``r`` is in the results ``a``.
    ``len(a)``          Return the length of results ``a``.
    ``iter(a)``         Return an iterator over records in ``a``.
    ``a == b``          Return `True` if ``a`` and ``b`` are both `_Result`
                        instances and contain the same items in the same
                        order
    ``a != b``          Return `True` if ``not a == b``
    ``a & b``           Return a new `_Result` object containing records in
                        both ``a`` and ``b``.
    ``a | b``           Return a new `_Result` object containing records in
                        either ``a`` or ``b``.
    ``a ^ b``           Return a new `_Result` object containing records in
                        either ``a`` or ``b``, but not both.
    ``a - b``           Return a new `_Result` object containing records in
                        ``a`` which are not in ``b``.
    ``a.field(name)``   Return an iterator over values in field *name* in
                        each record.
    ``a.one()``         Return a single record.
    ``a.sort(field)``   Return a new `_Result` object containing records
                        sorted by *field*
    =================== =======================================================
    """

    def __init__(self, table, matches):
        self._table = table
        self._m = matches

    def __and__(self, other):
        return _Result(self._table, set(self._m) & set(other))

    def __contains__(self, record):
        return record in set(self._m)

    def __eq__(self, other):
        return isinstance(other, _Result) and list(self) == list(other)

    def __iter__(self):
        return iter(self._m)

    def __len__(self):
        return len(set(self._m))

    def __or__(self, other):
        return _Result(self._table, set(self._m) | set(other))

    def __repr__(self):
        return '_Results(' + ', '.join(repr(i) for i in self) + ')'

    def __sub__(self, other):
        return _Result(self._table, set(self._m) - set(other))

    def __xor__(self, other):
        return _Result(self._table, set(self._m) ^ set(other))

    def field(self, name):
        """
        Return a list of field values.
        """
        return [getattr(r, name) for r in self]

    def one(self):
        """
        Return a single record matching *kwargs*.

        If the results have been sorted, then the first record is returned,
        otherwise a random record returned.
        """
        return next(iter(self._m))

    def sort(self, field, reverse=False):
        """
        Return a `_Result` object where each record is sorted by *field*.
        """
        key = lambda r: getattr(r, field)
        return _Result(self._table, sorted(self, key=key, reverse=reverse))
