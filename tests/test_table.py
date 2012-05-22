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

import collections
import weakref
import timeit

from nose.tools import assert_raises
from norman import Table, Field, NotSet, _table

import sys
if sys.version < '3':
    range = xrange

###############################################################################
# Some test data


def convidx(table, index):
    'Utility to convert an index (i.e. defaultdict with a weakset) to a dict'
    r = [(value, set(table._instances[k] for k in keys)) \
                for value, keys in table._indexes[index].items()]
    return dict(a for a in r if a[1])


def test_conv_index():
    class K(object): pass
    k1 = K()
    k2 = K()
    class T(object):
        _instances = {k1: 'i1', k2: 'i2'}
        _indexes = {'f1': collections.defaultdict(weakref.WeakSet),
                    'f2': collections.defaultdict(weakref.WeakSet)}
    T._indexes['f1']['a'].add(k1)
    T._indexes['f1']['a'].add(k2)
    T._indexes['f1']['b'].add(k1)
    T._indexes['f2']['a'] #note: is this actually required?
    assert convidx(T, 'f1') == {'a': set(['i1', 'i2']), 'b': set(['i1'])}
    assert convidx(T, 'f2') == {}

class Test_I(object):

    def test_hash(self):
        'Test that _I is hashable.'
        i1 = _table._I()
        i2 = _table._I()
        h1 = hash(i1)
        h2 = hash(i2)
        assert h1 != h2

    def test_weakref(self):
        'Test that _I can have a weak ref.'
        i = _table._I()
        ref = weakref.ref(i)
        assert ref() is i
        del i
        assert ref() is None


class TestTable(object):

    def setup(self):
        class T(Table):
            oid = Field(index=True)
            name = Field(index=True)
            age = Field()
        self.T = T

    def test_init_empty(self):
        'Test initialisation with no arguments.'
        t = self.T()
        assert t.oid is NotSet
        assert t.name is NotSet
        assert t.age is NotSet
        assert convidx(self.T, 'oid') == {NotSet: set([t])}, convidx(self.T, 'oid')
        assert convidx(self.T, 'name') == {NotSet: set([t])}
        assert 'age' not in t._indexes

    def test_init_single(self):
        'Test initialisation with a single argument.'
        t = self.T(oid=1)
        assert t.oid == 1, t.oid
        assert t.name is NotSet
        assert t.age is NotSet
        assert convidx(self.T, 'oid') == {1: set([t])}, convidx(self.T, 'oid')
        assert convidx(self.T, 'name') == {NotSet: set([t])}
        assert 'age' not in t._indexes

    def test_init_many(self):
        'Test initialisation with many arguments.'
        t = self.T(oid=1, name='Mike', age=23)
        assert t.oid == 1
        assert t.name is 'Mike'
        assert t.age is 23
        assert convidx(self.T, 'oid') == {1: set([t])}
        assert convidx(self.T, 'name') == {'Mike': set([t])}
        assert 'age' not in t._indexes

    def test_init_bad_kwargs(self):
        'Invalid keywords raise AttributeError.'
        with assert_raises(AttributeError):
            self.T(bad='field')

    def test_init_invalid(self):
        class T(Table):
            v = Field()
            def validate(self):
                assert False
        with assert_raises(ValueError):
            T(v=1)

    def test_name(self):
        'Test that Table.name == "Table"'
        assert self.T.__name__ == 'T'

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

    def test_contains_method(self):
        'Test the `contains` method.'
        t1 = self.T(oid=1)
        t2 = self.T(oid=2)
        assert self.T.contains(oid=1)
        assert not self.T.contains(oid=3)

    def test_iter(self):
        'Test iter(table)'
        t1 = self.T(oid=1)
        t2 = self.T(oid=2)
        result = set(i for i in self.T)
        assert result == set([t1, t2])

    def test_iter_method(self):
        'Test that iter returns the matching records.'
        p1 = self.T(oid=1)
        p2 = self.T(oid=2)
        p3 = self.T(oid=3)
        p = set(self.T.iter(oid=1))
        assert p == set([p1]), p

    def test_iter_other_attr(self):
        'Test that iter finds matches for non-indexed fields.'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        p = set(self.T.iter(age=23))
        assert p == set([p1, p3]), p

    def test_get(self):
        p1 = self.T(oid=1)
        p2 = self.T(oid=2)
        p3 = self.T(oid=3)
        p = self.T.get(oid=1)
        assert p == set([p1])

    def test_indexes_updated(self):
        'Test that indexes are updated when a value changes'
        t = self.T(oid=1)
        i = convidx(self.T, 'oid')
        assert i == {1: set([t])}, i

    def test_index_speed(self):
        'Getting indexed fields should be ten times faster'
        count = 500
        for i in range(count):
            self.T(oid=i, name='Mike', age=int(i % 10))
        number = 100000
        fast = timeit.timeit(lambda: self.T.iter(id=300), number=number)
        slow = timeit.timeit(lambda: self.T.iter(age=5), number=number)
        assert fast * 10 > slow

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
        with assert_raises(ValueError):
            t.oid = 1
        assert t.oid == 2

    def test_validate_changes(self):
        'Test the case where validate changes a value.'
        class T(self.T):
            def validate(self):
                if self.name:
                    self.name = self.name.upper()

        t = T()
        t.name = 'abc'
        assert t.name == 'ABC'

    def test_validate_changes_fails(self):
        'Test the case where validate changes a value then fails.'
        class T(self.T):
            def validate(self):
                if self.name:
                    self.name = self.name.upper()
                    assert len(self.name) == 3

        t = T()
        t.name = 'ABC'
        with assert_raises(ValueError):
            t.name = 'abcd'
        assert t.name == 'ABC', t.name


class TestUnique(object):

    def setup(self):
        class T(Table):
            oid = Field(unique=True)
        self.T = T

    def test_unique_implies_index(self):
        'Unique implies index'
        assert self.T.oid.index

    def test_unique_init(self):
        'Test the initialisation of a duplicate record.'
        t1 = self.T(oid=3)
        with assert_raises(ValueError):
            t2 = self.T(oid=3)

    def test_unique_set(self):
        'Test setting a record to a duplicate value.'
        t1 = self.T(oid=1)
        t2 = self.T(oid=2)
        with assert_raises(ValueError):
            t2.oid = 1

    def test_unique_delete_set(self):
        'Deleting a record allows the value to be reused.'
        t1 = self.T(oid=1)
        self.T.delete(t1)
        self.T(oid=1)

    def test_unique_multiple(self):
        'Test multiple unique fields'
        class T(Table):
            a = Field(unique=True)
            b = Field(unique=True)
        T(a=1, b=2)
        T(a=1, b=3)
        T(a=2, b=2)
        with assert_raises(ValueError):
            T(a=1, b=2)


class TestValidateDelete(object):

    def setup(self):
        class T(Table):
            value = Field()
            def validate_delete(self):
                assert self.value > 1
        self.T = T

    def test_valid(self):
        t = self.T(value=5)
        assert self.T.get() == set([t])
        self.T.delete(value=5)
        assert self.T.get() == set()

    def test_invalid(self):
        t = self.T(value=0)
        assert self.T.get() == set([t])
        with assert_raises(ValueError):
            self.T.delete(value=0)
        assert self.T.get() == set([t])

    def test_propogate(self):
        class T(Table):
            value = Field()
            def validate_delete(self):
                if self.value != 3:
                    T.delete(value=3)
        t1 = T(value=1)
        t2 = T(value=2)
        t3 = T(value=3)
        T.delete(value=1)
        assert T.get() == set([t2])
