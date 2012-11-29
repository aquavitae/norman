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

from __future__ import with_statement
from norman import Index, NotSet


class TestIndex_Empty(object):
    'Tests starting with an empty index'

    def setup(self):
        self.i = Index()

    def test_insert_NotSet(self):
        self.i.insert(NotSet, 2)
        assert self.i._bins == (set([2]), ([], []))
        self.i.insert(NotSet, 3)
        assert self.i._bins == (set([2, 3]), ([], []))
        self.i.insert(NotSet, 4)
        assert self.i._bins == (set([2, 3, 4]), ([], []))

    def test_insert_value(self):
        self.i.insert(2, 'v2')
        assert self.i._bins == (set(), ([2], ['v2']))
        self.i.insert(1, 'v1')
        assert self.i._bins == (set(), ([1, 2], ['v1', 'v2']))
        self.i.insert(3, 'v3')
        assert self.i._bins == (set(), ([1, 2, 3], ['v1', 'v2', 'v3']))
        self.i.insert(2, 'v1.2')
        assert self.i._bins == (set(), ([1, 2, 2, 3],
                                        ['v1', 'v2', 'v1.2', 'v3']))

    def test_insert_mixture(self):
        self.i.insert(2, 'v2')
        assert self.i._bins == (set(), ([2], ['v2']))
        self.i.insert(NotSet, 'n1')
        assert self.i._bins == (set(['n1']), ([2], ['v2']))
        self.i.insert(1, 'v1')
        assert self.i._bins == (set(['n1']), ([1, 2], ['v1', 'v2']))
        self.i.insert(NotSet, 'n2')
        assert self.i._bins == (set(['n1', 'n2']), ([1, 2], ['v1', 'v2']))

    def test_keyfunc(self):
        i = Index(keyfunc=str)
        i.insert(2, 'v2')
        i.insert(NotSet, 'n1')
        i.insert('a', 'A')
        assert i._bins == (set(['n1']), (['2', 'a'], ['v2', 'A']))
        it = list(i.iter_gt(2))
        assert it == ['A']


class TestPopulated(object):

    def setup(self):
        self.i = Index()
        self.i._bins = (set(['n1', 'n2']), ([1, 2, 2, 3],
                                            ['v1', 'v2a', 'v2b', 'v3']))

    def test_remove_NotSet(self):
        self.i.remove(NotSet, 'n2')
        assert self.i._bins == (set(['n1']), ([1, 2, 2, 3],
                                              ['v1', 'v2a', 'v2b', 'v3']))

    def test_remove_value(self):
        self.i.remove(2, 'v2b')
        assert self.i._bins == (set(['n1', 'n2']), ([1, 2, 3],
                                                    ['v1', 'v2a', 'v3']))

    def test_len(self):
        assert len(self.i) == 6, len(self.i)

    def test_iter_value(self):
        got = set(self.i.iter_eq(2))
        assert got == set(['v2a', 'v2b'])

    def test_iter_NotSet(self):
        got = set(self.i.iter_eq(NotSet))
        assert got == set(['n1', 'n2'])

    def test_iter_ne_value(self):
        got = set(self.i.iter_ne(2))
        assert got == set(['n1', 'n2', 'v1', 'v3']), got

    def test_iter_ne_NotSet(self):
        got = set(self.i.iter_ne(NotSet))
        assert got == set(['v1', 'v2a', 'v2b', 'v3'])

    def test_iter_lt(self):
        got = set(self.i.iter_lt(2))
        assert got == set(['v1'])

    def test_iter_le(self):
        got = set(self.i.iter_le(2))
        assert got == set(['v1', 'v2a', 'v2b'])

    def test_iter_gt(self):
        got = set(self.i.iter_gt(2))
        assert got == set(['v3'])

    def test_iter_ge(self):
        got = set(self.i.iter_ge(2))
        assert got == set(['v2a', 'v2b', 'v3'])
