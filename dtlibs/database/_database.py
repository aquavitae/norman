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

class Database:
    ''' The main database class containing a list of tables.
    
    Tables are added to the database when they are created by giving
    the class a *database* keyword argument.  For example
    
    >>> db = Database()
    >>> class MyTable(Table, database=db):
    ...     pass
    >>> MyTable in db.tables
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

    def tables(self):
        return iter(self._tables)

    def tablenames(self):
        for t in self._tables:
            yield t.__name__

    def reset(self):
        ''' Delete all records from all tables. '''
        for table in self._tables:
            table.delete()
