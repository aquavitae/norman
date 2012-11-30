# -*- coding: utf-8 -*-
#
# Copyright (c) 2012 David Townshend
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

from norman import NotSet
from norman.store import DefaultStore

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class BaseTestCase(object):

    def setup(self):
        self.f1 = Mock(default=NotSet)
        self.f2 = Mock(default=32)
        self.f3 = Mock(default=NotSet)
        for i in range(5):
            self.store.set(str(i), self.f1, i)
            self.store.set(str(i), self.f2, i)

    def test_add_record(self):
        self.store.add_record('new')
        assert self.store.has_record('new')

    def test_clear(self):
        self.store.clear()
        assert self.store.record_count() == 0

    def test_get(self):
        assert self.store.get('0', self.f1) == 0
        assert self.store.get('1', self.f3) == NotSet

    def test_has_record(self):
        assert self.store.has_record('0')
        assert not self.store.has_record('not a record')

    def test_iter_field_valid(self):
        got = set(self.store.iter_field(self.f1))
        expect = set([(str(i), i) for i in range(5)])
        assert got == expect, got

    def test_iter_field_invalid(self):
        it = self.store.iter_field(self.f3)
        expect = set([(str(i), NotSet) for i in range(5)])
        assert set(it) == expect

    def test_iter_records(self):
        it = self.store.iter_records()
        assert set(it) == set('012324')

    def test_record_count(self):
        assert self.store.record_count() == 5

    def test_remove_record(self):
        self.store.remove_record('3')
        assert set(self.store.iter_records()) == set('0124')

    def test_remove_field(self):
        self.store.remove_field(self.f1)
        it = self.store.iter_field(self.f1)
        expect = set([(str(i), NotSet) for i in range(5)])
        assert set(it) == expect

    def test_set_overwrite(self):
        self.store.set('1', self.f2, 'new value')
        assert self.store.get('1', self.f2) == 'new value'


class TestDefaultStore(BaseTestCase):

    def setup(self):
        self.store = DefaultStore()
        super(TestDefaultStore, self).setup()

