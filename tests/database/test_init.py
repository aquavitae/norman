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

from nose.tools import assert_raises, raises

from dtlibs import dev
from dtlibs.database import Record

###############################################################################
# Some test data

class Parent(Record):

    @classmethod
    def fields(cls):
        return {'name': str,
                'value': float,
                'child': Child}

    @classmethod
    def uniquefields(cls):
        return ['name']

    @classmethod
    def validate(cls, data):
        assert data['value'] > 0
        data['name'] = data['name'].upper()
        return data


class Parent2(Record):

    @classmethod
    def fields(cls):
        return {'name': str,
                'value': float,
                'child': Child}

    @classmethod
    def uniquefields(cls):
        return ['name', 'child']


class Child(Record):

    @classmethod
    def fields(cls):
        return {'name': str,
                'id': int,
                'number': int}

    @classmethod
    def uniquefields(cls):
        return ['name', 'id']

    @classmethod
    def validate(cls, data):
        assert data['number'] is None or data['number'] > 0
        return data


class ListChild(Record):

    @classmethod
    def fields(cls):
        return {'name': str,
                'parent': ListParent}

    @classmethod
    def uniquefields(cls):
        return ['name', 'parent']


class ListParent(Record):

    @classmethod
    def fields(cls):
        return {'name': str}

    @classmethod
    def childfields(cls):
        return {'children': ('parent', records)}

    @classmethod
    def uniquefields(cls):
        return ['name']

records = []

###############################################################################
# Test cases

class TestCase:

    def setup(self):
        global records
        records = []
        Child.clear()
        Parent.clear()
        Parent2.clear()
        ListChild.clear()
        ListParent.clear()

    def teardown(self):
        self.setup()


class TestRecordDefinition(TestCase):

    def test_bad_fields(self):
        'Test for bad field names'
        class R(Record):
            @classmethod
            def fields(cls):
                return {'bad_name': str}
        assert_raises(AttributeError, R)

    def test_instances(self):
        'Test that instances are tracked separately'
        class R1(Record):
            @classmethod
            def fields(cls):
                return {'n': str}
            @classmethod
            def uniquefields(cls):
                return ['n']

        class R2(Record):
            @classmethod
            def fields(cls):
                return {'n': str}
            @classmethod
            def uniquefields(cls):
                return ['n']

        r1 = R1(n='n')
        r2 = R2(n='n')
        assert R1.instances() == {r1}
        assert R2.instances() == {r2}

    def test_all_unique(self):
        'Test a Record that has no unique fields.'
        class R(Record):
            @classmethod
            def fields(cls):
                return {'n': str}
            @classmethod
            def uniquefields(cls):
                return []
        r1 = R(n='a')
        r2 = R(n='b')
        r3 = R(n='a')
        assert r1 is not r2
        assert r2 is not r3
        assert r1.n == 'a'
        assert r2.n == 'b'
        assert r3.n == 'a'


class TestSimpleRecord(TestCase):

    def test_init(self):
        'Test normal initalisation.'
        c = Child(name='name', id=1, number=3)
        assert c.name == 'name'
        assert c.id == 1
        assert c.number == 3

    def test_init_types(self):
        'Test initialisation with incorrect (but convertable) type.'
        c = Child(name='name', id=1, number='3')
        assert c.name == 'name'
        assert c.id == 1
        assert c.number == 3

    def test_init_types_None(self):
        'Test initialisation with None type.'
        c = Child(name='name', id=1, number=None)
        assert c.name == 'name'
        assert c.id == 1
        assert c.number is None

    def test_init_missing(self):
        'Test initialisation with missing fields.'
        c = Child(name='name', id=1)
        assert c.name == 'name'
        assert c.id == 1
        assert c.number is None

    def test_init_invalid(self):
        'Test initialisation with invalid fields.'
        assert_raises(AttributeError, Child, name='name', id=1, value=3)

    def test_init_missing_required(self):
        'Test initialisation with missing required fields.'
        assert_raises(AttributeError, Child, id=1, value=3)

    def test_init_bad_required(self):
        'Test initialisation with None required fields.'
        assert_raises(ValueError, Child, name=None, id=1)

    def test_unique(self):
        'Test that instances are unique on all keys.'
        c1 = Child(name='a', id=1)
        c2 = Child(name='b', id=1)
        c3 = Child(name='b', id=2)
        assert Child.instances() == {c1, c2, c3}, Child.instances()

    def test_validate(self):
        'Test that validate is called and raises ValueError.'
        assert_raises(ValueError, Child, name='name', id=1, number= -1)

    def test_instances_all(self):
        'Test that instances are stored.'
        c = Child(name='name', id=1, number='3')
        assert Child.instances() == {c}

    def test_instances_single(self):
        'Test that instances returns an object based on unique keys'
        c1 = Child(name='name', id=1, number='3')
        inst = Child.instances(name='name')
        assert inst == {c1}

    def test_instances_many(self):
        'Test that all matching instances are returned.'
        c1 = Child(name='name1', id=1, number='3')
        c2 = Child(name='name2', id=2, number='3')
        c3 = Child(name='name3', id=3, number='4')
        inst = Child.instances(number=3)
        assert inst == {c1, c2}, inst

    def test_instances_unique(self):
        'Test instance for only unique keys.'
        c1 = Child(name='name1', id=1)
        c2 = Child(name='name2', id=1)
        i1 = Child.instances(name='name1', id=1)
        i2 = Child.instances(name='name2', id=1)
        assert i1 == {c1}, i1
        assert i2 == {c2}, i2

    def test_setattr(self):
        'Test setting an attribute.'
        c = Child(name='name', id=1, number=3)
        c.number = 4
        assert c.name == 'name'
        assert c.number == 4

    def test_setattr_unique_fails(self):
        'Cannot set a unique field if it already exists.'
        c1 = Child(name='name1', id=1)
        c2 = Child(name='name2', id=1)
        assert_raises(ValueError, setattr, c2, 'name', 'name1')

    def test_setattr_other(self):
        'Setting attribute names starting with "_" works.'
        c = Child(name='name1', id=1)
        c._value = 23
        assert c._value == 23


class TestParent(TestCase):

    def test_init(self):
        'Test normal initalisation.'
        child = Child(name='name', id=1)
        parent = Parent(name='name', value=3, child=child)
        assert parent.name == 'NAME'
        assert parent.value == 3
        assert parent.child is child

    def test_init_child_name(self):
        'Test initialisation with child arguments.'
        child = Child(name='name', id=1)
        parent = Parent(name='name', value=3, child_name='name', child_id=1)
        assert parent.name == 'NAME'
        assert parent.value == 3
        assert parent.child is child

    def test_getattr_child_attribute(self):
        'It is possible to query child attributes using underscore notation.'
        child = Child(name='name', id=1)
        parent = Parent(name='name', value=3, child=child)
        assert parent.child_name == 'name'

    def test_getattr_child_property(self):
        'Child attributes can also be got from properties.'
        class P(Parent):
            @property
            def propchild(self):
                return self.child

        child = Child(name='name', id=1)
        parent = P(name='name', value=3, child=child)
        assert parent.propchild_name == 'name'

    def test_getattr_child_missing_attr(self):
        'Return None on child attributes when child is missing.'
        parent = Parent(name='name', value=3)
        assert parent.child is None
        assert parent.child_name is None

#    def test_setattr_child_attribute(self):
#        'Setting a child attribute changes it in the child.'
#        child = Child(name='name', id=1, number=1)
#        parent = Parent(name='name', value=3, child=child)
#        parent.child_number = 2
#        assert child.number == 2

    def test_setattr_child_unique(self):
        'Setting a unique child field sets a different child'
        c1 = Child(name='name1', id=1)
        c2 = Child(name='name2', id=1)
        parent = Parent(name='name', value=3, child=c1)
        parent.child_name = 'name2'
        assert parent.child is c2

    def test_setattr_bad_type(self):
        'Cannot set the wrong type to Record fields.'
        assert_raises(TypeError, Parent, name='name', value=3, child='c1')

    def test_unique_child(self):
        'Test the case where a unique field is a Record.'
        c = Child(name='name', id=1)
        parent = Parent2(name='name', child_name='name', child_id=1)
        assert parent.child is c

    def test_child_instances(self):
        child = Child(name='name', id=1)
        parent = Parent(name='name', value=3, child=child)
        inst = Parent.instances(child_name='name')
        assert inst == {parent}

class TestLists(TestCase):

    def test_children(self):
        'Test that children work.'
        global records
        p = ListParent(name='p')
        c = ListChild(parent=p, name='c')
        records.append(c)
        assert list(p.children) == [c], p.children

    def test_only_parent(self):
        'Test that children are only listed for the parent.'
        global records
        p1 = ListParent(name='p1')
        p2 = ListParent(name='p2')
        c1 = ListChild(parent=p1, name='c1')
        c2 = ListChild(parent=p2, name='c2')
        records += [c1, c2]
        assert list(p1.children) == [c1]

    def test_underscore(self):
        'Test that underscored names work.'
        global records
        p = ListParent(name='p')
        c = ListChild(parent=p, name='c')
        records.append(c)
        assert p.children_name == ['c']

    def test_setattr(self):
        'Setting child names raises an exception'
        p = ListParent(name='p')
        assert_raises(AttributeError, setattr, p, 'children', [])

    def test_set_underscored_names(self):
        'Setting child underscored names raises and exception'
        p = ListParent(name='p')
        assert_raises(AttributeError, setattr, p, 'children_name', [])
