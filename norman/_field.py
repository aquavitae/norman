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


class NotSet:
    def __bool__(self):
        return False


# Senitinal indicating that the field value has not yet been set.
NotSet = NotSet()

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
    
    ========== ============ ===================================================
    Keyword    Default      Description
    ========== ============ ===================================================
    unique     False        True if records should be unique on this field.
                            In database terms, this is the same as setting
                            a primary key.  If more than one field have this 
                            set then records are expected to be unique on all
                            of them.  Unique fields are always indexed.
    index      False        True if the field should be indexed.  Indexed 
                            fields are much faster to look up.  Setting
                            ``unique = True`` implies ``index = True``
    default    None         If missing, `NotSet` is used.
    readonly   False        Prohibits setting the variable, unless its value
                            is `NotSet`.  This can be used with *default*
                            to simulate a constant.
    ========== ============ ===================================================
    
    Note that *unique* and *index* are table-level controls, and are not used
    by `Field` directly.  It is the responsibility of the table to
    implement the necessary constraints and indexes.
    '''

    def __init__(self, *, unique=False, index=False, default=NotSet,
                 readonly=False):
        self.unique = unique
        self.index = index or unique
        self.default = default
        self.readonly = readonly
        self._data = {}

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return self._data.get(instance, self.default)

    def __set__(self, instance, value):
        ''' Set a value for an instance.'''
        if (self.readonly and
            self.__get__(instance, instance.__class__) is not NotSet):
            raise TypeError('Field is read only')
        self._data[instance] = value

