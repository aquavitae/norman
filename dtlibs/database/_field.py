#!/usr/bin/env python3
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

import collections

class NotSet:
    ''' Senitinal indicating that the field value has not yet been set.'''
    pass


class Field:
    ''' A `Field` is used in tables to define attributes of data.
    
    When a table is created, fields can be identified by using a `Field` 
    object:
    
    >>> class Table:
    ...     name = Field()
    
    `Field` objects support *get* and *set* operations, similar to 
    *properties*, but also provide additional options.  They are intended
    for use with `Table` subclasses.
    
    Field options are set as keyword arguments when it is initialised
    
    =========== ============================================================
    Keyword     Description
    =========== ============================================================
    index       This field should be indexed.  Indexed fields are much
                faster to look up.
    =========== ============================================================
    '''

    def __init__(self, index=False):
        self.index = index
        self._data = {}

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self._data.get(instance, NotSet)

    def __set__(self, instance, value):
        ''' Set a value for an instance.'''
        self._data[instance] = value
