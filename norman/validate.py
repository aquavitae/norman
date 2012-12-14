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

import datetime

from ._except import ValidationError
from ._field import NotSet


class _Sentinel(object):
    pass
_Sentinel = _Sentinel()


def ifset(func):
    """
    Return a `~norman.Field` validator returning ``func(value)`` if *value*
    is not `~norman.NotSet`.  If *value* is `~norman.NotSet`, then it is
    returned and ``func`` is never called.  This is normally used as a wrapper
    around another validator to permit `~norman.NotSet` values to pass.
    For example::

        >>> validator = ifset(istype(float))
        >>> validator(4.3)
        4.3
        >>> validator(NotSet)
        NotSet
        >>> validator(None)
        Traceback (most recent call last):
            ...
        ValidationError: None
    """
    def inner(value):
        if value is NotSet:
            return value
        else:
            return func(value)
    return inner


def isfalse(func, default=_Sentinel):
    """
    Return a `~norman.Field` validator which passes if *func* returns `False`.

    :param func:     A callable which returns `False` if the value passes.
    :param default:  The value to return if *func* returns `True`.  If this is
                     omitted, a `~norman.ValidationError` is raised.
    """
    def inner(value):
        if not func(value):
            return value
        elif default is _Sentinel:
            raise ValidationError(value)
        else:
            return default
    return inner


def istrue(func, default=_Sentinel):
    """
    Return a `~norman.Field` validator which passes if *func* returns `True`.

    :param func:     A callable which returns `True` if the value passes.
    :param default:  The value to return if *func* returns `False`.  If this is
                     omitted, a `~norman.ValidationError` is raised.
    """
    def inner(value):
        if func(value):
            return value
        elif default is _Sentinel:
            raise ValidationError(value)
        else:
            return default
    return inner


def istype(*t):
    """
    Return a validator which raises a `~norman.ValidationError` on an invalid
    type.

    :param t: The expected type, or types.
    """
    def inner(value):
        if isinstance(value, t):
            return value
        else:
            raise ValidationError(value)
    return inner


def map(mapping):
    """
    Return a validator which maps values to new values.

    :param mapping: A dict mapping old values to new values.

    If a value is passed which has no mapping then it is accepted unchanged.
    For example::

        >>> validator = map({1: 'one', 0: NotSet})
        >>> validator(1)
        'one'
        >>> validator(0)
        NotSet
        >>> validator(2)
        2
    """
    def inner(value):
        return mapping.setdefault(value, value)
    return inner


def settype(t, default):
    """
    Return a `~norman.Field` validator which converts the value to type *t*.

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


def todate(fmt=None):
    """
    Return a validator which converts a string to a `datetime.date`.  If
    *fmt* is omitted, the ISO representation used by `datetime.date.__str__`
    is used, otherwise it should be a format string for
    `datetime.datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *date*
    component is returned.  If it is a `datetime.date` it is returned
    unchanged.

    The return value is always a `datetime.date` object.  If the value
    cannot be converted a `~norman.ValidationError` is raised.
    """
    def inner(value, _fmt=fmt):
        if isinstance(value, datetime.datetime):
            return value.date()
        elif isinstance(value, datetime.date):
            return value
        else:
            if _fmt is None:
                _fmt = '%Y-%m-%d'
            try:
                return datetime.datetime.strptime(value, _fmt).date()
            except ValueError as err:
                raise ValidationError(*err.args)
    return inner


def todatetime(fmt=None):
    """
    Return a validator which converts a string to a `datetime.datetime`.  If
    *fmt* is omitted, the ISO representation used by
    `datetime.datetime.__str__` is used, otherwise it should be a format
    string for `datetime.datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime` it is
    returned unchanged.  If it is a `datetime.date` or `datetime.time`,
    it is converted to a `datetime.datetime`, replacing missing the missing
    information with ``1900-1-1`` or ``00:00:00``.

    The return value is always a `datetime.datetime` object.  If the value
    cannot be converted a `~norman.ValidationError` is raised.
    """
    def inner(value, _fmt=fmt):
        if isinstance(value, datetime.datetime):
            return value
        elif isinstance(value, datetime.date):
            return datetime.datetime.combine(value, datetime.time(0, 0, 0))
        elif isinstance(value, datetime.time):
            return datetime.datetime.combine(datetime.date(1900, 1, 1), value)
        elif _fmt is None:
            date, time = value.split(' ')
            date = todate()(date)
            time = totime()(time)
            return datetime.datetime.combine(date, time)
        else:
            try:
                return datetime.datetime.strptime(value, _fmt)
            except ValueError as err:
                raise ValidationError(*err.args)
    return inner


def totime(fmt=None):
    """
    Return a validator which converts a string to a `datetime.time`.
    If *fmt* is omitted, the ISO representation used by
    `datetime.time.__str__` is used, otherwise it should be a format
    string for `datetime.datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *time*
    component is returned.  If it is a `datetime.time` it is returned
    unchanged.

    The return value is always a `datetime.time` object.  If the value
    cannot be converted a `~norman.ValidationError` is raised.
    """
    def inner(value, _fmt=fmt):
        if isinstance(value, datetime.datetime):
            return value.time()
        elif isinstance(value, datetime.time):
            return value
        else:
            if _fmt is None:
                _fmt = '%H:%M:%S' + ('.%f' if '.' in value else '')
            try:
                return datetime.datetime.strptime(value, _fmt).time()
            except ValueError as err:
                raise ValidationError(*err.args)
    return inner
