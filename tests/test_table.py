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

import re
from nose.tools import assert_raises
from norman import Table, Field, NotSet, Join, ValidationError


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
            oid = Field()
            name = Field()
            age = Field()
        self.T = T

    def test_init_empty(self):
        'Test initialisation with no arguments.'
        t = self.T()
        assert t.oid is NotSet
        assert t.name is NotSet
        assert t.age is NotSet
        assert t in self.T

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
        expect = "T(age=..., name='tee', oid=4)"
        assert repr(t) == expect, repr(t)

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
        assert t2 in self.T

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

    def test_delete_all(self):
        'Test that delete with no args clears all instances.'
        self.T(oid=1, name='Mike', age=23)
        self.T(oid=2, name='Mike', age=22)
        self.T(oid=3, name='Mike', age=23)
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
            f = Field(validators=[fail])

        with assert_raises(ValidationError):
            T(f=3)


class TestInheritance(object):

    def setup(self):
        class Other(Table):
            f = Field()

        class B(Table):
            a = Field()
            j = Join(Other.f)

        class I(B):
            b = Field()

        self.B = B
        self.I = I
        self.Other = Other

    def test_store(self):
        assert self.B._store is not self.I._store

    def test_fields(self):
        assert set(self.B.fields()) == set(['a'])
        assert set(self.I.fields()) == set(['a', 'b'])

    def test_different_fields(self):
        assert self.B.a is not self.I.a

    def test_owner(self):
        assert self.B.a.owner is self.B
        assert self.I.a.owner is self.I

    def test_join(self):
        b = self.B()
        i = self.I()
        o1 = self.Other(f=b)
        o2 = self.Other(f=i)
        assert set(b.j) == set([o1])
        assert set(i.j) == set([o2])


class TestUid(object):

    def setup(self):

        class T(Table):
            pass

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

    def test_unique_init(self):
        'Test the initialisation of a duplicate record.'
        self.T(oid=3)
        with assert_raises(ValueError):
            self.T(oid=3)

    def test_unique_set(self):
        'Test setting a record to a duplicate value.'
        t1 = self.T(oid=1)
        t2 = self.T(oid=2)
        with assert_raises(ValueError):
            t2.oid = 1
        assert t1.oid == 1
        assert t2.oid == 2, t2.oid

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

    def test_validation(self):
        'Test changing to a unique value during validation'
        class T(Table):
            a = Field(unique=True)
            b = Field()

            def validate(self):
                self.a = self.b

        t1 = T(b=1)
        t2 = T(b=2)
        assert t1.a == 1
        assert t2.a == 2
        with assert_raises(ValidationError):
            t2.b = 1


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

        dummy = T(value=4)
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
