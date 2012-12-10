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

from nose.tools import assert_raises

from norman import NotSet, Field
from norman.store import Store, Index

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


##### Index tests

class TestIndex_Ordered(object):
    'Tests starting with an empty index'

    def setup(self):
        field = Mock(key=lambda x: x)
        self.i = Index(field)
        self.orecords = ['M' + str(i) for i in range(6)]
        self.urecords = ['U0', 'U1', 'U2']
        self.i._ordered = ([0, 1, 2, 3, 3, 4], [r for r in self.orecords])
        self.ordered = ([0, 1, 2, 3, 3, 4], [r for r in self.orecords])
        self.unordered = self.i._unordered.copy()
        self.i._unordered[-1] = [('1', self.urecords[0]),
                                 ('1', self.urecords[1])]
        self.i._unordered[-2] = [('2', self.urecords[2])]
        self.unordered[-1] = [('1', self.urecords[0]),
                              ('1', self.urecords[1])]
        self.unordered[-2] = [('2', self.urecords[2])]

    def test_insert(self):
        r = Mock()
        self.i.insert(1, r)
        self.orecords.insert(2, r)
        assert self.i._ordered == ([0, 1, 1, 2, 3, 3, 4], self.orecords)
        assert self.i._unordered == self.unordered

    def test_len(self):
        assert len(self.i) == 9, len(self.i)

    def test_remove(self):
        self.i.remove(2, self.orecords[2])
        del self.orecords[2]
        expect = ([0, 1, 3, 3, 4], self.orecords)
        assert self.i._ordered == expect
        assert self.i._unordered == self.unordered

    def test_iter_eq(self):
        got = set(self.i == 3)
        expect = set(self.orecords[3:5])
        assert got == expect, (got, expect)

    def test_iter_ne(self):
        expect = set(self.orecords[:3] + self.orecords[5:] + self.urecords)
        got = set(self.i != 3)
        assert got == expect, (got, expect)

    def test_iter_lt(self):
        got = set(self.i < 3)
        expect = set(self.orecords[:3])
        assert got == expect, (got, expect)

    def test_iter_le(self):
        got = set(self.i <= 3)
        expect = set(self.orecords[:5])
        assert got == expect, (got, expect)

    def test_iter_gt(self):
        got = set(self.i > 2)
        expect = set(self.orecords[3:])
        assert got == expect, (got, expect)

    def test_iter_ge(self):
        got = set(self.i >= 2)
        expect = set(self.orecords[2:])
        assert got == expect, (got, expect)


class TestIndex_UnOrdered(object):
    'Tests starting with an empty index'

    def setup(self):
        def key(value):
            raise TypeError
        field = Mock(key=key)
        self.i = Index(field)
        self.orecords = ['M' + str(i) for i in range(6)]
        self.urecords = ['U0', 'U1', 'U2']
        self.i._ordered = ([0, 1, 2, 3, 3, 4], [r for r in self.orecords])
        self.ordered = ([0, 1, 2, 3, 3, 4], [r for r in self.orecords])
        self.unordered = self.i._unordered.copy()
        self.i._unordered[-1] = [('1', self.urecords[0]),
                                 ('1', self.urecords[1])]
        self.i._unordered[-2] = [('2', self.urecords[2])]
        self.unordered[-1] = [('1', self.urecords[0]),
                              ('1', self.urecords[1])]
        self.unordered[-2] = [('2', self.urecords[2])]

        def mockhash(v):
            try:
                return -int(v)
            except ValueError:
                raise TypeError
        patch('norman.store.hash', mockhash, create=True).start()
        patch('norman.store.id', lambda v: 10, create=True).start()

    def teardown(self):
        patch.stopall()

    def test_insert1(self):
        r = Mock()
        self.i.insert('4', r)
        self.unordered[-4] = [('4', r)]
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_insert2(self):
        r = Mock()
        self.i.insert('2', r)
        self.unordered[-2].append(('2', r))
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_insert_id(self):
        r = Mock()
        self.i.insert('a', r)
        self.unordered[10] = [('a', r)]
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_insert_NotSet(self):
        r = Mock()
        self.i.insert(NotSet, r)
        self.unordered[NotSet] = [(NotSet, r)]
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_remove(self):
        self.i.remove('1', self.urecords[1])
        self.unordered[-1].pop()
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_remove_id(self):
        self.i.remove('2', self.urecords[2])
        del self.unordered[-2]
        assert self.i._unordered == self.unordered
        assert self.i._ordered == self.ordered

    def test_iter_eq(self):
        expect = set(self.urecords[:2])
        got = set(self.i == '1')
        assert got == expect, (got, expect)

    def test_iter_ne(self):
        expect = set([self.urecords[2]] + self.orecords)
        got = set(self.i != '1')
        assert got == expect, (got, expect)

    def test_comparison(self):
        with assert_raises(TypeError):
            set(self.i < '1')
        with assert_raises(TypeError):
            set(self.i <= '1')
        with assert_raises(TypeError):
            set(self.i > '1')
        with assert_raises(TypeError):
            set(self.i >= '1')


class TestIndexCornerCases(object):

    def test_notset(self):
        field = Field()
        i = Index(field)
        r = Mock()
        i.insert(NotSet, r)
        assert i._unordered[NotSet] == [(NotSet, r)]


class TestStore(object):

    def setup(self):
        self.full = Field(default=NotSet)
        self.sparse = Field(default= -1)
        self.missing = Field(default=NotSet)
        self.full._name = 'full'
        self.sparse._name = 'sparse'
        self.missing._name = 'missing'
        self.store = Store()
        self.store.add_field(self.full)
        self.store.add_field(self.sparse)

    def populate(self):
        for i in range(5):
            self.store.add_record(str(i))
            self.store.set(str(i), self.full, i)
        for i in [1, 3]:
            self.store.set(str(i), self.sparse, i)

    def test_add_field(self):
        self.populate()
        self.store.add_field(self.missing)
        assert self.store.get('0', self.missing) == NotSet

    def test_add_record(self):
        self.store.add_record('new')
        assert self.store.has_record('new')

    def test_clear(self):
        self.populate()
        self.store.clear()
        assert self.store.record_count() == 0
        for index in self.store.indexes.values():
            assert len(index) == 0

    def test_get(self):
        self.populate()
        assert self.store.get('0', self.full) == 0

    def test_has_record(self):
        self.populate()
        assert self.store.has_record('0')
        assert not self.store.has_record('not a record')

    def test_iter_field_full(self):
        self.populate()
        got = set(self.store.iter_field(self.full))
        expect = set([(str(i), i) for i in range(5)])
        assert got == expect, got

    def test_iter_field_sparse(self):
        self.populate()
        got = set(self.store.iter_field(self.sparse))
        expect = set([('0', -1), ('1', 1), ('2', -1), ('3', 3), ('4', -1)])
        assert got == expect, got

    def test_iter_records(self):
        self.populate()
        it = self.store.iter_records()
        assert set(it) == set('012324')

    def test_record_count(self):
        self.populate()
        assert self.store.record_count() == 5

    def test_remove_record(self):
        self.populate()
        self.store.remove_record('3')
        assert set(self.store.iter_records()) == set('0124')

    def test_remove_field(self):
        # This merely tests that it runs.
        self.populate()
        self.store.remove_field(self.full)

    def test_set_overwrite(self):
        self.populate()
        self.store.set('1', self.sparse, 'new value')
        assert self.store.get('1', self.sparse) == 'new value'


class TestStoreIndex(object):

    def setup(self):
        self.f = Field()
        self.f._name = 'f'
        self.store = Store()
        self.store.add_field(self.f)
        self.index = self.store.indexes[self.f]

    def test_add_record(self):
        self.store.add_record('new')
        assert self.index._unordered[NotSet] == [(NotSet, 'new')]
        assert self.index._ordered == ([], [])

    def test_remove_record(self):
        self.store.add_record('new')
        self.store.remove_record('new')
        assert self.index._unordered == {}
        assert self.index._ordered == ([], [])

    def test_set(self):
        self.store.add_record('new')
        self.store.set('new', self.f, 'value')
        assert self.index._unordered == {}
        assert self.index._ordered == ([('1str', 'value')], ['new'])
