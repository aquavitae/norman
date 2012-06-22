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

from collections import defaultdict
import copy
import functools
import re
import uuid
import weakref

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

    The methods provided by this metaclass are essentially those which apply
    to the table (as opposed to those which apply records).

    Tables support a limited sequence-like interface, with rapid lookup
    through indexed fields.  The sequence operations supported are ``__len__``,
    ``__contains__`` and ``__iter__``, and all act on instances of the table,
    i.e. records.
    """

    def __new__(mcs, name, bases, cdict):
        cls = type.__new__(mcs, name, bases, cdict)
        cls._instances = {}
        cls._indexes = {}
        cls._fields = {}
        fulldict = copy.copy(cdict)
        for base in bases:
            fulldict.update(base.__dict__)
        for name, value in fulldict.items():
            if isinstance(value, (Field, Join)):
                value._name = name
                value._owner = cls
            if isinstance(value, Field):
                cls._fields[name] = value
                if value.index:
                    cls._indexes[name] = defaultdict(weakref.WeakSet)
        return cls

    def __init__(cls, name, bases, cdict):
        super(TableMeta, cls).__init__(name, bases, cdict)

    def __len__(cls):
        return len(cls._instances)

    def __contains__(cls, record):
        return record._key in cls._instances

    def __iter__(cls):
        return iter(cls._instances.values())

    def iter(cls, **kwargs):
        """
        Iterate over records with field values matching *kwargs*.
        """
        if not kwargs:
            return iter(cls)
        qs = (getattr(cls, k) == v for k, v in kwargs.items())
        q = functools.reduce(lambda a, b: a & b, qs)
        return iter(q)

    def contains(cls, **kwargs):
        """
        Return `True` if the table contains any records matching *kwargs*.
        """
        it = cls.iter(**kwargs)
        try:
            next(it)
        except StopIteration:
            return False
        return True

    def get(cls, **kwargs):
        """
        Return a set of all records with field values matching *kwargs*.
        """
        return set(cls.iter(**kwargs))

    def delete(cls, records=None, **keywords):
        """
        Delete delete all instances in *records* which match *keywords*.

        If *records* is omitted then the entire table is searched.  For
        example:

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
        """
        if records is None:
            records = set(cls)
        elif isinstance(records, Table):
            records = set([records])
        else:
            records = set(records)
        kwmatch = set(cls.iter(**keywords))
        keys = [r._key for r in records & kwmatch]
        for key in keys:
            # Check if its been deleted by validate_delete
            r = cls._instances.get(key, None)
            if r:
                try:
                    r.validate_delete()
                except AssertionError as err:
                    raise ValueError(*err.args)
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

    This class should be inherited from to define the fields in the table.
    It may also optionally provide a `validate` method.
    """

    def __init__(self, **kwargs):
        key = _I()
        self._key = key
        data = dict([(f, getattr(self, f)) for f in self.__class__.fields()])
        badkw = set(kwargs.keys()) - set(data.keys())
        if badkw:
            raise AttributeError(badkw)
        data.update(kwargs)
        validate = self.validate
        self.validate = lambda: None
        try:
            for k, v in data.items():
                setattr(self, k, v)
        finally:
            self.validate = validate
        self._validate()
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
                    existing = set(table.iter(**uniques)) - {self}
                    if existing:
                        field.__set__(self, oldvalue)
                        raise ValueError("Not unique: {}={}".format(field.name,
                                                                repr(value)))
                try:
                    self._validate()
                except:
                    field.__set__(self, oldvalue)
                    raise
            if field.index:
                self._updateindex(attr, oldvalue, value)
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
        values are any integer except 0, or a UUID.  The default
        value is calculated using `uuid.uuid4` upon its first call.
        It is not necessarily required that it be universally unique.
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
        Convert AssertionError to ValueError
        """
        try:
            self.validate()
        except Exception as err:
            if isinstance(err, AssertionError):
                raise ValueError(*err.args)
            else:
                raise

    def _updateindex(self, name, oldvalue, newvalue):
        index = self._indexes[name]
        try:
            index[oldvalue].remove(self._key)
        except KeyError:
            pass
        index[newvalue].add(self._key)

    def validate(self):
        """
        Raise an exception if the record contains invalid data.

        This is usually re-implemented in subclasses, and checks that all
        data in the record is valid.  If not, and exception should be raised.
        Internal validate (e.g. uniqueness checks) occurs before this
        method is called, and a failure will result in a `ValueError` being
        raised.  For convenience, any `AssertionError` which is raised here
        is considered to indicate invalid data, and is re-raised as a
        `ValueError`.  This allows all validation errors (both from this
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
        re-implemented to check for other referring instances.  For example,
        the following structure only allows deletions of *Name* instances
        not in a *Group*.

        >>> class Name(Table):
        ...  name = Field()
        ...  group = Field(default=None)
        ...
        ...  def validate_delete(self):
        ...      assert self.group is None, "Can't delete '{}'".format(self.name)
        ...
        >>> class Group(Table)
        ...  id = Field()
        ...  @property
        ...  def names(self):
        ...      return Name.get(group=self)
        ...
        >>> group = Group(id=1)
        >>> n1 = Name(name='grouped', group=group)
        >>> n2 = Name(name='not grouped')
        >>> Name.delete(name='not grouped')
        >>> Name.delete(name='grouped')
        Traceback (most recent call last):
            ...
        AssertionError: Can't delete "grouped"
        >>> {name.name for name in Name.get()}
        {'grouped'}

        Exceptions are handled in the same was as for `validate`.

        This method can also be used to propogate deletions and can safely
        modify this or other tables.
        """
        pass
