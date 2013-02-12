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

import warnings

from ._table import AutoTable
from ._except import NormanWarning


class Database(object):

    """
    `Database` instances act as containers of `Table` objects, which are
    identified by name.  `Database` supports the following operations.

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

    Databases are mainly provided for convenience, as a way to group
    related tables.  Tables may beloong to multiple databases, or no database
    at all.
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

    def delete(self, record):
        """
        Delete a record from the database.  This is a convenience function
        which simply calls record.__class__.delete(record), but also
        checks that the record does actually belong to the database.  If not,
        a `NormanWarning` is raised, and the record is still deleted.
        """
        table = record.__class__
        if table not in self:
            warnings.warn('Record does not belong to database', NormanWarning)
        table.delete(record)


class AutoDatabase(Database):

    """
    A subclass of `Database` which automatically creates `AutoTable`
    subclasses when a table is looked up by name.  For example::

        >>> adb = AutoDatabase()
        >>> newtable = adb['NewTable']
        >>> issubclass(newtable, AutoTable)
        True

    Apart from this, it behaves exactly the same as `Database`.
    """

    def __getitem__(self, name):
        try:
            return super(AutoDatabase, self).__getitem__(name)
        except KeyError:
            class C(AutoTable): pass
            C.__name__ = name
            self.add(C)
            return C
