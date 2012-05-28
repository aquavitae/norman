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

from __future__ import with_statement
from __future__ import unicode_literals

import os
from nose.tools import assert_raises
from mock import patch

from norman import Database, Table, Field, tools, serialize

db = Database()


@db.add
class Person(Table):
    custno = Field(unique=True)
    name = Field(index=True)
    age = Field(default=20)
    address = Field(index=True)

    def validate(self):
        if not isinstance(self.age, int):
            self.age = tools.int2(self.age, 0)
        assert isinstance(self.address, Address)


@db.add
class Address(Table):
    street = Field(unique=True)
    town = Field(unique=True)

    @property
    def people(self):
        return Person.get(address=self)

    def validate(self):
        assert isinstance(self.town, Town)


@db.add
class Town(Table):
    name = Field(unique=True)


class TestCase(object):

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

    def check_integrity(self, db):
        assert set(db.tablenames()) == set(['Town', 'Address', 'Person'])
        streets = set(a.street for a in db['Address'])
        assert streets == set(['easy', 'some']), streets
        address = next(db['Address'].iter(street='easy'))
        assert set(p.name for p in address.people) == set(['matt', 'bob'])
        assert set(p.age for p in address.people) == set([43, 3])


class TestSqlite3(TestCase):

    def test_tofromsql(self):
        serialize.Sqlite3().dump(db, 'test')
        db.reset()
        serialize.Sqlite3().load(db, 'test')
        self.check_integrity(db)

    def test_bad_sql(self):
        'Should be tolerant of incorrect tables and fields.'
        import logging
        import sqlite3
        logging.disable(logging.CRITICAL)
        sql = """
            CREATE TABLE "other" ("field");
            CREATE TABLE "provinces" ("oid", "name", "number");
            CREATE TABLE "units" ("field");
            CREATE TABLE "cycles" ("oid", "name");
            INSERT INTO "units" VALUES ('a value');
            INSERT INTO "provinces" VALUES (1, 'Eastern Cape', 42);
            INSERT INTO "cycles" VALUES (2, 'bad value');
            INSERT INTO "cycles" VALUES (3, '2009/10');
        """
        conn = sqlite3.connect('test')
        conn.executescript(sql)
        conn.close()
        serialize.Sqlite3().load(db, 'test')

    def test_tosqlite_exception(self):
        'Make sure sqlite3 closes on an exception.'
        with patch.object(Person, 'fields', side_effect=TypeError):
            with assert_raises(TypeError):
                serialize.Sqlite3().dump(db, 'file')
        try:
            os.unlink('file')
        except OSError:
            assert False
