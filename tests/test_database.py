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

from nose.tools import assert_raises
from norman import Database, Table

class TestDatabase:

    def setup(self):
        self.db = Database()
        class T(Table, database=self.db):
            pass
        self.T = T

    def test_contains_table(self):
        assert self.T in self.db

    def test_contains_name(self):
        assert 'T' in self.db

    def test_getitem(self):
        assert self.db['T'] is self.T

    def test_getitem_raises(self):
        with assert_raises(KeyError):
            self.db['not a table']

    def test_setitem_raises(self):
        'Cannot set a table.'
        with assert_raises(TypeError):
            self.db['key'] = 'value'

    def test_tablenames(self):
        assert set(self.db.tablenames()) == {'T'}

    def test_iter(self):
        assert set(iter(self.db)) == {self.T}
