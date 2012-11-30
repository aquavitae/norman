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


class TestNotSet(object):

    def test_NotSet(self):
        'Test that NotSet cannot be instantiated.'
        with assert_raises(TypeError):
            NotSet()

    def test_NotSet_compare(self):
        'Test that bool(NotSet) is False.'
        assert not NotSet


class TestAutoIndex(object):

    def setup(self):
        self.autoindex = Field.autoindex

    def teardown(self):
        Field.autoindex = self.autoindex

    def check(self, auto, kwargs, expect):
        Field.autoindex = auto
        f = Field(**kwargs)
        assert f.index == expect

    def test_combinations(self):
        c = [[True, {}, True],
             [False, {}, False],
             [True, {'index': False}, False],
             [False, {'index': True}, True],
             [False, {'unique': True, 'index': False}, True]]
        for a, k, e in c:
            yield self.check, a, k, e


class TestSingleField(object):

    def setup(self):
        class T(Table):
            a = Field()
        self.T = T

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


class TestOperations(object):

    def setup(self):
        class T(Table):
            a = Field()
        self.records = [T(a=n) for n in range(5)]
        self.T = T

    def test_eq(self):
        got = set(self.T.a == 2)
        assert got == set(self.records[2:3])

    def test_gt(self):
        got = set(self.T.a > 2)
        assert got == set(self.records[3:])

    def test_lt(self):
        got = set(self.T.a < 2)
        assert got == set(self.records[:2])

    def test_ge(self):
        got = set(self.T.a >= 2)
        assert got == set(self.records[2:])

    def test_le(self):
        got = set(self.T.a <= 2)
        assert got == set(self.records[:3]), got

    def test_ne(self):
        got = set(self.T.a != 2)
        assert got == set(self.records[:2]) | set(self.records[3:])

    def test_and(self):
        got = set(self.T.a & [0, 3])
        assert got == set([self.records[0], self.records[3]])

    def test_indexed_and(self):
        # Test a bug where multiple matches on an indexed field were removed
        class T(Table):
            a = Field(index=True)
            b = Field(index=True)

        r = [T(a=1, b=1), T(a=2, b=2), T(a=3, b=1), T(a=2, b=2)]
        got = set(T.a & [1, 2])
        assert got == set([r[0], r[1], r[3]]), got


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

    def test_query(self):
        class T(Table):
            j = Join(query=lambda v: 'Query')

        t = T()
        assert t.j == 'Query'

    def test_add(self):
        class Child(Table):
            parent = Field()
            id = Field()

        class Parent(Table):
            children = Join(Child.parent)

        p1 = Parent()
        p1.children.add(id=1)
        assert p1.children.one().id == 1

class TestManyJoin(object):

    def setup(self):
        self.db = Database()
        @self.db.add
        class Left(Table):
            rights = Join(self.db, 'Right.lefts')

        @self.db.add
        class Right(Table):
            lefts = Join(self.db, 'Left.rights', jointable='MyJoinTable')

    def test_create_jointable(self):
        jt1 = self.db['Left'].rights.jointable
        jt2 = self.db['Right'].lefts.jointable
        assert jt1 is jt2
        assert issubclass(jt1, Table)
        assert set(jt1.fields()) == set(['Left', 'Right']), set(jt1.fields())
        assert jt1.__name__ == 'MyJoinTable'

    def test_join(self):
        l1 = self.db['Left']()
        l2 = self.db['Left']()
        r1 = self.db['Right']()
        r2 = self.db['Right']()
        assert set(l1.rights) == set()
        assert set(r1.lefts) == set()
        l1.rights.add(r1)
        assert set(l1.rights) == set([r1])
        assert set(r1.lefts) == set([l1])
        jt = self.db['Left'].rights.jointable
        assert len(jt) == 1


class TestValidator(object):

    def test_convert(self):
        class T(Table):
            number = Field(validate=[float])

        t = T(number=3)
        assert t.number == 3
        t.number = '4'
        assert t.number == 4

    def test_except(self):
        class T(Table):
            number = Field(validate=[float])

        t = T(number=3)
        with assert_raises(TypeError):
            t.number = None
        assert t.number == 3

    def test_chain(self):
        class T(Table):
            a = Field(validate=[float, lambda v: v * 2])
            b = Field(validate=[lambda v: v * 2, float])

        t = T(a=3, b=3)
        assert t.a == 6
        assert t.b == 6
        t.a = '4'
        assert t.a == 8
        t.b = '4'
        assert t.b == 44

    def test_notset(self):
        class T(Table):
            a = Field(validate=[float])

        with assert_raises(TypeError):
            t = T()

    def test_default(self):
        class T(Table):
            a = Field(default=None, validate=[float])

        with assert_raises(TypeError):
            t = T()
