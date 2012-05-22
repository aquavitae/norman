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

from norman import tools


class TestDateFromIso:

    def check_dt(self, dt):
        iso = str(dt)
        got = tools.dtfromiso(iso)
        assert got == dt, got

    def test_datetime(self):
        'Test a bunch of datetimes'
        dt = [datetime.datetime(2001, 12, 23, 11, 23, 43, 123456),
              datetime.datetime(2000, 1, 1, 1, 1, 1, 1),
              datetime.datetime(1990, 12, 3)]
        for d in dt:
            self.check_dt(d)

    def test_date(self):
        'Test a bunch of dates'
        dt = [datetime.date(1992, 1, 1),
              datetime.date(2123, 12, 31)]
        for d in dt:
            self.check_dt(d)

    def test_time(self):
        'Test a bunch of times'
        dt = [datetime.time(11, 23, 19, 123456),
              datetime.time(14, 43, 20),
              datetime.time(1, 59),
              datetime.time(4)]
        for d in dt:
            self.check_dt(d)
