# -*- coding: utf-8 -*-
#
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

import abc
import contextlib
import csv
import re
import sqlite3
import sys
import logging
import uuid

from ._table import Table
from ._field import NotSet
from ._six import u, string_types, with_metaclass
from ._six.moves import zip

_re_hex = ''
_re_uuid = re.compile(r'[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}', re.I)


def tarjan(graph):
    """
    Tarjan's Algorithm for finding cycles.
    """

    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}

    def strongconnect(node):
        # set the depth index for this node to the smallest unused index
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        # Consider successors of `node`
        try:
            successors = graph[node]
        except:
            successors = []
        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited; recurse on it
                for r in strongconnect(successor):
                    yield r
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current
                # strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node], index[successor])

        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []

            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            yield tuple(connected_component)

    for node in graph:
        if node not in lowlinks:
            for r in strongconnect(node):
                yield r


def uid():
    """
    Create a new uid value.  This is useful for files which do not
    natively provide a uid.
    """
    return u(str(uuid.uuid4()))


class Reader(with_metaclass(abc.ABCMeta)):

    """
    An abstract base class providing a framework for readers.

    Subclasses are required to implement `iter_source` and may re-implement
    any other methods to customise behaviour.

    The entry point in the `read` method, which iterates of over records
    yielded by `iter_source`, identifies possible foreign keys by `isuid` and
    dereferences them by identifying loops and processing them with
    `create_group`.  This method calls `create_record` to actually create the
    record.
    """

    @abc.abstractmethod
    def iter_source(self, source, db):
        """
        Iterate over record in the source file, yielding tuples of
        ``(table, data)`` or ``(table, uid, data)``.  *table* is the
        `~norman.Table` containing the record, *uid* is a globally unique
        value identifying the record and *data* is a dict of field values
        for the record, possibly containing other uids.  If *uid* is omitted,
        then one is automatically generated using `uuid`.

        :param db:      The `~norman.Database` being read into.
        :param source:  The data source, as specified in `read`.
        """
        raise NotImplementedError

    def create_record(self, table, uid, data):
        """
        Create a single record in *table*, using *uid* and *data*, as given
        by `iter_source`. This is called by `create_group`, so any
        foreign uid in *data* should have been dereferenced.  The record
        created should be returned, or, if it cannot be created, `None` should
        be returned.

        The default implementation simply calls ``table(**data)`` and sets the
        *uid*.
        """
        r = table(**data)
        r._uid = uid
        return r

    def create_group(self, records):
        """
        Create a group of records.  *records* is an iterable containing
        co-dependant records, i.e. records which cyclically reference each
        other.  In many cases, *records* will contain only a single record.

        Each record returned by *records* is a tuples of
        ``(table, uid, data, cycles)`` .  The first three values are the same
        as those returned by `iter_source`, except that foreign uids in *data*
        have been dereferenced.  *cycles* is a set of field names which
        contain the cyclic references.

        The default behaviour is to remove the cyclic fields from *data*
        for each record, create the records using `create_record`
        and assign the created records to the cyclic fields.

        The return value is an iterator over ``(uid, record)`` pairs.
        """
        created = {}
        for table, uid, data, cycles in records:
            fuids = set((field, data.pop(field)) for field in cycles)
            record = self.create_record(table, uid, data)
            if record is not None:
                created[uid] = (record, fuids)

        for uid, (record, fuids) in created.items():
            for field, fuid in fuids:
                setattr(record, field, created[fuid][0])
            yield uid, record

    def isuid(self, field, value):
        """
        Return `True` if *value*, for the specified *field*, could be a *uid*.

        *field* is a `~norman.Field` object.

        This only needs to check whether the value could possibly represent
        another field.  It is only actually considered a *uid* if there is
        another record which matches it.

        By default, this returns `True` for all strings which match a UUID
        regular expression, e.g. ``'a8098c1a-f86e-11da-bd1a-00112444be1e'``.
        """
        return (isinstance(value, string_types) and
                len(value) == 36 and _re_uuid.match(value))

    def read(self, source, db):
        """
        Read data from a *source* into *db*.

        This converts each value returned by `iter_source` into a record using
        `create_record`.  It also attempts to re-map nested records by
        searching for matching uids.

        Cycles in the data are detected, and all records involved in
        in a cycle are created in `create_group`.
        """
        # Dict of record dictionaries, keyed by UID.
        records = {}
        created = {}

        # Load records.
        for datatuple in self.iter_source(source, db):
            if len(datatuple) == 3:
                table, _uid, data = datatuple
            else:
                table, data = datatuple
                _uid = uid()
            records[_uid] = (table, data)

        # TODO: Can optimise this if uid is never specified.

        # Build a dependancy graph
        graph = {}
        for _uid in records:
            successors = set()
            uidfields = set()
            table, data = records[_uid]
            for f, v in data.items():
                if self.isuid(f, v) and v in records:
                    successors.add(v)
                    uidfields.add(f)
            records[_uid] = (table, data, uidfields)
            graph[_uid] = successors

        # Use Tarjan's algorithm to return uids in the order in which they
        # must be created, detecting cycles.
        for uids in tarjan(graph):
            iterrecords = []
            for _uid in uids:
                table, data, uidfields = records[_uid]
                cycles = set()
                for f in uidfields:
                    if data[f] not in uids:
                        data[f] = created[data[f]]
                    else:
                        cycles.add(f)
                iterrecords.append((table, _uid, data, cycles))
            for u, r in self.create_group(iterrecords):
                created[u] = r


class Writer(with_metaclass(abc.ABCMeta)):

    """
    An abstract base class providing a framework for writers.

    Subclasses are required to implement `context` and `write_record` and may
    re-implement any other methods to customise behaviour.

    The entry point in the `write` method, which opens the target file
    with `context` and iterates of over records in the database with `iterdb`.
    Each record is converted to a simple python structure with `simplify`
    and written using `write_record`.
    """

    @abc.abstractmethod
    def context(self, targetname, db):
        """
        Return a context manager which opens and closes the file, including
        and preparation and finalisation needed.  A common implementation
        might be::

            def context(self, file):
                return open(file, 'w')

        This can also be implemented using `contextlib.contextmanager`, which
        is useful for more complicated examples::

            @contextlib.contextmanager
            def context(self, targetname, db):
                fh = open(targetname, 'w')
                fh.write('### Header line ###')
                yield fh
                fh.write('### Footer line ###')
                fh.close()

        """
        raise NotImplementedError

    def iterdb(self, db):
        """
        Return an iterator over records in the database.

        Records should be returned in the order they are to be written.  The
        default implementation is a generator which iterates over records in
        each table.
        """
        for table in db:
            for record in table:
                yield record

    def simplify(self, record):
        """
        Convert a record to a simple python structure.

        The default implementation converts *record* to a `dict` of
        field values, omitting `~norman.NotSet` values and replacing other
        records with their *_uid* properties.  The return value is passed
        directly to `write_record`, so it can be anything recognised by it.
        This implementation returns a tuple of
        ``(tablename, record._uid, record_dict)``.
        """
        keys = record.__class__.fields()
        d = dict()
        for k in keys:
            value = getattr(record, k)
            if value is not NotSet:
                if isinstance(value, Table):
                    value = value._uid
                d[k] = value
        return (record.__class__.__name__, record._uid, d)

    def write(self, targetname, db):
        """
        Write the database to *filename*.

        *fieldname* is used only to open the file using `open`, so, depending
        on the implementation could be anything (e.g. a URL) which `open`
        recognises.  It could even be omitted entirely if, for example,
        the serialiser dumps the database as formatted text to stdout.
        """
        with self.context(targetname, db) as fh:
            for record in self.iterdb(db):
                self.write_record(self.simplify(record), fh)

    @abc.abstractmethod
    def write_record(self, record, target):
        """
        Write *record* to *target*.

        This is called by `write` for every record yielded by `iterdb`.
        *record* is the values returned by `simplify` and *target* is the
        value returned by `context`.
        """
        raise NotImplementedError


class Serialiser(Reader, Writer):

    """
    This simply inherits from `Reader` and `Writer` to combine the
    functionality into one class for interfaces which support both reading
    and writing.
    """


class Sqlite(Serialiser):

    """
    This is a `Serialiser` which reads and writes to a sqlite database.

    Each table is dumped to a sqlite table with the same field names.
    An additional field specified by *uidname* is included which
    contains the record's `~norman.Table._uid`.  *uidname* may be empty or
    `None`, in which case uids are ignored and the field is omitted.

    The sqlite database is created without any constraints.  As described in
    the `sqlite3` docs, under Python2, text is always returned as unicode.
    """

    def __init__(self, uidname='_uid_'):
        self.uidname = uidname

    def iter_source(self, source, db):
        """
        Only tables which match those in *db* and have a *_uid_* field
        are read.
        """
        with contextlib.closing(sqlite3.connect(source)) as conn:
            conn.row_factory = sqlite3.Row
            for table in db:
                tname = table.__name__
                query = 'SELECT * FROM "{0}";'.format(tname)
                try:
                    cursor = conn.execute(query)
                except sqlite3.OperationalError:
                    logging.warning("Table '{0}' not found".format(tname))
                else:
                    for row in cursor:
                        row = dict(row)
                        if not self.uidname:
                            yield table, row
                        elif self.uidname in row:
                            uid = row.pop(self.uidname)
                            yield table, uid, row

    @contextlib.contextmanager
    def context(self, targetname, db):
        conn = sqlite3.connect(targetname)
        conn.execute('BEGIN;')
        self.schema = {}
        for table in db:
            tname = table.__name__
            fields = list(table.fields())
            self.schema[tname] = fields
            fstr = ', '.join('"{0}"'.format(f) for f in fields)
            if self.uidname:
                fstr = '"{0}", '.format(self.uidname) + fstr
            try:
                conn.execute('DROP TABLE "{0}"'.format(tname))
            except sqlite3.OperationalError:
                pass
            query = 'CREATE TABLE "{0}" ({1});\n'.format(tname, fstr)
            conn.execute(query)
        yield conn
        conn.commit()
        conn.close()

    def write_record(self, record, target):
        tname, uid, rdict = record
        values = [rdict.get(f, None) for f in self.schema[tname]]
        if self.uidname:
            values[0:0] = [uid]
        qmarks = ', '.join('?' * len(values))
        query = 'INSERT INTO "{0}" VALUES ({1})'.format(tname, qmarks)
        target.execute(query, values)


class CSV(Serialiser):

    """
    This is a `Serialiser` which reads and writes to a collection of csv files.

    Each table in the database is written to a separate file, which is
    managed by `csv.DictReader` and `csv.DictWriter`.  Any extra initialisation
    parameters are passed to these.  If this includes *fieldnames*, it should
    be a mapping of table to fieldnames.  This defaults to a sorted list
    of table fields.  This is only used for writing.

    An additional field specified by *uidname* is prepended which
    contains the record's `~norman.Table._uid`.   *uidname* may be empty or
    `None`, in which case uids are ignored and the field is omitted.

    Since csv files can only contain text, all values are converted to
    strings when writing, and it is up to the database to convert them back
    into other objects when reading.  The exception to this is uid keys, which
    are handled by the `Reader`.  `~norman.NotSet` values are omitted when
    writing, and empty field values are converted to `~norman.NotSet` when
    reading.

    The target and source specified in `~Reader.read` and `~Writer.write`
    should be a mapping of table name to file name, for example::

        mapping = {Table1: '/path/table1.csv', Table2: '/path/table2.csv'}
        CSV().read(mapping, db)

    Any missing tables are omitted.
    """

    def __init__(self, uidname='_uid_', **kwargs):
        self.uidname = uidname
        self.kwargs = kwargs
        self.fieldnames = self.kwargs.pop('fieldnames', {})
        if sys.version >= '3':
            self._open = lambda name, mode: open(name, mode, newline='')
        else:
            self._open = lambda name, mode: open(name, mode + 'b')

    def iter_source(self, source, db):
        for table in db:
            try:
                filename = source[table]
            except KeyError:
                pass
            with self._open(filename, 'r') as fh:
                for row in csv.DictReader(fh, **self.kwargs):
                    if not self.uidname:
                        yield table, row
                    elif self.uidname in row:
                        uid = row.pop(self.uidname)
                        yield table, uid, row

    @contextlib.contextmanager
    def context(self, targetname, db):
        files = []
        writers = {}
        for table, path in targetname.items():
            fh = self._open(path, 'w')
            files.append(fh)
            fieldnames = self.fieldnames.get(table, sorted(table.fields()))
            if self.uidname:
                fieldnames = [self.uidname] + fieldnames
            writer = csv.DictWriter(fh, fieldnames=fieldnames, **self.kwargs)
            writer.writerow(dict(zip(fieldnames, fieldnames)))
            writers[table.__name__] = writer
        yield writers
        for fh in files:
            fh.close()

    def write_record(self, record, target):
        table, uid, record = record
        if self.uidname:
            record[self.uidname] = uid
        target[table].writerow(record)
