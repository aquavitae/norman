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

from nose.tools import assert_raises
from norman import Table, Field, Join, query
from norman._query import _Adder


class TestCase(object):

    def setup(self):
        class A(Table):
            a = Field()
            b = Field()
            c = Field()

        class B(Table):
            d = Field()
            e = Field()
            a = Join(A.b)

        self.A = A
        self.B = B
        self.br = [
            B(d=1, e='a'),
            B(d=2, e='b'),
            B(d=1, e='c'),
        ]
        self.ar = [
            A(a=1, b=self.br[0], c='a'),
            A(a=1, b=self.br[1], c='b'),
            A(a=2, b=self.br[0], c='b'),
            A(a=3, b=self.br[2], c='z'),
            A(a=4, b=self.br[2], c='y'),
            A(a=5, b=self.br[2], c='x')
        ]


class TestExamples(TestCase):

    def test_filter_one_field(self):
        query = self.A.a == 1
        assert set(query) == set(self.ar[:2])

    def test_filter_multiple_fields(self):
        query = (self.A.a < 2) & (self.A.c == 'b')
        assert set(query) == set([self.ar[1]])

    def test_custom_function(self):
        func = lambda a: a.a in [3, 5]
        q = query(func, self.A)
        assert set(q) == set([self.ar[3], self.ar[5]])


class TestQueryFunc(TestCase):

    def test(self):
        def f(record):
            return record.c in 'bx'
        q = query(f, self.A)
        got = set(q)
        expect = set([self.ar[1], self.ar[2], self.ar[5]])
        assert got == expect


class TestQuery(TestCase):

    def setup(self):
        super(TestQuery, self).setup()
        self.query = self.A.a == 1
        self.query._results = [self.ar[0], self.ar[1]]

    def test_type(self):
        from norman._query import Query
        assert isinstance(self.query, Query)

    def test_in(self):
        assert self.ar[0] in self.query

    def test_not_in(self):
        assert self.ar[5] not in self.query

    def test_len(self):
        assert len(self.query) == 2

    def test_iter(self):
        assert set(iter(self.query)) == set(self.ar[:2])

    def test_and(self):
        q2 = self.A.c == 'b'
        expect = set([self.ar[1]])
        got = set(self.query & q2)
        assert got == expect, (got, expect)

    def test_or(self):
        q2 = self.A.c == 'b'
        expect = set(self.ar[:3])
        got = set(self.query | q2)
        assert got == expect, (got, expect)

    def test_xor(self):
        q2 = self.A.c == 'b'
        expect = set([self.ar[0], self.ar[2]])
        assert set(self.query ^ q2) == expect

    def test_sub(self):
        q2 = self.A.c == 'b'
        expect = set([self.ar[0]])
        assert set(self.query - q2) == expect

    def test_delete(self):
        self.query.delete()
        assert set(self.A) == set(self.ar[2:])

    def test_one_success(self):
        result = self.query.one()
        assert result in self.ar[:1]

    def test_one_fails_return(self):
        q = self.A.a == -100
        result = q.one(5)
        assert result == 5

    def test_one_fails_exception(self):
        q = self.A.a == -100
        with assert_raises(IndexError):
            q.one()

    def test_bool_true(self):
        q = self.A.a == 1
        assert bool(q) is True

    def test_bool_false(self):
        q = self.A.a == -100
        assert bool(q) is False

    def test_add_single(self):
        q = self.A.a == 1
        a = q.add(c='5')
        assert isinstance(a, self.A)
        assert a.a == 1
        assert a.c == '5'

    def test_add_query(self):
        'Test that add is available for table queries.'
        q = query(self.A)
        r = q.add(a=10)
        assert r.a == 10

    def test_add_and(self):
        q = (self.A.a == 1) & (self.A.c == '5')
        assert len(q) == 0
        a = q.add()
        assert isinstance(a, self.A)
        assert a.a == 1
        assert a.c == '5'
        assert len(q) == 1

    def test_add_field(self):
        q = (self.A.a == 1).field('b')
        a = q.add(self.br[2], c='c')
        assert isinstance(a, self.A)
        assert a.a == 1
        assert a.b is self.br[2]
        assert a.c == 'c'

    def test_add_field2_fails(self):
        q = (self.A.a == 1).field('b').field('e')
        with assert_raises(TypeError):
            q.add(self.br[0])

    def test_field(self):
        q1 = self.A.a >= 2
        q2 = q1.field('b')
        assert set(q2) == set([self.br[0], self.br[2]])

    def test_field_join(self):
        q1 = self.B.d == 1
        q2 = q1.field('a')
        assert set(q2) == set([self.ar[0]] + self.ar[2:])

    def test_call_return(self):
        q = self.A.a == 1
        assert len(q) == 2
        self.A(a=1)
        assert len(q) == 2
        q2 = q()
        assert q2 is q
        assert len(q2) == 3

    def test_str1(self):
        q = self.A.a == 1
        assert str(q) == 'A.a == 1', str(q)

    def test_str2(self):
        q = (self.A.a >= 1) | ((self.A.b != 4) & (self.A.c & [1, 2, 3]))
        expect = '(A.a >= 1) | ((A.b != 4) & (A.c & [1, 2, 3]))'
        assert str(q) == expect, str(q)


class TestAdder(TestCase):

    def test_settable(self):
        a = _Adder()
        assert a.table is None
        a.set_table(None)
        assert a.table is None
        a.set_table(self.A)
        assert a.table is self.A
        a.set_table(self.B)
        assert a.table is False, a.table
        a.set_table(self.A)
        assert a.table is False, a.table

class TestQueryTable(TestCase):

    def setup(self):
        super(TestQueryTable, self).setup()
        self.q1 = self.A.a == 1
        self.q2 = self.B.a == self.ar[1]

    def test_single(self):
        assert self.q1.table is self.A

    def test_inequality(self):
        assert (self.A.a > 3).table is self.A

    def test_combination(self):
        q = self.q1 & (self.A.b < 2)
        assert q.table is self.A

    def test_field_query(self):
        q = (self.B.d == 1).field('a')
        assert q.table is None

    def test_multiple_no_table(self):
        q = (self.A.a == 1) & (self.B.d == 2)
        assert q.table is None
