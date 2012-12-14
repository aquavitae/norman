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

import contextlib
import os
from nose.tools import assert_raises

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from norman import Database, Table, Field, serialise, NotSet, Join
from norman.validate import ifset, settype, istype
from norman._compat import unicode

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
        address = db['Address'].street == 'easy'
        address = address.one()
        assert set(p.name for p in address.people) == set(['matt', 'bob'])
        assert set(p.age for p in address.people) == set([43, 3])


class TestAPI(object):

    class S(serialise.Serialiser):

        def __init__(self, filedata):
            self.filedata = filedata

        def isuid(self, field, value):
            return isinstance(value, int)

        def iter_source(self, source, db):
            return iter(self.filedata)

        @contextlib.contextmanager
        def context(self, targetname, db):
            yield

        def write_record(self, record, db):
            pass

    def teardown(self):
        db.reset()

    def test_isuid(self):
        f = unicode('field')
        v = unicode('a8098c1a-f86e-11da-bd1a-00112444be1e')
        assert serialise.Serialiser.isuid(None, f, v)

    def test_simple(self):
        data = [(Town, 1, {'name': 'A'}),
                (Town, 2, {'name': 'B'}),
                (Town, 3, {'name': 'C'})]
        s = self.S(data)
        s.read('source', db)
        got = set(Town)
        assert len(got) == 3
        assert set((g._uid, g.name) for g in got) == \
               set(((1, 'A'), (2, 'B'), (3, 'C')))

    def test_tree(self):
        data = [(Town, 1, {'name': 'down'}),
                (Town, 2, {'name': 'up'}),
                (Address, 3, {'street': 'easy', 'town': 1}),
                (Address, 4, {'street':'some', 'town': 2}),
                (Person, 5, {'custno': '1', 'name': 'matt', 'age': 43,
                             'address': 3}),
                (Person, 6, {'custno': '2', 'name': 'bob', 'age': 13,
                             'address': 3}),
                (Person, 7, {'custno': '3', 'name': 'peter', 'age': 29,
                             'address': 4})]

        s = self.S(data)
        s.read('source', db)
        assert len(Town) == 2
        assert len(Address) == 2
        assert len(Person) == 3
        t1 = (Town.name == 'down').one()
        t2 = (Town.name == 'up').one()
        a1 = (Address.street == 'easy').one()
        a2 = (Address.street == 'some').one()
        p1 = (Person.name == 'matt').one()
        p2 = (Person.name == 'bob').one()
        p3 = (Person.name == 'peter').one()
        assert a1.town is t1
        assert a2.town is t2
        assert p1.address is a1
        assert p2.address is a1
        assert p3.address is a2

    def test_loop(self):
        data = [(Town, 1, {'name': '1'}),
                (Town, 2, {'name': '2'}),
                (Address, 3, {'street': 4, 'town': 1}),
                (Address, 4, {'street': 3, 'town': 2})]
        s = self.S(data)
        s.read('source', db)
        t1 = (Town.name == '1').one()
        t2 = (Town.name == '2').one()
        a1 = (Address.town == t1).one()
        a2 = (Address.town == t2).one()
        assert a1.street is a2
        assert a2.street is a1


class TestSqlite(TestCase):

    def teardown(self):
        super(TestSqlite, self).teardown()
        try:
            os.unlink('sqltest')
        except OSError:
            pass

    def test_tofromsql(self):
        serialise.Sqlite().write('sqltest', db)
        db.reset()
        serialise.Sqlite().read('sqltest', db)
        self.check_integrity(db)

    def test_bad_sql(self):
        'Should be tolerant of incorrect tables and fields.'
        import logging
        import sqlite3
        logging.disable(logging.CRITICAL)
        sql = """
            CREATE TABLE "other" ("field");
            CREATE TABLE "provinces" ("_uid_", "name", "number");
            CREATE TABLE "units" ("field");
            CREATE TABLE "cycles" ("_uid_", "name");
            INSERT INTO "units" VALUES ('a value');
            INSERT INTO "provinces" VALUES (1, 'Eastern Cape', 42);
            INSERT INTO "cycles" VALUES (2, 'bad value');
            INSERT INTO "cycles" VALUES (3, '2009/10');
        """
        with contextlib.closing(sqlite3.connect('sqltest')) as conn:
            conn.executescript(sql)
        serialise.Sqlite().read('sqltest', db)


class TestCSV(TestCase):

    def teardown(self):
        super(TestCSV, self).teardown()
        try:
            os.unlink('Town')
            os.unlink('Address')
            os.unlink('Person')
        except OSError:
            pass

    def test_tofromsql(self):
        names = dict((t, t.__name__) for t in db)
        serialise.CSV().write(names, db)
        db.reset()
        serialise.CSV().read(names, db)
        self.check_integrity(db)
