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


class NormanWarning(UserWarning):
    """
    Base class for all Norman warnings.

    Currently all warnings use this class.  In the future, this behaviour
    will change, and subclasses will be used.
    """

#TODO: Situations where warning should be raised:
#    Field set to record outside database
#    record used which has been deleted.


class NormanError(Exception):
    """
    Base class for all Norman exceptions.
    """


class ConsistencyError(NormanError):
    """
    Raised on a fatal inconsistency in the data structure.
    """


class ValidationError(NormanError, ValueError, TypeError):
    """
    Raised when an operation resulting in table validation failing.

    For now this inherits from `NormanError`, `ValueError` and `TypeError`
    to keep it backwardly compatible.  This will change in version 0.7.0
    """
