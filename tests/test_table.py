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
import re
import weakref
import timeit

from nose.tools import assert_raises
from norman import Table, Field, NotSet, Join, _table, ValidationError
from norman._query import Query

import sys
if sys.version < '3':
    range = xrange


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


class TestFields(object):

    def setup(self):
        class S(Table):
            t = Field()

        class T(Table):
            me = Field()
            other = Join(S.t)

        self.T = T

    def test_field_name(self):
        'Test that fields have a read-only name'
        assert self.T.me.name == 'me'
        with assert_raises(AttributeError):
            self.T.me.name = 'notme'

    def test_field_owner(self):
        'Test that fields have a read-only owner'
        assert self.T.me.owner is self.T
        with assert_raises(AttributeError):
            self.T.me.owner = 'notme'

    def test_join_name(self):
        'Test that joins have a read-only name'
        assert self.T.other.name == 'other'
        with assert_raises(AttributeError):
            self.T.other.name = 'notme'

    def test_join_owner(self):
        'Test that joins have a read-only owner'
        assert self.T.other.owner is self.T
        with assert_raises(AttributeError):
            self.T.other.owner = 'notme'


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

    def test_init_single(self):
        'Test initialisation with a single argument.'
        t = self.T(oid=1)
        assert t.oid == 1, t.oid
        assert t.name is NotSet
        assert t.age is NotSet

    def test_init_many(self):
        'Test initialisation with many arguments.'
        t = self.T(oid=1, name='Mike', age=23)
        assert t.oid == 1
        assert t.name is 'Mike'
        assert t.age is 23

    def test_init_bad_kwargs(self):
        'Invalid keywords raise AttributeError.'
        with assert_raises(AttributeError):
            self.T(bad='field')

    def test_init_invalid(self):
        class T(Table):
            v = Field()

            def validate(self):
                assert False

        with assert_raises(ValidationError):
            T(v=1)

    def test_init_defaults(self):
        'Test that defaults are set for default fields'
        class T(Table):
            a = Field(default=1)
            b = Field()
        t = T()
        assert t.a == 1
        assert t.b is NotSet

    def test_setattr(self):
        'Test that fields can be assigned late'
        f = Field()
        self.T.other = f
        t = self.T(other=4)
        assert self.T.other is f
        assert t.other == 4
        assert f.owner is self.T

    def test_name(self):
        'Test that Table.name == "Table"'
        assert self.T.__name__ == 'T'

    def test_repr(self):
        'Test repr(table)'
        t = self.T(oid=4, name='tee', age=23)
        t.age = t   # Test self-reference
        if sys.version >= '3':
            expect = "T(age=..., name='tee', oid=4)"
        else:
            expect = "T(age=..., name=u'tee', oid=4)"
        assert repr(t) == expect, repr(t)

    def test_indexes(self):
        'Test that indexes are created.'
        assert self.T.name.index
        assert self.T.oid.index
        assert hasattr(self.T.name, '_index')
        assert hasattr(self.T.name, '_index')

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
        b = self.T.oid._index._bins
        assert b == (set(), ([1], [t]))

    def test_index_speed(self):
        'Getting indexed fields should be ten times faster'
        assert self.T.oid.index
        assert not self.T.age.index
        count = 1000
        for i in range(count):
            self.T(oid=i, name='Mike', age=int(i % 10))
        number = 100
        fast = timeit.timeit(lambda: list(self.T.oid == 300), number=number)
        slow = timeit.timeit(lambda: list(self.T.age == 5), number=number)
        assert fast * 10 < slow, (fast, slow)

    def test_delete_instance(self):
        'Test deleting a single instance'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete(p1)
        assert p1 not in self.T
        assert p2 in self.T
        assert p3 in self.T
        assert self.T.oid._index._bins == (set(), ([2, 3], [p2, p3]))

    def test_delete_instances(self):
        'Test deleting a list of instances'
        p1 = self.T(oid=1, name='Mike', age=23)
        p2 = self.T(oid=2, name='Mike', age=22)
        p3 = self.T(oid=3, name='Mike', age=23)
        self.T.delete([p1, p2])
        assert p1 not in self.T
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

    def test_field_validate_fails(self):
        'Test when a field validation fails while creating a record.'
        def fail(r):
            assert False

        class T(Table):
            f = Field(validate=[fail])

        with assert_raises(ValidationError):
            T(f=3)


class TestInheritance(object):

    def setup(self):
        class Other(Table):
            f = Field()

        class B(Table):
            a = Field(index=True)
            j = Join(Other.f)

        class I(B):
            b = Field()

        self.B = B
        self.I = I
        self.Other = Other

    def test_fields(self):
        assert set(self.B.fields()) == set(['a'])
        assert set(self.I.fields()) == set(['a', 'b'])

    def test_different_fields(self):
        assert self.B.a is not self.I.a
        assert self.B.a._index is not self.I.a._index

    def test_owner(self):
        assert self.B.a.owner is self.B
        assert self.I.a.owner is self.I

    def test_data(self):
        b = self.B(a=1)
        i = self.I(a=2)
        assert list(self.B.a._data.values()) == [1]
        assert list(self.I.a._data.values()) == [2]

    def test_join(self):
        b = self.B()
        i = self.I()
        o1 = self.Other(f=b)
        o2 = self.Other(f=i)
        assert set(b.j) == set([o1])
        assert set(i.j) == set([o2])


class TestUid(object):

    def setup(self):
        class T(Table): pass
        self.t = T()

    def test_default(self):
        r = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        assert re.match(r, self.t._uid)

    def test_values(self):
        values = ['16fd2706-8baf-433b-82eb-8c7fada847da', 10, id([1])]
        for v in values:
            yield self.check_value, v

    def check_value(self, value):
        self.t._uid = value
        assert self.t._uid == value

    def test_uid_bad_type(self):
        with assert_raises(TypeError):
            self.t._uid = [1, 2, 3]

    def test_uid_bad_int(self):
        with assert_raises(ValueError):
            self.t._uid = 0

    def test_uid_bad_uuid(self):
        with assert_raises(ValueError):
            self.t._uid = '123fe'


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
        assert t1.oid == 1
        assert t2.oid == 2

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
        assert set(self.T) == set([t])
        self.T.delete(t)
        assert set(self.T) == set()

    def test_invalid(self):
        t = self.T(value=0)
        assert set(self.T) == set([t])
        with assert_raises(ValueError):
            self.T.delete(t)
        assert set(self.T) == set([t])

    def test_propogate(self):
        class T(Table):
            value = Field()
            def validate_delete(self):
                if self.value != 3:
                    self.__class__.delete(t3)

        t1 = T(value=1)
        t2 = T(value=2)
        t3 = T(value=3)
        T.delete(t1)
        assert set(T) == set([t2])


class TestHooks:

    def test_validate(self):
        calls = []
        class T(Table):
            value = Field()
            def validate(self):
                calls.append('validate')

        def one(inst):
            assert isinstance(inst, T)
            calls.append('one')

        def two(inst):
            assert isinstance(inst, T)
            calls.append('two')

        T.hooks['validate'] += [one, two]

        t = T(value=4)
        assert calls == ['validate', 'one', 'two']

    def test_validate_delete(self):
        calls = []
        class T(Table):
            value = Field()
            def validate_delete(self):
                calls.append('delete')

        def one(inst):
            assert isinstance(inst, T)
            calls.append('one')

        def two(inst):
            assert isinstance(inst, T)
            calls.append('two')

        T.hooks['delete'] += [one, two]

        t = T(value=4)
        T.delete(t)
        assert calls == ['delete', 'one', 'two'], calls
