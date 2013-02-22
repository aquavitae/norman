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

from norman._six import assert_raises
import datetime

from norman import validate, NotSet


class Test_ifset(object):

    """
    Return ``func(value)`` if *value* is not `NotSet`, otherwise return
    `NotSet`.  This is normally used as a wrapper around another validator
    to permit `NotSet` values to pass.
    """

    def test(self):
        v = validate.ifset(lambda v:-v)
        assert v(NotSet) == NotSet
        assert v(4) == -4
        with assert_raises(TypeError):
            v(None)


class Test_isfalse(object):

    """
    Return a `Field` validator which passes if *func* returns `False`.

    :param func:     A callable which returns `False` if the value passes.
    :param default:  The value to return if *func* returns `True`.  If this is
                     omitted, an exception is raised.
    """

    def test_pass(self):
        v = validate.isfalse(lambda v: False)
        assert v(4) == 4

    def test_fail_default(self):
        v = validate.isfalse(lambda v: True, 2)
        assert v(4) == 2

    def test_fail_except(self):
        v = validate.isfalse(lambda v: True)
        with assert_raises(ValueError):
            v(4)


class Test_istrue(object):

    """
    Return a `Field` validator which passes if *func* returns `True`.

    :param func:     A callable which returns `True` if the value passes.
    :param default:  The value to return if *func* returns `False`.  If this is
                     omitted, an exception is raised.
    """

    def test_pass(self):
        v = validate.istrue(lambda v: True)
        assert v(4) == 4

    def test_fail_default(self):
        v = validate.istrue(lambda v: False, 2)
        assert v(4) == 2

    def test_fail_except(self):
        v = validate.istrue(lambda v: False)
        with assert_raises(ValueError):
            v(4)


class Test_istype(object):

    """
    Return a `Field` validator which raises an exception on an invalid type.

    :param t: The expected type, or types.
    """

    def test_single_pass(self):
        v = validate.istype(float)
        assert v(4.0) == 4.0

    def test_multi_pass(self):
        v = validate.istype(int, float)
        assert v(4) == 4
        assert v(3.2) == 3.2

    def test_fail(self):
        v = validate.istype(float)
        with assert_raises(TypeError):
            v('4')


class Test_map(object):

    def test_passing(self):
        v = validate.map({1: 'one', 0: NotSet})
        assert v(1) == 'one'

    def test_notset(self):
        v = validate.map({1: 'one', 0: NotSet})
        assert v(0) is NotSet

    def test_missing(self):
        v = validate.map({1: 'one', 0: NotSet})
        assert v(2) == 2


class Test_settype(object):

    """
    Return a `Field` validator which converts the value to a type

    :param t:       The required type.
    :param default: If the value cannot be converted, then use this value
                    instead.
    """

    def test_pass(self):
        v = validate.settype(float, 1.1)
        assert v('3') == 3.0

    def test_fail(self):
        v = validate.settype(float, 1.1)
        assert v(None) == 1.1


class Test_todate(object):

    """
    Return a validator which converts a string to a `datetime.date`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.date.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *date*
    component is returned.  If it is a `datetime.date` it is returned
    unchanged.

    The return value is always a `datetime.date` object.  If the value
    cannot be converted an exception is raised.
    """

    def test_date(self):
        v = validate.todate()
        d = datetime.date(2013, 12, 23)
        assert v(d) == d

    def test_datetime(self):
        v = validate.todate()
        d = datetime.datetime(2013, 12, 23, 12, 23, 34)
        assert v(d) == d.date()

    def test_iso(self):
        v = validate.todate()
        d = datetime.date(2013, 12, 23)
        assert v('2013-12-23') == d

    def test_fmt(self):
        v = validate.todate('%d/%m/%y')
        d = datetime.date(2013, 12, 23)
        assert v('23/12/13') == d


class Test_todatetime(object):

    """
    Return a validator which converts a string to a `datetime.datetime`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.datetime.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime` it is
    returned unchanged.  If it is a `datetime.date` or `datetime.time`,
    it is converted to a `datetime.datetime`, replacing missing the missing
    information with ``1900-1-1`` or ``00:00:00``.

    The return value is always a `datetime.datetime` object.  If the value
    cannot be converted an exception is raised.
    """

    def test_datetime(self):
        v = validate.todatetime()
        d = datetime.datetime(2013, 12, 23, 12, 23, 34)
        assert v(d) == d

    def test_date(self):
        v = validate.todatetime()
        d = datetime.date(2013, 12, 23)
        assert v(d) == datetime.datetime(2013, 12, 23, 0, 0, 0)

    def test_time(self):
        v = validate.todatetime()
        d = datetime.time(12, 23, 34)
        assert v(d) == datetime.datetime(1900, 1, 1, 12, 23, 34)

    def test_iso(self):
        v = validate.todatetime()
        d = datetime.datetime(2013, 12, 23, 12, 23, 34, 567000)
        assert v('2013-12-23 12:23:34.567') == d

    def test_fmt(self):
        v = validate.todatetime('%H, %M, %S - %d/%m/%y')
        d = datetime.datetime(2013, 12, 23, 12, 23, 34)
        assert v('12, 23, 34 - 23/12/13') == d


class Test_totime(object):

    """
    Return a validator which converts a string to a `datetime.time`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.time.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *time*
    component is returned.  If it is a `datetime.time` it is returned
    unchanged.

    The return value is always a `datetime.time` object.  If the value
    cannot be converted an exception is raised.
    """

    def test_time(self):
        v = validate.totime()
        d = datetime.time(12, 23, 34)
        assert v(d) == d

    def test_datetime(self):
        v = validate.totime()
        d = datetime.datetime(2013, 12, 23, 12, 23, 34)
        assert v(d) == d.time()

    def test_iso(self):
        v = validate.totime()
        d = datetime.time(12, 23, 34)
        assert v('12:23:34') == d

    def test_iso_micro(self):
        v = validate.totime()
        d = datetime.time(12, 23, 34, 987000)
        assert v('12:23:34.987') == d

    def test_fmt(self):
        v = validate.totime('%M, %S, %H')
        d = datetime.time(12, 23, 34)
        assert v('23, 34, 12') == d
