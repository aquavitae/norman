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

from dtlibs import core, dev
from dtlibs.mock import assert_raised
from dtlibs.database import Field, NotSet

class MockTable:
    _updateinstance = core.none
    validate = core.none


def test_NotSet():
    'Test that notset cannot be instantiated.'
    with assert_raised(TypeError):
        NotSet()


class TestSingleField:

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
        with assert_raised(TypeError):
            t.a = 5

    def test_readonly_notset(self):
        'Test that readonly fields can be written to if they are NotSet'
        self.T.a.readonly = True
        t = self.T()
        assert t.a is NotSet
        t.a = 4
        assert t.a == 4
        with assert_raised(TypeError):
            t.a = 5

    def test_default(self):
        'Test that default values are used.'
        self.T.a.default = 5
        t = self.T()
        assert t.a == 5
        t.a = 4
        assert t.a == 4
