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

''' A new database framework.  

This framework provides a bases for creating database-like structures.
It doesn't, however, link into any database API (e.g. sqlite) and
doesn't support SQL syntax.  It is intended to be used as a lightweight,
in-memory framework allowing complex data structures, but without
the restrictions imposed by formal databases.  It should not be seen as
in any way as a replacement for, e.g., sqlite or postgreSQL, since it
services a different requirement.

One of the main distinctions between this framework and a SQL database is
in the way relationships are managed.  In a SQL database, each record
has one or more primary keys, which are typically referred to in other,
related tables by foreign keys.  Here, however, keys do not exist, and
records are linked directly to each other as attributes.
  
The main class is `Table` which defines the structure of a specific
type of record
'''

import weakref
import collections
import re
import copy

from ..xcollections import FilterList, MultiDict

from ._table import Table
from ._field import Field
from ._database import Database










class _Meta(type):
    def __new__(mcls, name, bases, cdict):
        cls = type.__new__(mcls, name, bases, cdict)
        #cls._instances = weakref.WeakValueDictionary()
        cls._instances = MultiDict()
        return cls

    def clear(cls):
        ''' Clear all instances. '''
        cls._instances.clear()

    def instances(cls, **kwargs):
        ''' Return a set of instances with attributes matching *kwargs*.  
        
        If no arguments are given, then all instances are returned.
        '''
        if len(kwargs) == 0:
            return set(v for v in cls._instances.values())
        ukeys = kwargs.keys() & set(cls.uniquefields())
        if len(ukeys) == 0:
            matches = cls._instances.values()
        else:
            matches = cls._instances.get(kwargs[ukeys.pop()])
            for k in ukeys:
                matches &= cls._instances.get(kwargs[k])
        it = kwargs.items()
        return set(i for i in matches if all(getattr(i, n) == v for n, v in it))


class Record(metaclass=_Meta):
    ''' A record is defined by a set of fields, as returned by the `fields`
    class method.  Each field has an associated type, which may be another 
    record.  Some fields may also be marked as *unique* (comparable to
    *primary keys*).  If a field type is a subclass of `Record`, then its 
    fields may also be accessed by joining the parent and child fieldnames
    with an underscore.  For this reason, field name should never have an
    underscore in them.  E.g., if a Record has a field called 'child'
    which is a subclass or Record and itself has a field, 'name', then the
    childs name can be accessed by ``record.child_name``.  Child fields
    may also be set this way, although if the child field is *unique*,
    then the behaviour is slightly different.  *Unique* fields define 
    a record, so changing a child's unique field implies changing the
    child itself, and an attempt is made to find another instance of
    the child type natching the new field value.  *child* itself is 
    then set to this value.
    
    Three levels of validation are used when field values are set.  The
    first is an internal prevalidation, which checks that the value
    type is correct, and if not attempts to correct it automatically.
    The second is defined by the `Record` subclass, and is used to define
    various constraints.  This is done by reimplementing `validate`, and 
    raising an AssertionError if a constraint is not fulfilled.  The third
    level of validation checks that all *unique* fields are supplied, 
    and are unique.  Each of these checks is done by checking all the
    field values (those in `fields`), including those previously set.
    
    Type checking is not excessively rigid, and *None* if the value cannot 
    be converted to the appropriate type it is accepted as is.  If this 
    behaviour is not desired, then additional type checks can be placed
    in `validate`.  *None* values are not allowed for unique fields, as 
    these imply that the field is not set. 
    
    All created instances are stored in a weak referenced dictionary,
    which can be queries using the class method `instances`. 
    '''

    @classmethod
    def fields(cls):
        raise NotImplementedError

    @classmethod
    def childfields(cls):
        ''' This is used to set child fields.
        
        This should return a dict of field names where each value is a 
        (field, list) tuple.  *field* is the name of the field in each 
        child containing this record and *list* is a mutable sequence 
        containing records.

        For example:
        
        >>> emails = []
        >>> class Emails(Record):
        ...     
        ...     @classmethod
        ...     def fields(cls):
        ...         return {'address': str,
        ...                 'person': Person}
        ...     
        ...     @classmethod
        ...     def uniquefields(cls):
        ...         return ['person', 'address']
        ...         
        >>> class Person(Record):
        ...     
        ...     @classmethod
        ...     def fields(cls):
        ...         return {'name': str}
        ...
        ...     @classmethod
        ...     def childfields(cls):
        ...         return {'emails': ('person', emails)} 
        ...
        ...     @classmethod
        ...     def uniquefields(cls):
        ...         return ['name']
        ...
        >>> person = Person(name='John')
        >>> emails.append(Email(person=person, address='john@gmail.com'))
        >>> emails.append(Email(person=person, address='john@yahoo.com'))
        >>> [e.address for e in person.emails]
        ['john@gmail.com', john@yahoo.com']
        
        It is also possible to use underscore notation:
        
        >>> person.emails_address
        ['john@gmail.com', john@yahoo.com']
        '''
        return {}

    @classmethod
    def uniquefields(cls):
        raise NotImplementedError

#    @classmethod
#    def uniqueinstances(cls, **kwargs):
#        ''' Same as `instances`, but only check unique fields.
#        
#        For checks where *kwargs* contains all the unique fields, this
#        method is much faster than `instances`.  However, all of the
#        unique fields must be specified, and other fields are ignored.
#        '''
#        key = tuple(kwargs[n] for n in cls.uniquefields())
#        try:
#            return {cls._instances[key]}
#        except KeyError:
#            return {}


    def __init__(self, **kwargs):
        # Check for valid field names
        fields = self.fields().keys()
        for field in fields:
            if not re.match('[a-zA-Z][a-zA-Z0-9]*$', field):
                raise AttributeError(field)
        dups = self.fields().keys() & self.childfields().keys()
        if len(dups) > 0:
            raise AttributeError('fields cannot be in childfields: {}'.format(dups))
        missing = set(self.uniquefields()) - self.fields().keys()
        if len(missing) > 0:
            raise AttributeError('uniquefields must be in fields: {}'.format(missing))

        # Populate data
        # _key is a tuple of keys which store this in _instances. The tuple 
        # values correspond with uniquefields.
        self._key = tuple()
        data = dict.fromkeys(self.fields().keys(), None)
        data.update(kwargs)
        data = self._validate(data)
        self._data = data
        self._children = dict((n, FilterList(lambda o: getattr(o, v[0]) is self,
                                 v[1])) for n, v in self.childfields().items())
        self._updateinstances()

    def _updateinstances(self):
        for k in self._key:
            self._instances.popitem((k, self))
        self._key = tuple(self._data[n] for n in self.uniquefields())
        if not self._key:
            self._key = (id(self),)
        for k in self._key:
            self._instances[k] = self

    def __getattr__(self, attr):
        if attr in self._data:
            return self._data[attr]
        elif attr in self._children:
            return self._children[attr]
        elif '_' in attr:
            attr, childattr = attr.split('_', 1)
            child = getattr(self, attr)
            if attr in self._children:
                return [getattr(c, childattr) for c in child]
            else:
                return None if child is None else getattr(child, childattr)
        else:
            raise AttributeError(attr)

    def __setattr__(self, attr, value):
        if attr.startswith('_'):
            return super().__setattr__(attr, value)
        data = copy.copy(self._data)
        data[attr] = value
        data = self._validate(data)
        self._data = data
        self._updateinstances()

    @classmethod
    def _checkfieldnames(cls, data):
        for name in data:
            if '_' in name:
                name = name.split('_', 1)[0]
            if name not in cls.fields():
                raise AttributeError(name)

    @classmethod
    def _checkunique(cls, data):
        for name in cls.uniquefields():
            if data.get(name, None) is None:
                raise ValueError("Not unique: '{}'".format(name))

    @classmethod
    def _checkchildnames(cls, data):
        children = {} # keyed by name, values are dicts of (fieldname, value)
        for name in list(filter(lambda f: '_' in f, data.keys())):
            pfield, cfield = name.split('_', 1)
            children.setdefault(pfield, {})[cfield] = data.pop(name)
        for name in children:
            child = data.get(name, None)
            child = cls._child(name, child, children[name])
            data[name] = child
        return data

    @classmethod
    def _child(cls, name, child, data):
        '''Return a child instance for field *name*.
        
        *data* is a dict of values defining the child, and *child* is an
        existing child instance, or None.  If *data* contains
        unique fields, then a matching instance in searched for and returned,
        otherwise the existing instance is just updated.
        '''
        ctype = cls.fields()[name]
        if set(data.keys()) & set(ctype.uniquefields()) or child is None:
            cdata = {} if child is None else copy.copy(child._data)
            cdata.update(data)
            existing = ctype.instances(**cdata)
            if len(existing) == 0:
                raise ValueError('No match for {}: {}'.format(name, data))
            elif len(existing) == 1:
                child = existing.pop()
            else:
                raise ValueError('Insufficient information for {}: {}'.format(name, data))

#        for n, v in data.items():
#            setattr(child, n, v)
        return child

    def _validate(self, data):
        data = self._prevalidate(data)
        try:
            data = self.validate(data)
        except AssertionError as err:
            raise ValueError(*err.args)
        data = self._postvalidate(self._key, data)
        return data

    @classmethod
    def _checktype(cls, name, data):
        vtype = cls.fields()[name]
        if not isinstance(data[name], (vtype, type(None))):
            if issubclass(vtype, Record):
                raise TypeError("'{}' has wrong type.".format(name))
            else:
                try:
                    data[name] = vtype(data[name])
                except Exception:
                    pass

    @classmethod
    def _prevalidate(cls, data):
        cls._checkfieldnames(data)
        data = cls._checkchildnames(data)
        cls._checkunique(data)
        for name in data:
            if name in cls.fields():
                cls._checktype(name, data)
        return data

    @classmethod
    def validate(cls, data):
        return data

    @classmethod
    def _postvalidate(cls, currentkey, data):
        key = tuple((data[n]) for n in cls.uniquefields())
        if (key not in (currentkey, tuple()) and
            cls.instances(**dict(zip(cls.uniquefields(), key)))):
            raise ValueError('Not unique: {}'.format(key))
        return data

