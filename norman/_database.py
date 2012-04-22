#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

import logging
import sqlite3

from ._table import Table
from ._field import NotSet

class Database:
    ''' The main database class containing a list of tables.
    
    Tables are added to the database when they are created by giving
    the class a *database* keyword argument.  For example
    
    >>> db = Database()
    >>> class MyTable(Table, database=db):
    ...     name = Field()
    >>> MyTable in db
    True
    
    The database can be written to a sqlite database as file storage.  So
    if a `Database` instance represents a document state, it can be saved
    using the following code:
    
    >>> db.tosqlite('file.sqlite')
    
    And reloaded thus:
    
    >>> db.fromsqlite('file.sqlite')
    
    :note:
        The sqlite database created does not contain any constraints
        at all (not even type constraints).  This is because the sqlite 
        database is meant to be used purely for file storage.
        
    In the sqlite database, all values are saved as strings (determined
    from ``str(value)``.  Keys (foreign and primary) are globally unique
    integers > 0.  *None* is stored as *NULL*, and *NotSet* as 0.
    
    '''

    def __init__(self):
        self._tables = set()

    def __contains__(self, t):
        return t in self._tables or t in {t.__name__ for t in self._tables}

    def __iter__(self):
        return iter(self._tables)

    def __getitem__(self, name):
        for t in self._tables:
            if t.__name__ == name:
                return t
        raise KeyError(name)

    def add(self, table):
        ''' Add a `Table` class to the database.
        
        This is the same as including the *database* argument in the
        class definition.  The table is returned so this can be used
        as a class decorator.
        
        >>> db = Database()
        >>> @db.add
        ... class MyTable(Table):
        ...     name = Field()
        '''
        self._tables.add(table)
        return table

    def tablenames(self):
        return [t.__name__ for t in self._tables]

    def reset(self):
        ''' Delete all records from all tables. '''
        for table in self._tables:
            table.delete()

    def tosqlite(self, filename):
        ''' Dump the database to a sqlite database.
        
        Each table is dumped to a sqlite table, without any constraints.
        All values in the table are converted to strings and foreign objects
        are stored as an integer id (referring to another record). Each
        record has an additional field, '_oid_', which contains a unique
        integer.
        '''
        conn = sqlite3.connect(filename)
        conn.execute('BEGIN;')
        for table in self:
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
                        value = str(value)
                    values.append(value)
                qmarks = ', '.join('?' * len(values))
                query = 'INSERT INTO "{}" VALUES ({})'.format(tname, qmarks)
                conn.execute(query, values)
        conn.commit()
        conn.close()

    def fromsqlite(self, filename):
        ''' The database supplied is read as follows:
        
        1.  Tables are searched for by name, if they are missing then
            they are ignored.
            
        2.  If a table is found, but does not have an "oid" field, it is
            ignored
        
        3.  Values in "oid" should be unique within the database, e.g.
            a record in "units" cannot have the same "oid" as a record
            in "cycles".
            
        4.  Records which cannot be added, for any reason, are ignored
            and a message logged.
        '''
        conn = sqlite3.connect(filename)
        conn.row_factory = sqlite3.Row
        # Extract the sql to a temporary dict structure, keyed by oid
        flat = {}
        for table in self:
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


    def _makerecord(self, flat, oid):
        ''' Create a new record for oid and return it. '''
        table, row = flat[oid]
        if isinstance(row, table):
            return row
        keys = set(table.fields()) & row.keys()
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
