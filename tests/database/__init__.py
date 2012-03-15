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

''' Some system test for the database. '''

import pickle

from dtlibs import core
from dtlibs.database import Database, Table, Field

db = Database()

class Person(Table, database=db):
    custno = Field(unique=True)
    name = Field(index=True)
    age = Field(default=20)
    address = Field(index=True)

    def validate(self):
        if not isinstance(self.age, int):
            self.age = core.int2(self.age, 0)
        assert isinstance(self.address, Address)

class Address(Table, database=db):
    street = Field(unique=True)
    town = Field(unique=True)

    @property
    def people(self):
        return Person.get(address=self)

    def validate(self):
        assert isinstance(self.town, Town)

class Town(Table, database=db):
    name = Field(unique=True)

def test_indexes():
    'All these indexes should be True'
    assert Person.custno.index
    assert Person.name.index
    assert not Person.age.index
    assert Person.address.index
    assert Address.street.index
    assert Address.town.index
    assert Town.name.index

class TestCase1:

    def setup(self):
        self.t1 = Town(name='down')
        self.t2 = Town(name='up')
        self.a1 = Address(street='easy', town=self.t1)
        self.a2 = Address(street='some', town=self.t2)
        self.p1 = Person(custno=1, name='matt', age=43, address=self.a1)
        self.p2 = Person(custno=2, name='bob', age=3, address=self.a1)
        self.p3 = Person(custno=3, name='peter', age=29, address=self.a2)

    def teardown(self):
        db.reset()

    def test_links(self):
        assert self.a1.town is self.t1
        assert set(self.a1.people) == {self.p1, self.p2}

    def test_pickle(self):
        b = pickle.dumps(db)
        db2 = pickle.loads(b)
        assert set(db2.tablenames()) == {'Town', 'Address', 'Person'}
        assert set(a.street for a in db['Address']) == {'easy', 'some'}
        address = next(db['Address'].get(street='easy'))
        assert set(p.name for p in address.people) == {'matt', 'bob'}
        assert set(p.age for p in address.people) == {43, 3}
