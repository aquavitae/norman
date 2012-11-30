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

from __future__ import with_statement
from __future__ import unicode_literals


class Database(object):

    """
    `Database` instances act as containers of `Table` objects, and support a
    basic dict-like interface.  Tables are identified by their name, which is
    obtained by ``table.__name__``.

    In addition to the methods described below, database support the following
    operations.

    =================== =======================================================
    Operation           Description
    =================== =======================================================
    ``db[name]``        Return a `Table` by name
    ``name in db``      Return `True` if a `Table` named *name* is in the
                        database.
    ``table in db``     Return `True` if a `Table` object is in the database.
    ``iter(db)``        Return an iterator over `Table` objects in the
                        database.
    =================== =======================================================

    Tables are not required to belong to a database, or may belong to many
    databases.
    """

    def __init__(self):
        self._tables = set()

    def __contains__(self, t):
        return t in self._tables or t in set(t.__name__ for t in self._tables)

    def __iter__(self):
        return iter(self._tables)

    def __getitem__(self, name):
        for t in self._tables:
            if t.__name__ == name:
                return t
        raise KeyError(name)

    def add(self, table):
        """
        Add a `Table` class to the database.

        This is the same as including the *database* argument in the
        class definition.  The table is returned so this can be used
        as a class decorator.

        >>> db = Database()
        >>> @db.add
        ... class MyTable(Table):
        ...     name = Field()
        """
        self._tables.add(table)
        return table

    def tablenames(self):
        """
        Return an list of the names of all tables managed by the database.
        """
        return [t.__name__ for t in self._tables]

    def reset(self):
        """
        Delete all records from all tables in the database.
        """
        for table in self._tables:
            table._store.clear()
            for field in table._fields.values():
                if field.index:
                    field._index.clear()


    # TODO: delete(record)
