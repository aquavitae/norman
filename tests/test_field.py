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

from norman._six import assert_raises
from norman import Database, Field, NotSet, Table, Join, ValidationError


class TestNotSet(object):

    def test_NotSet(self):
        'Test that NotSet cannot be instantiated.'
        with assert_raises(TypeError):
            NotSet()

    def test_NotSet_compare(self):
        'Test that bool(NotSet) is False.'
        assert not NotSet


class TestSingleField(object):

    def setup(self):
        class T(Table):
            a = Field()
        self.T = T

    def test_kwargs(self):
        'Test that kwargs are set'
        f = Field(key=len, default=1, readonly=True)
        assert f.key is len
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
        self.T.a._readonly = True
        with assert_raises(TypeError):
            t.a = 5

    def test_readonly_notset(self):
        'Test that readonly fields can be written to if they are NotSet'
        self.T.a._readonly = True
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
            a = Field()
            b = Field()

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
            number = Field(validators=[float])

        t = T(number=3)
        assert t.number == 3
        t.number = '4'
        assert t.number == 4

    def test_except(self):
        class T(Table):
            number = Field(validators=[float])

        t = T(number=3)
        with assert_raises(TypeError):
            t.number = None
        assert t.number == 3

    def test_chain(self):
        class T(Table):
            a = Field(validators=[float, lambda v: v * 2])
            b = Field(validators=[lambda v: v * 2, float])

        t = T(a=3, b=3)
        assert t.a == 6
        assert t.b == 6
        t.a = '4'
        assert t.a == 8
        t.b = '4'
        assert t.b == 44

    def test_notset(self):
        class T(Table):
            a = Field(validators=[float])

        with assert_raises(TypeError):
            T()

    def test_default(self):
        class T(Table):
            a = Field(default=None, validators=[float])

        with assert_raises(TypeError):
            T()


class TestMutable(object):

    def test_readonly_set(self):
        class T(Table):
            f = Field()
        t1 = T(f=1)
        t2 = T()
        T.f.readonly = True
        # t2 can still be set once
        t2.f = 2
        with assert_raises(ValidationError):
            t1.f = -1
        with assert_raises(ValidationError):
            t2.f = -1

    def test_readonly_unset(self):
        class T(Table):
            f = Field(readonly=True)
        t1 = T()
        T.f.readonly = False
        # t2 can still be set once
        t1.f = -1
        assert t1.f == -1

    def test_unique_set_ok(self):
        class T(Table):
            f = Field()
        t1 = T(f=1)
        T.f.unique = True
        with assert_raises(ValidationError):
            T(f=1)

    def test_unique_set_fail(self):
        class T(Table):
            f = Field()
        t1 = T(f=1)
        t2 = T(f=1)
        with assert_raises(ValidationError):
            T.f.unique = True
        assert T.f.unique == False

    def test_unique_unset(self):
        class T(Table):
            f = Field(unique=True)
        t1 = T(f=1)
        T.f.unique = False
        t2 = T(f=1)
        assert t2.f == 1


class TestCopy(object):

    def test_field(self):
        class T1(Table):
            f = Field(readonly=True, default=4, key=lambda a:a)
        class T2(Table):
            pass
        T2.f = T1.f
        assert T1.f.owner is T1
        assert T2.f.owner is T2
        assert T1.f.name == T2.f.name == 'f'
        assert T2.f.readonly
        assert T2.f.default == 4
        assert T1.f.key == T2.f.key
