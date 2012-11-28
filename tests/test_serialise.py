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

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from norman import Database, Table, Field, tools, serialise, NotSet
from norman._compat import unicode

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
        return set(Person.address == self)

    def validate(self):
        assert isinstance(self.town, (type(NotSet), Town)), self.town


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
        address = db['Address'].street == 'easy'
        address = address.one()
        assert set(p.name for p in address.people) == set(['matt', 'bob'])
        assert set(p.age for p in address.people) == set([43, 3])


class TestAPI:

    class S(serialise.Serialiser):

        def __init__(self, filedata):
            self.filedata = filedata

        def isuid(self, field, value):
            return isinstance(value, int)

        def open(self, filename):
            return

        def close(self):
            return

        def iterfile(self):
            return iter(self.filedata)

    def teardown(self):
        db.reset()

    def test_isuid(self):
        s = serialise.Serialiser(None)
        f = unicode('field')
        v = unicode('a8098c1a-f86e-11da-bd1a-00112444be1e')
        assert s.isuid(f, v)

    def test_simple(self):
        data = [(Town, 1, {'name': 'A'}),
                (Town, 2, {'name': 'B'}),
                (Town, 3, {'name': 'C'})]
        s = self.S(data)
        s.read(None)
        got = set(Town)
        assert len(got) == 3
        assert set((g._uid, g.name) for g in got) == \
               set(((1, 'A'), (2, 'B'), (3, 'C')))

    def test_tree(self):
        data = [(Town, 1, {'name': 'down'}),
                (Town, 2, {'name': 'up'}),
                (Address, 3, {'street': 'easy', 'town': 1}),
                (Address, 4, {'street':'some', 'town': 2}),
                (Person, 5, {'custno': '1', 'name': 'matt', 'age': 43, 'address': 3}),
                (Person, 6, {'custno': '2', 'name': 'bob', 'age': 13, 'address': 3}),
                (Person, 7, {'custno': '3', 'name': 'peter', 'age': 29, 'address': 4})]

        s = self.S(data)
        s.read(None)
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
        s.read(None)
        t1 = (Town.name == '1').one()
        t2 = (Town.name == '2').one()
        a1 = (Address.town == t1).one()
        a2 = (Address.town == t2).one()
        assert a1.street is a2
        assert a2.street is a1


class TestSqlite(TestCase):

    def test_tofromsql(self):
        serialise.Sqlite.dump(db, 'test')
        db.reset()
        serialise.Sqlite.load(db, 'test')
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
        conn = sqlite3.connect('test')
        conn.executescript(sql)
        conn.close()
        serialise.Sqlite.load(db, 'test')

    def test_tosqlite_exception(self):
        'Make sure sqlite3 closes on an exception.'
        with patch.object(Person, 'fields', side_effect=TypeError):
            with assert_raises(TypeError):
                serialise.Sqlite3().dump(db, 'file')
        try:
            os.unlink('file')
        except OSError:
            assert False


class TestCSV(TestCase):

    def setup(self):
        class T(Table):
            name = Field()
            age = Field()
            number = Field()
        self.T = T
        self.expect = ['age,name,number\n', '43,matt,2\n',
                       '3,bob,4\n', '29,peter,-9.32\n']

    def test_init(self):
        for args in [(self.T,), (self.T, db)]:
            s = serialise.CSV(*args)
            assert s.table is self.T
            assert s.db is None

    def test_tocsv(self):
        self.T(name='matt', age=43, number=2)
        self.T(name='bob', age=3, number=4)
        self.T(name='peter', age=29, number= -9.32)
        serialise.CSV.dump(self.T, 'test')
        with open('test', 'rt') as f:
            data = set(l for l in f)
        assert data == set(self.expect), data

    def text_fromcsv(self):
        with open('test', 'wt') as f:
            for l in self.expect:
                f.write(l)
        serialise.CSV.load(self.T, 'test')
        assert len(self.T) == 3
        assert (self.T.name == 'matt' & self.T.age == 43).one().number == 2
        assert (self.T.name == 'bob' & self.T.age == 3).one().number == 4
        assert (self.T.name == 'peter' & self.T.age == 29).one().number == -9.32


class TestSqlite3(TestCase):

    def test_tofromsql(self):
        serialise.Sqlite3().dump(db, 'test')
        db.reset()
        serialise.Sqlite3().load(db, 'test')
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
        serialise.Sqlite3().load(db, 'test')

    def test_tosqlite_exception(self):
        'Make sure sqlite3 closes on an exception.'
        with patch.object(Person, 'fields', side_effect=TypeError):
            with assert_raises(TypeError):
                serialise.Sqlite3().dump(db, 'file')
        try:
            os.unlink('file')
        except OSError:
            assert False
