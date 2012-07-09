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

import copy
import random

from nose.tools import assert_raises
from norman import Table, Field, Join, query, tools


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
        func = lambda a: a & set([3, 5])
        q = query(func, self.A.a)
        assert set(q) == set([self.ar[3], self.ar[5]])


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
        assert set(self.A._instances.values()) == set(self.ar[2:])

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
