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

import collections
import copy
import functools
import re
import uuid

from ._except import ConsistencyError, ValidationError
from ._field import Field, Join
from ._query import Query
from ._compat import unicode, long, recursive_repr
from .tools import reduce2


_re_uuid = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
_re_uuid = re.compile(_re_uuid)


class _I:
    """
    An empty, hashable and weak referenceable object.
    """
    pass


class TableMeta(type):

    """
    Base metaclass for all tables.

    Tables support a limited sequence-like interface, with rapid lookup
    through indexed fields.  The sequence operations supported are ``__len__``,
    ``__contains__`` and ``__iter__``, and all act on instances of the table,
    i.e. records.
    """

    def __new__(mcs, name, bases, cdict):
        fulldict = {}
        for base in bases:
            for n, value in base.__dict__.items():
                if isinstance(value, (Field, Join)):
                    value = copy.copy(value)
                fulldict[n] = value
        fulldict.update(cdict)
        cls = type.__new__(mcs, name, bases, fulldict)
        cls._instances = {}
        cls._fields = {}
        for n, value in fulldict.items():
            if isinstance(value, (Field, Join)):
                value._name = n
                value._owner = cls
            if isinstance(value, Field):
                cls._fields[n] = value

        cls.hooks = collections.defaultdict(list)

        return cls

    def __init__(cls, name, bases, cdict):
        super(TableMeta, cls).__init__(name, bases, cdict)

    def __len__(cls):
        return len(cls._instances)

    def __contains__(cls, record):
        return record._key in cls._instances

    def __iter__(cls):
        return iter(cls._instances.values())

    def __setattr__(cls, name, value):
        if isinstance(value, (Field, Join)):
            if hasattr(value, '_owner'):
                raise ConsistencyError('Field already belongs to a table')
            if hasattr(cls, name):
                raise ConsistencyError("Field '{}' already exists".format(name))
            value._name = name
            value._owner = cls
            if isinstance(value, Field):
                cls._fields[name] = value
        super(TableMeta, cls).__setattr__(name, value)

    #TODO: addhook decorator, or something similar

    def delete(cls, records=None):
        """
        Delete delete all instances in *records*.  If *records* is
        omitted then all records in the table are deleted.
        """
        if records is None:
            records = set(cls)
        elif isinstance(records, Table):
            records = set([records])
        else:
            records = set(records)
        for r in records:
            key = r._key
            # Check if its been deleted by validate_delete
            r = cls._instances.get(key, None)
            if r:
                try:
                    r.validate_delete()
                    for v in cls.hooks['delete']:
                        v(r)
                except AssertionError as err:
                    raise ValidationError(*err.args)
                except:
                    raise
                else:
                    del cls._instances[r._key]

    def fields(cls):
        """
        Return an iterator over field names in the table
        """
        return cls._fields.keys()


_TableBase = TableMeta(str('_TableBase'), (object,), {})


class Table(_TableBase):

    """
    Each instance of a Table subclass represents a record in that Table.

    This class should be subclassed to define the fields in the table.
    It may also optionally provide `validate` and `validate_delete` methods.

    `Field` names should not start with ``_``, as these names are reserved
    for internal use.  Fields may be added to a `Table` after the `Table`
    is created, provided they do not already belong to another `Table`, and
    the `Field` name is not already used in the `Table`.
    """

    def __init__(self, **kwargs):
        key = _I()
        self._key = key
        data = dict([(f, getattr(self, f)) for f in self.__class__.fields()])
        badkw = set(kwargs.keys()) - set(data.keys())
        if badkw:
            raise AttributeError(badkw)
        data.update(kwargs)
        validate = self._validate
        self._validate = lambda: None
        try:
            for k, v in data.items():
                setattr(self, k, v)
        finally:
            self._validate = validate
        self._validate()
        self._instances[key] = self

    def __setattr__(self, attr, value):
        try:
            field = getattr(self.__class__, attr)
        except AttributeError:
            field = None
        if isinstance(field, Field):
            oldvalue = getattr(self, attr)
            # Get new value by validation
            try:
                for validator in field.validators:
                    value = validator(value)
            except Exception as err:
                if isinstance(err, AssertionError):
                    raise ValidationError(*err.args)
                else:
                    raise
            # To avoid endless recursion if validate changes a value
            if oldvalue != value:
                field.__set__(self, value)
                if field.unique:
                    table = self.__class__
                    uniques = (getattr(table, f) == getattr(self, f)
                               for f in table.fields() if getattr(table, f).unique)
                    existing = set(functools.reduce(lambda a, b: a & b, uniques)) - set([self])
                    if existing:
                        field.__set__(self, oldvalue)
                        msg = ('{}={}'.format(k, v) for k, v in uniques)
                        msg = ', '.join(msg)
                        msg = 'Not unique: {}'.format(msg)
                        raise ValidationError(msg)
                try:
                    self._validate()
                except:
                    field.__set__(self, oldvalue)
                    raise
            # Update the index
            if field.index:
                index = field._index
                try:
                    index[oldvalue].remove(self._key)
                except KeyError:
                    pass
                index[value].add(self._key)
        else:
            super(Table, self).__setattr__(attr, value)

    @recursive_repr()
    def __repr__(self):
        fields = sorted(self.__class__.fields())
        fields = [(f + '=%s') % repr(getattr(self, f)) for f in fields]
        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'

    @property
    def _uid(self):
        """
        This contains an id which is unique in the session.

        It's primary use is as an identity key during serialisation.  Valid
        values are any integer except 0, or a valid `uuid`.  The default
        value is calculated using `uuid.uuid4` upon its first call.
        It is not necessary that the value be unique outside the session,
        unless required by the serialiser.
        """
        try:
            return self.__uid
        except AttributeError:
            self._uid = unicode(uuid.uuid4())
            return self.__uid

    @_uid.setter
    def _uid(self, value):
        if isinstance(value, (int, long)):
            if value == 0:
                raise ValueError('_uid cannot be 0')
        elif isinstance(value, unicode):
            if not _re_uuid.match(value):
                raise ValueError('_uid must be a valid UUID')
        else:
            raise TypeError(value)
        self.__uid = value

    def _validate(self):
        """
        Convert AssertionError to ValidationError
        """
        try:
            self.validate()
            for v in self.__class__.hooks['validate']:
                v(self)
        except Exception as err:
            if isinstance(err, AssertionError):
                raise ValidationError(*err.args)
            else:
                raise

    def validate(self):
        """
        Raise an exception if the record contains invalid data.

        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, an exception should be raised.
        Internal validate (e.g. uniqueness checks) occurs before this
        method is called, and a failure will result in a `ValidationError`
        being raised.  For convenience, any `AssertionError` which is raised
        here is considered to indicate invalid data, and is re-raised as a
        `ValidationError`.  This allows all validation errors (both from this
        function and from internal checks) to be captured in a single
        *except* statement.

        Values may also be changed in the method.  The default implementation
        does nothing.
        """
        return

    def validate_delete(self):
        """
        Raise an exception if the record cannot be deleted.

        This is called just before a record is deleted and is usually
        re-implemented to check for other referring instances.  This method
        can also be used to propogate deletions and can safely modify
        this or other tables.

        Exceptions are handled in the same was as for `validate`.
        """
        pass
