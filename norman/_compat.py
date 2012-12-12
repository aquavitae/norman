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

"""
Compatibility library, to unify cross-version imports.

This defines the following symbols:

 *  unicode
 *  long
 *  recursive_repr
"""

import sys

if sys.version >= '3':
    unicode = str
    long = int
    from reprlib import recursive_repr
    range = range

else:
    unicode = unicode
    long = long
    range = xrange

    # Copied directly from Python 3.2 reprlib
    from thread import get_ident

    def recursive_repr(fillvalue='...'):
        """
        Decorator to make a repr function return fillvalue for a recursive call
        """

        def decorating_function(user_function):
            repr_running = set()

            def wrapper(self):
                key = id(self), get_ident()
                if key in repr_running:
                    return fillvalue
                repr_running.add(key)
                try:
                    result = user_function(self)
                finally:
                    repr_running.discard(key)
                return result

            # Can't use functools.wraps() here because of bootstrap issues
            wrapper.__module__ = getattr(user_function, '__module__')
            wrapper.__doc__ = getattr(user_function, '__doc__')
            wrapper.__name__ = getattr(user_function, '__name__')
            wrapper.__annotations__ = getattr(user_function,
                                              '__annotations__', {})
            return wrapper

        return decorating_function
