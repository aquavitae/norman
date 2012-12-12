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
import operator
import re
import uuid

from ._except import ConsistencyError, ValidationError
from ._field import Field, Join, NotSet
from ._compat import unicode, long, recursive_repr
from ._store import Store


_re_uuid = '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
_re_uuid = re.compile(_re_uuid)


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
        if '_store' not in cdict:
            cls._store = Store()
        for n, value in fulldict.items():
            if isinstance(value, (Field, Join)):
                value._name = n
                value._owner = cls
            if isinstance(value, Field):
                cls._store.add_field(value)

        cls.hooks = collections.defaultdict(list)
        return cls

    def __init__(cls, name, bases, cdict):
        super(TableMeta, cls).__init__(name, bases, cdict)

    def __len__(cls):
        return cls._store.record_count()

    def __contains__(cls, record):
        return cls._store.has_record(record)

    def __iter__(cls):
        return cls._store.iter_records()

    def __setattr__(cls, name, value):
        if isinstance(value, (Field, Join)):
            if hasattr(value, '_owner'):
                raise ConsistencyError('Field already belongs to a table')
            if hasattr(cls, name):
                raise ConsistencyError("Field '{}' already exists".format(name))
            value._name = name
            value._owner = cls
            if isinstance(value, Field):
                cls._store.add_field(value)
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
            # Check if its been deleted by validate_delete
            if r in cls:
                try:
                    r.validate_delete()
                    for v in cls.hooks['delete']:
                        v(r)
                except AssertionError as err:
                    raise ValidationError(*err.args)
                except:
                    raise
                else:
                    cls._store.remove_record(r)

    def fields(cls):
        """
        Return an iterator over field names in the table
        """
        return cls._store.fields.keys()


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

    The internal data store used can be set by assigning an instance of
    a `Store` to `_store`.  The default is to use `DefaultStore`.
    """

    def __init__(self, **kwargs):
        store = self.__class__._store
        badkw = set(kwargs.keys()) - set(store.fields.keys())
        if badkw:
            raise AttributeError(badkw)
        kwargs
        # Get new values by validation
        data = {}
        for field in store.fields.values():
            if field.name in kwargs:
                if field.readonly:
                    raise ValidationError('Field is read only')
                value = kwargs[field.name]
            else:
                value = field.default
            try:
                for validator in field.validators:
                    value = validator(value)
            except Exception as err:
                if isinstance(err, AssertionError):
                    raise ValidationError(*err.args)
                else:
                    raise
            data[field] = value

        # Check uniqueness
        if any(f.unique for f in store.fields.values()):
            self._assert_unique(data)

        # All good so far, so add the data to the store
        store.add_record(self)
        for field, value in data.items():
            store.set(self, field, value)

        # Validate record
        try:
            self._validate()
        except:
            store.remove_record(self)
            raise

    def __setattr__(self, attr, value):
        store = self.__class__._store
        try:
            field = store.fields[attr]
        except KeyError:
            return super(Table, self).__setattr__(attr, value)

        # Get new value by validation
        try:
            for validator in field.validators:
                value = validator(value)
        except Exception as err:
            if isinstance(err, AssertionError):
                raise ValidationError(*err.args)
            else:
                raise
        oldvalue = store.get(self, field)
        # To avoid endless recursion if validate changes a value
        if oldvalue != value:
            if field.readonly and oldvalue is not NotSet:
                raise ValidationError('Field is read only')
            # This is expensive, only do it once on record creation
            if field.unique:
                self._assert_unique({field: value})
            store.set(self, field, value)
            try:
                self._validate()
            except:
                store.set(self, field, oldvalue)
                raise

    def _assert_unique(self, replacevalues):
        store = self.__class__._store
        # Don't use a Query here because it is too slow
        matches = []
        for field in store.fields.values():
            if field.unique:
                if field in replacevalues:
                    value = replacevalues[field]
                else:
                    value = store.get(self, field)
                matches.append(set(store.indexes[field] == value))

        matches = functools.reduce(operator.and_, matches)
        existing = set(matches) - set([self])
        if existing:
            raise ValidationError('Not unique: ', existing)

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

    def __eq__(self, other):
        """
        Identical objects are equal.
        """
        return self is other

    def __gt__(self, other):
        """
        Compare by string.
        """
        return str(self) > str(other)
