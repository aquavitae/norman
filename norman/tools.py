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

import datetime
import re


def dtfromiso(iso):
    """
    Return a `datetime` object from a string representation in ISO format.

    The database serialisation procedures store `datetime` objects as strings,
    in ISO format.  This provides an easy way to reverse this.
    `~datetime.datetime`, `~datetime.date` and `~datetime.time` objects are
    all supported.

    Note that this assumes naive datetimes.

    .. doctest:: tools

        >>> import datetime
        >>> dt = datetime.date(2001, 12, 23)
        >>> isodt = str(dt)
        >>> dtfromiso(isodt)
        datetime.date(2001, 12, 23)
    """
    date = None
    time = None
    exp = ('((?P<Y>\d\d\d\d)-(?P<m>\d\d)-(?P<d>\d\d))? ?' +
           '((?P<H>\d\d):(?P<M>\d\d):(?P<s>\d\d)(\.(?P<f>\d{1,6}))?)?')
    m = re.match(exp, iso).groupdict()
    for k in m:
        m[k] = int2(m[k], None)
    m['f'] = int2(m['f'], 0)
    if m['Y'] is not None:
        date = datetime.date(m['Y'], m['m'], m['d'])
    if m['H'] is not None:
        time = datetime.time(m['H'], m['M'], m['s'], m['f'])
    if date is None and time is None:
        raise ValueError("Invalid datetime: '{}'".format(iso))
    elif date is None:
        return time
    elif time is None:
        return date
    else:
        return datetime.datetime.combine(date, time)


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


def reduce2(func, seq, default):
    """
    Similar to `functools.reduce`, but return *default* if *seq* is empty.

    The third argument to `functools.reduce` is an *initializer*, which
    essentially acts as the first item in *seq*.  In this function,
    *default* is returned if *seq* is empty, otherwise it is ignored.

        >>> reduce2(lambda a, b: a + b, [1, 2, 3], 4)
        6
        >>> reduce2(lambda a, b: a + b, [], 'default')
        'default'
    """
    it = iter(seq)
    try:
        value = next(it)
    except StopIteration:
        return default
    while True:
        try:
            v = next(it)
        except StopIteration:
            return value
        value = func(value, v)
