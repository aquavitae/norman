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

from __future__ import with_statement
from __future__ import unicode_literals

import contextlib
import sqlite3
import logging

from ._table import Table
from ._field import NotSet

import sys
if sys.version >= '3':
    unicode = str


class Sqlite3:

    def load(self, db, filename):
        """
        The database supplied is read as follows:

        1.  Tables are searched for by name, if they are missing then
            they are ignored.

        2.  If a table is found, but does not have an "oid" field, it is
            ignored

        3.  Values in "oid" should be unique within the database, e.g.
            a record in "units" cannot have the same "oid" as a record
            in "cycles".

        4.  Records which cannot be added, for any reason, are ignored
            and a message logged.
        """
        with contextlib.closing(sqlite3.connect(filename)) as conn:
            conn.row_factory = sqlite3.Row
            # Extract the sql to a temporary dict structure, keyed by oid
            flat = {}
            for table in db:
                tname = table.__name__
                query = 'SELECT * FROM "{}";'.format(tname)
                try:
                    cursor = conn.execute(query)
                except sqlite3.OperationalError:
                    logging.warning("Table '{}' not found".format(tname))
                else:
                    for row in cursor:
                        row = dict(row)
                        if '_oid_' in row:
                            oid = row.pop('_oid_')
                            flat[oid] = (table, row)

            # Create correct types in flat
            for oid in flat.keys():
                self._makerecord(flat, oid)

    def dump(self, db, filename):
        """
        Dump the database to a sqlite database.

        Each table is dumped to a sqlite table, without any constraints.
        All values in the table are converted to strings and foreign objects
        are stored as an integer id (referring to another record). Each
        record has an additional field, '_oid_', which contains a unique
        integer.
        """
        with contextlib.closing(sqlite3.connect(filename)) as conn:
            conn.execute('BEGIN;')
            for table in db:
                tname = table.__name__
                fstr = ['"{}"'.format(f) for f in table.fields()]
                fstr = '"_oid_", ' + ', '.join(fstr)
                try:
                    conn.execute('DROP TABLE "{}"'.format(tname))
                except sqlite3.OperationalError:
                    pass
                query = 'CREATE TABLE "{}" ({});\n'.format(tname, fstr)
                conn.execute(query)
                for record in table:
                    values = [id(record)]
                    for fname in table.fields():
                        value = getattr(record, fname)
                        if isinstance(value, Table):
                            value = id(value)
                        elif value is NotSet:
                            value = 0
                        elif value is not None:
                            value = unicode(value)
                        values.append(value)
                    qmarks = ', '.join('?' * len(values))
                    query = 'INSERT INTO "{}" VALUES ({})'.format(tname, qmarks)
                    conn.execute(query, values)
            conn.commit()

    def _makerecord(self, flat, oid):
        """
        Create a new record for oid and return it.
        """
        table, row = flat[oid]
        if isinstance(row, table):
            return row
        keys = set(table.fields()) & set(row.keys())
        args = {}
        for key in keys:
            if isinstance(row[key], int):
                if row[key] == 0:
                    args[key] = NotSet
                else:
                    args[key] = self._makerecord(flat, row[key])
            else:
                args[key] = row[key]
        record = None
        try:
            record = table(**args)
        except ValueError as err:
            logging.warning(err)
        else:
            flat[oid] = (table, record)
        return record
