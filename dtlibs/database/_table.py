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
import copy
import functools
import weakref

from .. import core

from ._field import Field, NotSet

class _I:
    ''' An empty, hashable and weak referenceable object.'''
    pass


class TableMeta(type):
    ''' Metaclass for all tables.
    
    The methods provided by this metaclass are essentially those which apply
    to the table (as opposed to those which apply records).
    
    Tables support a limited sequence-like interface, but support rapid
    lookup through indexes.  Internally, each record is stored in a dict
    with random numerical keys.  Indexes simply map record attributes to keys.
    '''

    def __new__(mcls, name, bases, cdict, database=None):
        cls = type.__new__(mcls, name, bases, cdict)
        cls._instances = {}
        cls._indexes = {}
        cls._fields = {}
        if database is not None:
            database._tables.add(cls)
        fulldict = copy.copy(cdict)
        for base in bases:
            fulldict.update(base.__dict__)
        for name, value in fulldict.items():
            if isinstance(value, Field):
                value.name = name
                cls._fields[name] = value
                if value.index:
                    cls._indexes[name] = collections.defaultdict(weakref.WeakSet)
        return cls

    def __init__(cls, name, bases, cdict, database=None):
        super().__init__(name, bases, cdict)

    def __len__(cls):
        return len(cls._instances)

    def __contains__(cls, record):
        return record._key in cls._instances

    def __iter__(cls):
        return iter(cls._instances.values())

    def get(cls, **kwargs):
        ''' A generator which iterates over records matching kwargs.'''
        keys = kwargs.keys() & cls._indexes.keys()
        if keys:
            f = lambda a, b: a & b
            matches = functools.reduce(f, (cls._indexes[key][kwargs[key]] for key in keys))
            matches = [cls._instances[k] for k in matches if k in cls._instances]
        else:
            matches = cls._instances.values()
        for m in matches:
            if all(getattr(m, k) == v for k, v in kwargs.items()):
                yield m

    def delete(cls, records=None, **keywords):
        ''' Delete records from the table.
        
        This will delete all instances in *records* which match *keywords*.
        E.g.
        
        >>> class T(Table):
        ...     id = Field()
        ...     value = Field()
        >>> records = [T(id=1, value='a'),
        ...            T(id=2, value='b'),
        ...            T(id=3, value='c'),
        ...            T(id=4, value='b'),
        ...            T(id=5, value='b'),
        ...            T(id=6, value='c'),
        ...            T(id=7, value='c'),
        ...            T(id=8, value='b'),
        ...            T(id=9, value='a'),
        >>> [t.id for t in T.get()]
        [1, 2, 3, 4, 5, 6, 7, 8, 9]
        >>> T.delete(records[:4], value='b')
        >>> [t.id for t in T.get()]
        [1, 3, 5, 6, 7, 8, 9]
        
        If no records are specified, then all are used.
        
        >>> T.delete(value='a')
        >>> [t.id for t in T.get()]
        [3, 5, 6, 7, 8]
        
        If no keywords are given, then all records in in *records* are deleted.
        >>> T.delete(records[2:4])
        >>> [t.id for t in T.get()]
        [3, 5, 8]
        
        If neither records nor keywords are deleted, then the entire 
        table is cleared.
        '''
        if records is None:
            records = cls.get()
        if isinstance(records, Table):
            records = {records}
        kwmatch = cls.get(**keywords)
        rec = set(records) & set(kwmatch)
        for r in rec:
            del cls._instances[r._key]

    def fields(cls):
        ''' Return an iterator over field names in the table. '''
        return cls._fields.keys()


class Table(metaclass=TableMeta):
    ''' Each instance of a Table subclass represents a record in that Table.
    
    This class should be inherited from to define the fields in the table.
    It may also optionally provide a `validate` method.
    '''
    def __init__(self, **kwargs):
        key = _I()
        self._key = key
        data = dict.fromkeys(self.__class__.fields(), NotSet)
        badkw = kwargs.keys() - data.keys()
        if badkw:
            raise AttributeError(badkw)
        data.update(kwargs)
        validate = self.validate
        self.validate = core.none
        try:
            for k, v in data.items():
                setattr(self, k, v)
        finally:
            self.validate = validate
        self.validate()
        self._instances[key] = self

    def __setattr__(self, attr, value):
        try:
            field = getattr(self.__class__, attr)
        except AttributeError:
            field = None
        if isinstance(field, Field):
            oldvalue = getattr(self, attr)
            # To avoid endless recursion if validate changes a value
            if oldvalue != value:
                field.__set__(self, value)
                if field.unique:
                    table = self.__class__
                    uniques = dict((f, getattr(self, f)) for f in table.fields()
                                   if getattr(table, f).unique)
                    existing = set(self.__class__.get(**uniques)) - {self}
                    if existing:
                        raise ValueError(value)
                try:
                    self.validate()
                except Exception as err:
                    field.__set__(self, oldvalue)
                    if isinstance(err, AssertionError):
                        raise ValueError(*err.args)
                    else:
                        raise
            if field.index:
                self._updateindex(attr, oldvalue, value)
        else:
            super().__setattr__(attr, value)

    def _updateindex(self, name, oldvalue, newvalue):
        index = self._indexes[name]
        try:
            index[oldvalue].remove(self._key)
        except KeyError:
            pass
        index[newvalue].add(self._key)

    def validate(self):
        ''' Raise an exception of the record contains invalid data.
        
        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, and exception should be raised.
        Values may also be changed in the method, but care should be taken
        doing so as invalid records are rolled back.  For example:
        
        >>> class T(Table):
        ...     a = Field()
        ...     b = Field()
        ...     def validate(self):
        ...         self.b = self.a
        ...         assert self.a != 4
        >>> t = T()
        >>> t.a = 1
        >>> t.a, t.b
        (1, 1)
        >>> t.a = 4
        Traceback (Most recent call last):
          ...
        ValueError: 4
        >>> t.a, t.b
        (1, 4)
        '''
        return

