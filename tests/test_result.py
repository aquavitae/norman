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
from norman import Table, Field
from norman._result import _Result


class TestOperations(object):

    def setup(self):
        class T(Table):
            f = Field()
        self.T = T
        self.records = [T(f=r) for r in range(10)]
        self.result = _Result(T, self.records)

    def test_in(self):
        assert self.records[5] in self.result

    def test_not_in(self):
        assert self.T(f=15) not in self.result

    def test_len(self):
        assert len(self.result) == 10

    def test_iter(self):
        assert list(iter(self.result)) == self.records

    def test_eq(self):
        assert self.result == _Result(self.T, self.records)

    def test_not_eq_results(self):
        assert self.result != _Result(self.T, self.records[:8])

    def test_not_eq_type(self):
        assert self.result != set(self.records)

    def test_not_eq_order(self):
        records = copy.copy(self.records)
        random.shuffle(records)
        shuffled = _Result(self.T, records)
        assert self.result != shuffled

    def test_and(self):
        b = self.records[5:] + [self.T(f=11), self.T(f=12)]
        expect = set(self.records[5:])
        got = set(self.result & b)
        assert got == expect, (got, expect)

    def test_or(self):
        a = [self.T(f=11), self.T(f=12)]
        b = self.records[5:] + a
        expect = set(self.records + a)
        got = set(self.result | b)
        assert got == expect, (got, expect)

    def test_xor(self):
        a = [self.T(f=11), self.T(f=12)]
        b = self.records[5:] + a
        expect = set(self.records[:5] + a)
        assert set(self.result ^ b) == expect

    def test_sub(self):
        a = [self.T(f=11), self.T(f=12)]
        b = self.records[5:] + a
        expect = set(self.records[:5])
        assert set(self.result - b) == expect

    def test_field(self):
        assert self.result.field('f') == list(range(10))

    def test_one(self):
        assert self.result.one() == self.records[0]

    def test_sort(self):
        records = copy.copy(self.records)
        random.shuffle(records)
        result = _Result(self.T, records)
        got = result.sort('f')
        assert got == self.result

    def test_sort_reverse(self):
        records = copy.copy(self.records)
        random.shuffle(records)
        result = _Result(self.T, records)
        got = result.sort('f', reverse=True)
        expect = _Result(self.T, list(reversed(self.records)))
        assert got == expect, (got, expect)
