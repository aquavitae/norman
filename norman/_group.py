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


class Group:

    def __init__(self, table, **kwargs):
        self._kw = kwargs
        self._table = table

    @property
    def table(self):
        return self._table

    def __iter__(self):
        return self._table.iter(**self._kw)

    def __contains__(self, record):
        for k, v in self._kw.items():
            if getattr(record, k) != v:
                return False
        return record in self._table

    def __len__(self):
        return len(self._table.get(**self._kw))

    def contains(self, **kwargs):
        kwargs.update(self._kw)
        return self._table.contains(**kwargs)

    def iter(self, **kwargs):
        kwargs.update(self._kw)
        return self._table.iter(**kwargs)

    def get(self, **kwargs):
        kwargs.update(self._kw)
        return self._table.get(**kwargs)

    def delete(self, *args, **kwargs):
        for record in args:
            for k, v in self._kw.items():
                if getattr(record, k) != v:
                    raise ValueError("record not in group")
        kwargs.update(self._kw)
        return self._table.delete(*args, **kwargs)
