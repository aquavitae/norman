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
from nose.tools import assert_raises
from norman import Database, Field, NotSet, Table, Join


class MockTable(object):
    _updateinstance = lambda: None
    validate = lambda: None


def test_NotSet():
    'Test that NotSet cannot be instantiated.'
    with assert_raises(TypeError):
        NotSet()

def test_NotSet_compare():
    'Test that bool(NotSet) is False.'
    assert not NotSet


class TestSingleField(object):

    def setup(self):
        class Table(MockTable):
            a = Field()
        self.T = Table

    def test_kwargs(self):
        'Test that kwargs are set'
        f = Field(index=True, default=1, readonly=True)
        assert f.index
        assert f.default == 1
        assert f.readonly

    def test_storage(self):
        'Test that fields store data.'
        t = self.T()
        t.a = 5
        assert t.a == 5

    def test_storage_instances(self):
        'Test storage for many instances.'
        tabs = []
        for i in range(10):
            tabs.append(self.T())
            tabs[-1].a = i * 2
        for i in range(10):
            assert tabs[i].a == i * 2

    def test_readonly(self):
        'Test that readonly fields cannot be written to'
        t = self.T()
        t.a = 4
        self.T.a.readonly = True
        with assert_raises(TypeError):
            t.a = 5

    def test_readonly_notset(self):
        'Test that readonly fields can be written to if they are NotSet'
        self.T.a.readonly = True
        t = self.T()
        assert t.a is NotSet
        t.a = 4
        assert t.a == 4
        with assert_raises(TypeError):
            t.a = 5

    def test_default(self):
        'Test that default values are used.'
        self.T.a.default = 5
        t = self.T()
        assert t.a == 5
        t.a = 4
        assert t.a == 4

class TestComparisons(object):

    def setup(self):
        class T(Table):
            a = Field()
        self.records = [T(a=n) for n in range(5)]
        self.T = T

    def test_eq(self):
        got = self.T.a == 2
        assert got == set(self.records[2:3])

    def test_gt(self):
        got = self.T.a > 2
        assert got == set(self.records[3:])

    def test_lt(self):
        got = self.T.a < 2
        assert got == set(self.records[:2])

    def test_ge(self):
        got = self.T.a >= 2
        assert got == set(self.records[2:])

    def test_le(self):
        got = self.T.a <= 2
        assert got == set(self.records[:3])

    def test_ne(self):
        got = self.T.a != 2
        assert got == set(self.records[:2]) | set(self.records[3:])


class TestJoin(object):

    def test_field(self):
        class Child(Table):
            parent = Field()

        class Parent(Table):
            children = Join(Child.parent)

        p1 = Parent()
        p2 = Parent()
        c1 = Child(parent=p1)
        c2 = Child(parent=p1)
        c3 = Child(parent=p2)
        c4 = Child(parent=p2)
        assert set(p1.children) == set([c1, c2])
        assert set(p2.children) == set([c3, c4])

    def test_name(self):
        db = Database()
        @db.add
        class Parent(Table):
            children = Join(db, 'Child.parent')

        @db.add
        class Child(Table):
            parent = Field()

        p1 = Parent()
        p2 = Parent()
        c1 = Child(parent=p1)
        c2 = Child(parent=p1)
        c3 = Child(parent=p2)
        c4 = Child(parent=p2)
        assert set(p1.children) == set([c1, c2])
        assert set(p2.children) == set([c3, c4])
