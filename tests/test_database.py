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

import warnings
from nose.tools import assert_raises
from norman import AutoDatabase, AutoTable, Database, Table, Field, NormanWarning


class TestDatabase(object):

    def setup(self):
        self.db = Database()

        @self.db.add
        class T(Table):
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
        assert set(self.db.tablenames()) == set(['T'])

    def test_iter(self):
        assert set(iter(self.db)) == set([self.T])

    def test_add(self):
        class Tb(Table):
            pass
        r = self.db.add(Tb)
        assert r is Tb
        assert Tb in self.db

    def test_reset_blocked(self):
        'Reset should work even if validate_delete fails'
        class Tb(Table):
            def validate_delete(self):
                raise ValueError
        self.db.add(Tb)
        tb = Tb()
        with assert_raises(ValueError):
            Tb.delete(tb)
        assert tb in Tb
        self.db.reset()
        assert len(Tb) == 0

    def test_reset_field(self):
        'Reset should keep fields'
        class Tb(Table):
            f = Field()
        self.db.add(Tb)
        self.db.reset()
        assert Tb.f.name in Tb.fields()

    def test_delete(self):
        class Tb(Table):
            pass
        self.db.add(Tb)
        t = Tb()
        self.db.delete(t)
        assert len(Tb) == 0

    def test_delete_warn(self):
        class Tb(Table):
            pass
        t = Tb()
        with warnings.catch_warnings(record=True) as w:
            self.db.delete(t)
        assert w[0].category is NormanWarning


class TestAutoDatabase(object):

    def test_getitem(self):
        db = AutoDatabase()
        T = db['MyTable']
        assert issubclass(T, AutoTable)
