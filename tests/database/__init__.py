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

from dtlibs import core
from dtlibs.database import Table, Field

class Person(Table):
    custno = Field(unique=True)
    name = Field(index=True)
    age = Field(default=20)
    address = Field()

    def validate(self):
        if not isinstance(self.age, int):
            self.age = core.int2(self.age, 0)
        assert isinstance(self.address, Address)

class Address(Table):
    street = Field(unique=True)
    town = Field(unique=True)
    people = Field(aggregate=Person.address)

    def validate(self):
        assert isinstance(self.town, Town)

class Town(Table):
    name = Field(unique=True)

def test_indexes():
    'All these indexes should be True'
    assert Person.custno.index
    assert Person.name.index
    assert not Person.age.index
    assert Person.address.index
    assert Address.street.index
    assert Address.town.index
    assert not Address.people.index
    assert Town.name.index
