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

"""
**Norman** provides a framework for creating database-like structures.
It doesn't, however, link into any database API (e.g. sqlite) and
doesn't support SQL syntax.  It is intended to be used as a lightweight,
in-memory framework allowing complex data structures, but without
the restrictions imposed by formal databases.  It should not be seen as
in any way as a replacement for, e.g., sqlite or postgreSQL, since it
services a different requirement.

One of the main distinctions between this framework and a SQL database is
in the way relationships are managed.  In a SQL database, each record
has one or more primary keys, which are typically referred to in other,
related tables by foreign keys.  Here, however, keys do not exist, and
records are linked directly to each other as attributes.

The main containing class is `Database`, and an instance of this should be
created before creating any tables it contains.  Tables are subclassed
from the `Table` class and fields added to it by creating `Field` class
attributes.
"""

__version__ = '0.6.1'
__author__ = 'David Townshend'

from ._table import Table
from ._field import Field, Join, NotSet
from ._query import query
from ._group import Group
from ._database import Database
