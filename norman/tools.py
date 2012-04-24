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


def float2(s, default=0.0):
    """
    Convert *s* to a float, returning *default* if it cannot be converted.

    >>> float2('33.4', 42.5)
    33.4
    >>> float2('cannot convert this', 42.5)
    42.5
    >>> float2(None, 0)
    0
    >>> print(float2('default does not have to be a float', None))
    None
    """
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def int2(s, default=0):
    """
    Convert *s* to an int, returning *default* if it cannot be converted.

    >>> int2('33', 42)
    33
    >>> int2('cannot convert this', 42)
    42
    >>> print(int2('default does not have to be an int', None))
    None
    """
    try:
        return int(s)
    except (ValueError, TypeError):
        return default
