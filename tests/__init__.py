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

""" Some system test for the database. """

import pickle
import os

from norman import Database, Table, Field, Join
from norman.validate import settype, istype, ifset

db = Database()


@db.add
class Town(Table):
    name = Field(unique=True)


@db.add
class Person(Table):
    custno = Field(unique=True)
    name = Field()
    age = Field(default=20, validators=[settype(int, 0)])
    address = Field()

    def validate(self):
        assert isinstance(self.address, Address)


@db.add
class Address(Table):
    street = Field(unique=True)
    town = Field(unique=True, validators=[ifset(istype(Town))])
    people = Join(Person.address)


class TestCase1(object):

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
        try:
            os.unlink('test')
        except OSError:
            pass

    def test_links(self):
        assert self.a1.town is self.t1
        assert set(self.a1.people) == set([self.p1, self.p2])

    def test_pickle(self):
        b = pickle.dumps(db)
        db2 = pickle.loads(b)
        self.check_integrity(db)
        self.check_integrity(db2)

    def check_integrity(self, db):
        assert set(db.tablenames()) == set(['Town', 'Address', 'Person'])
        streets = set(a.street for a in db['Address'])
        assert streets == set(['easy', 'some']), streets
        address = db['Address'].street == 'easy'
        address = address.one()
        assert set(p.name for p in address.people) == set(['matt', 'bob'])
        assert set(p.age for p in address.people) == set([43, 3])
