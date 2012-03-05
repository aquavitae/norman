#!/usr/bin/env python3
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

import collections
import weakref

from dtlibs.mock import assert_raised
from dtlibs import dev
from dtlibs.database import Table, Field
from dtlibs import database

###############################################################################
# Some test data

def convidx(table, index):
    'Utility to convert an index (i.e. defaultdict with a weakset) to a dict'
    return dict((value, set(table._instances[k] for k in keys)) \
                for value, keys in table._indexes[index].items())

def test_conv_index():
    class K: pass
    k1 = K()
    k2 = K()
    class T:
        _instances = {k1: 'i1', k2: 'i2'}
        _indexes = {'f1': collections.defaultdict(weakref.WeakSet)}
    T._indexes['f1']['a'].add(k1)
    T._indexes['f1']['a'].add(k2)
    T._indexes['f1']['b'].add(k1)
    assert convidx(T, 'f1') == {'a': {'i1', 'i2'}, 'b': {'i1'}}


class Test_I:
    'Test that I is hashable and weakrefable'

    def test_hash(self):
        i1 = database._table._I()
        i2 = database._table._I()
        h1 = hash(i1)
        h2 = hash(i2)
        assert h1 != h2

    def test_weakref(self):
        i = database._table._I()
        ref = weakref.ref(i)
        assert ref() is i
        del i
        assert ref() is None


class TestTable:

    def setup(self):
        class T(Table):
            oid = Field(index=True)
            name = Field(index=True)
            age = Field()
        self.T = T

    def test_init_empty(self):
        'Test a few ways of initialising.'
        t = self.T()
        assert t.oid is None
        assert t.name is None
        assert t.age is None
        assert convidx(self.T, 'oid') == {None: {t}}, convidx(self.T, 'oid')
        assert convidx(self.T, 'name') == {None: {t}}
        assert 'age' not in t._indexes

    def test_init_single(self):
        t = self.T(oid=1)
        assert t.oid == 1, t.oid
        assert t.name is None
        assert t.age is None
        assert convidx(self.T, 'oid') == {1: {t}}
        assert convidx(self.T, 'name') == {None: {t}}
        assert 'age' not in t._indexes

    def test_init_many(self):
        t = self.T(oid=1, name='Mike', age=23)
        assert t.oid == 1
        assert t.name is 'Mike'
        assert t.age is 23
        assert convidx(self.T, 'oid') == {1: {t}}
        assert convidx(self.T, 'name') == {'Mike': {t}}
        assert 'age' not in t._indexes

    def test_init_bad_kwargs(self):
        'Invalid keywords raise AttributeError'
        with assert_raised(AttributeError):
            self.T(bad='field')

    def test_indexes(self):
        'Test that indexes are created.'
        assert self.T.name.index
        assert self.T.oid.index
        assert sorted(self.T._indexes.keys()) == ['name', 'oid']

    def test_inherited_indexes(self):
        'Test that indexes are created in inherited classes.'
        class T(self.T):
            pass
        assert T.name.index
        assert T.oid.index
        assert sorted(T._indexes.keys()) == ['name', 'oid']

    def test_len(self):
        'len(Table) returns the number of records.'
        self.T(oid=1)
        self.T(oid=2)
        self.T(oid=3)
        assert len(self.T) == 3

    def test_contains(self):
        'Test ``record in Table``'
        t1 = self.T(oid=1)
        t2 = self.T(oid=2)
        assert t1 in self.T

    def test_indexes_updated(self):
        'Test that indexes are updated when a value changes'
        t = self.T(oid=1)
        i = convidx(self.T, 'oid')
        assert i == {1: {t}}, i

    def test_get(self):
        'Test that get returns the matching records.'
        p1 = self.T(oid=1)
        p2 = self.T(oid=2)
        p3 = self.T(oid=3)
        p = set(self.T.get(oid=1))
        assert p == {p1}, p

    def test_get_other_attr(self):
        'Test that get finds matches for non-indexed fields.'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        p = set(self.T.get(age=23))
        assert p == {p1, p3}, p

    def test_index_speed(self):
        'Getting indexed fields should be ten times faster'
        count = 500
        for i in range(count):
            self.T(oid=i, name='Mike', age=int(i % 10))
        timer = dev.Timer()
        with timer('fast'):
            self.T.get(id=300)
        with timer('slow'):
            self.T.get(age=5)
        assert timer['fast'] * 10 > timer['slow']

    def test_delete_instance(self):
        'Test deleting a single instance'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete(p1)
        assert p1 not in self.T
        assert p2 in self.T
        assert p3 in self.T

    def test_delete_instances(self):
        'Test deleting a list of instances'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete([p1, p2])
        assert p1 not in self.T
        assert p2 not in self.T
        assert p3 in self.T

    def test_delete_attribute(self):
        'Test deletion by attribute'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete(oid=2)
        assert p1 in self.T
        assert p2 not in self.T
        assert p3 in self.T

    def test_delete_all(self):
        'Test that delete with no args clears all instances.'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete()
        assert len(self.T) == 0

    def test_set_invalid(self):
        'Test the case where validate fails.'
        class T(self.T):
            def validate(self):
                assert self.oid != 1

        t = T()
        t.oid = 2
        with assert_raised(ValueError):
            t.oid = 1
        assert t.oid == 2

    def test_validate_changes(self):
        'Test the case where validate changes a value.'
        class T(self.T):
            def validate(self):
                if self.name is not None:
                    self.name = self.name.upper()

        t = T()
        t.name = 'abc'
        assert t.name == 'ABC'

    def test_validate_changes_fails(self):
        'Test the case where validate changes a value then fails.'
        class T(self.T):
            def validate(self):
                if self.name is not None:
                    self.name = self.name.upper()
                    assert len(self.name) == 3

        t = T()
        t.name = 'ABC'
        with assert_raised(ValueError):
            t.name = 'abcd'
        assert t.name == 'ABC', t.name
