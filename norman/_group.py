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

    def __init__(self, table, matcher=None, **kwargs):
        self._matcher = matcher
        self._kw = kwargs
        self._table = table

    def __get__(self, instance, owner):
        self._instance = instance
        return self

    @property
    def table(self):
        return self._table

    def _getkw(self, kwargs=None):
        'Return the final kwargs to use'
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
        return self._table.contains(**self._getkw(kwargs))

    def iter(self, **kwargs):
        return self._table.iter(**self._getkw(kwargs))

    def get(self, **kwargs):
        return self._table.get(**self._getkw(kwargs))

    def add(self, **kwargs):
        return self._table(**self._getkw(kwargs))

    def delete(self, *args, **kwargs):
        kwargs = self._getkw(kwargs)
        for record in args:
            for k, v in kwargs.items():
                if getattr(record, k) != v:
                    raise ValueError("record not in group")
        return self._table.delete(*args, **kwargs)
