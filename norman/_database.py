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
    The main database class containing a list of tables.

    `Database` instances act as containers of `Table` objects, and support
    ``__getitem__``, ``__contains__`` and ``__iter__``.  ``__getitem__``
    returns a table given its name (i.e. its class name), ``__contains__``
    returns whether a `Table` object is managed by the database and
    ``__iter__`` returns a iterator over the tables.

    Tables may be added to the database when they are created by using
    `Database.add` as a class decorator.  For example:

    >>> db = Database()
    >>> @db.add
    ... class MyTable(Table):
    ...     name = Field()
    >>> MyTable in db
    True

    The database can be written to a file through the `serialise` module.
    Currently only sqlite3 is supported.  If a `Database` instance represents
    a document state, it can be saved using the following code:

    .. doctest::
        :options: +SKIP

        >>> serialise.Sqlite3().dump('file.sqlite')

    And reloaded:

    .. doctest::
        :options: +SKIP

        >>> serialise.Sqlite3().load('file.sqlite')

    :note:
        The sqlite database created does not contain any constraints
        at all (not even type constraints).  This is because the sqlite
        database is meant to be used purely for file storage.

    In the sqlite database, all values are saved as strings (determined
    from ``str(value)``.  Keys (foreign and primary) are globally unique
    integers > 0.  `None` is stored as *NULL*, and `NotSet` as 0.
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
        Delete all records from all tables.
        """
        for table in self._tables:
            table.delete()
