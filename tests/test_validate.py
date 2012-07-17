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
from nose.tools import assert_raises

from norman import validate


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
