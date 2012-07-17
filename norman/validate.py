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


class _Sentinel(object):
    pass
_Sentinel = _Sentinel()


def isfalse(func, default=_Sentinel):
    """
    Return a `Field` validator which passes if *func* returns `False`.

    :param func:     A callable which returns `False` if the value passes.
    :param default:  The value to return if *func* returns `True`.  If this is
                     omitted, an exception is raised.
    """
    def inner(value):
        if not func(value):
            return value
        elif default is _Sentinel:
            raise ValueError(value)
        else:
            return default
    return inner


def istrue(func, default=_Sentinel):
    """
    Return a `Field` validator which passes if *func* returns `True`.

    :param func:     A callable which returns `True` if the value passes.
    :param default:  The value to return if *func* returns `False`.  If this is
                     omitted, an exception is raised.
    """
    def inner(value):
        if func(value):
            return value
        elif default is _Sentinel:
            raise ValueError(value)
        else:
            return default
    return inner


def istype(*t):
    """
    Return a `Field` validator which raises an exception on an invalid type.

    :param t: The expected type, or types.
    """
    def inner(value):
        if isinstance(value, t):
            return value
        else:
            raise TypeError(value)
    return inner


def settype(t, default):
    """
    Return a `Field` validator which converts the value to a type

    :param t:       The required type.
    :param default: If the value cannot be converted, then use this value
                    instead.
    """
    def inner(value):
        try:
            return t(value)
        except TypeError:
            return default
    return inner
