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

__version__ = '0.7.2'
__author__ = 'David Townshend'

from ._table import AutoTable, Table
from ._field import Field, Join, NotSet
from ._query import query, Query
from ._database import AutoDatabase, Database
from ._except import (NormanWarning,
                      NormanError,
                      ConsistencyError,
                      ValidationError)
from ._store import Store, Index
