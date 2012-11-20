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

from __future__ import with_statement
from __future__ import unicode_literals

import contextlib
import csv
import re
import sqlite3
import logging
import uuid

from ._table import Table, TableMeta
from ._field import NotSet
from ._compat import unicode

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


class Serialiser(object):

    """
    An abstract base class providing a framework for serialisers.  Subclasses
    are instantiated with a `~norman.Database` object, and serialisation
    and de-serialisation is done through the `write` and `read`
    methods.  Class methods `dump` and `load` may also be used.

    Subclasses are required to implement `iterfile` and its counterpart,
    `write_record`, but may re-implement any other methods to customise
    behaviour.

    Serialisers are created with a single required argument, specifying the
    database upon which it acts.  They also support arbitrary keyword
    arguments which are set to an `options` dict and are intended to be used
    for setting serialisation options used by specific serialisers.
    """

    def __init__(self, db, **kwargs):
        self._db = db
        self._fh = None
        self._mode = None
        self.options = kwargs

    @property
    def db(self):
        """
        The database handled by the serialiser.
        """
        return self._db

    @property
    def fh(self):
        """
        An open file (or database connection), or `None`.   This is set to
        the result of `open`.  If a file is not currently open, then this
        is `None`.
        """
        return self._fh

    @property
    def mode(self):
        """
        Indicates the current mode of operation.  This is set to ``'w'`` 
        during *dump* operations and ``'r'`` during *load*.  At other
        times it is `None`.
        """
        return self._mode

    @classmethod
    def dump(cls, db, filename, **kwargs):
        """
        This is a convenience method for calling `write` and is equivalent
        to ``Serialise(db, **kwargs).write(filename)``.
        """
        return cls(db, **kwargs).write(filename)

    @classmethod
    def load(cls, db, filename, **kwargs):
        """
        This is a convenience method for calling `read` and is equivalent
        to ``Serialise(db, **kwargs).read(filename)``.
        """
        return cls(db, **kwargs).read(filename)

    @classmethod
    def uid(cls):
        """
        Create a new uid value.  This is useful for files which do not
        natively provide a uid, and can be used to generate one in
        `iterfile`.
        """
        return unicode(uuid.uuid4())

    def close(self):
        """
        Close the currently opened file.  The default behaviour is to call
        the file object's `!close` method.  This method is always called
        once a file has been opened, even if an exception occurs during
        writing.
        """
        self.fh.close()

    def create_records(self, records):
        """
        Create a group of records.  *records* is an iterable containing
        co-dependant records, i.e. records which cyclically reference each
        other.  In many cases, *records* will contain only a single record.

        Each record returned by *records* is a tuples of
        ``(table, uid, data, cycles)`` .  The first three values are the same
        as those returned by `iterfile`, except that foreign uids in *data*
        have been dereferenced.  *cycles* is a set of field names which
        contain the cyclic references.

        The default behaviour is to remove the cyclic fields from *data*
        for each record, create the records using ``table(**data)``
        and assign the created records to the cyclic fields.  The *uid*
        of each record is also assigned to its *_uid* attribute.

        The return value is an iterator over ``(uid, record)`` pairs.
        """
        created = {}
        for table, uid, data, cycles in records:
            fuids = set((field, data.pop(field)) for field in cycles)
            record = table(**data)
            record._uid = uid
            created[uid] = (record, fuids)

        for uid, (record, fuids) in created.items():
            for field, fuid in fuids:
                setattr(record, field, created[fuid][0])
            yield uid, record

    def finalise_read(self):
        """
        Finalise the file after reading data.  This is called after
        `run_read` but before `close`, and can be re-implemented for 
        implementation-specific finalisation.

        The default implementation does nothing.
        """
        return

    def finalise_write(self):
        """
        Finalise the file after writing data.

        This is called after `run_write` but before `close`, and can be
        re-implemented to for implementation-specific finalisation.

        The default implementation does nothing.
        """
        return

    def initialise_read(self):
        """
        Prepare the file for reading data.

        This is called before `run_read` but after `open`, and can be
        re-implemented to for implementation-specific setup.

        The default implementation does nothing.
        """
        return

    def initialise_write(self):
        """
        Prepare the file for writing data.

        This is called before `run_write` but after `open`, and can be
        re-implemented to for implementation-specific setup.

        The default implementation does nothing.
        """
        return

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
        return (isinstance(value, unicode) and
                len(value) == 36 and _re_uuid.match(value))

    def iterdb(self):
        """
        Return an iterator over records in the database.

        Records should be returned in the order they are to be written.  The
        default implementation is a generator which iterates over records in
        each table.
        """
        for table in self.db:
            for record in table:
                yield record

    def iterfile(self):
        """
        Return an iterator over records read from the file.

        Each item returned by the iterator should be a tuple of
        ``(table, uid, data)`` where  *table* is the `~norman.Table`
        containing the record, *uid* is a globally unique value identifying
        the record and *data* is a dict of field values for the record,
        possibly containing other uids.

        This is commonly implemented as a generator.
        """
        raise NotImplementedError

    def read(self, filename):
        """
        Load data into `db` from *filename*.

        *fieldname* is used only to open the file using `open`, so, depending
        on the implementation could be anything (e.g. a URL) which `open`
        recognises.  It could even be omitted entirely if, for example,
        the serialiser reads from stdin.
        """
        self._mode = 'r'
        self._fh = self.open(filename)
        try:
            self.initialise_read()
            self.run_read()
            self.finalise_read()
        finally:
            self.close()

    def open(self, filename):
        """
        Open *filename* for the current `mode`.

        The return value should be a handle to the open file.  The default
        behaviour is to open the file as binary using the builtin *open*
        function.
        """
        return open(filename, self.mode + 'b')

    def run_read(self):
        """
        Read data from the currently opened file.

        This is called between `initialise_read` and `finalise_read`, and
        converts each value returned by `iterfile` into a record using
        `create_records`.  It also attempts to re-map nested records by
        searching for matching uids.

        Cycles in the data are detected, and all records involved in
        in a cycle are created in `create_records`.
        """
        # Dict of record dictionaries, keyed by UID.
        records = {}
        created = {}

        # Load records.
        for table, uid, data in self.iterfile():
            records[uid] = (table, data)

        # Build a dependancy graph
        graph = {}
        for uid in records:
            successors = set()
            uidfields = set()
            table, data = records[uid]
            for f, v in data.items():
                if self.isuid(f, v) and v in records:
                    successors.add(v)
                    uidfields.add(f)
            records[uid] = (table, data, uidfields)
            graph[uid] = successors

        # Use Tarjan's algorithm to return uids in the order in which they
        # must be created, detecting cycles.
        for uids in tarjan(graph):
            iterrecords = []
            for uid in uids:
                table, data, uidfields = records[uid]
                cycles = set()
                for f in uidfields:
                    if data[f] not in uids:
                        data[f] = created[data[f]]
                    else:
                        cycles.add(f)
                iterrecords.append((table, uid, data, cycles))
            for u, r in self.create_records(iterrecords):
                created[u] = r

    def run_write(self):
        """
        Called by `dump` to write data.

        This is called after `initialise_write` and before `finalise_write`,
        and simply calls `write_record` for each value yielded by `iterdb`.
        """
        for record in self.iterdb():
            self.write_record(self.simplify(record))

    def simplify(self, record):
        """
        Convert a record to a simple python structure.

        The default implementation converts *record* to a `dict` of
        field values, omitting `~norman.NotSet` values and replacing other
        records with their *_uid* properties.  The return value of this
        implementation is a tuple of ``(tablename, record._uid, record_dict)``.
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

    def write(self, filename):
        """
        Write the database to *filename*.

        *fieldname* is used only to open the file using `open`, so, depending
        on the implementation could be anything (e.g. a URL) which `open`
        recognises.  It could even be omitted entirely if, for example,
        the serialiser dumps the database as formatted text to stdout.
        """
        self._mode = 'w'
        self._fh = self.open(filename)
        try:
            self.initialise_write()
            self.run_write()
            self.finalise_write()
        finally:
            self.close()

    def write_record(self, record):
        """
        Write *record* to the current file.

        This is called by `run_write` for every record yielded by `iterdb`.
        *record* is the values returned by `simplify`.
        """
        raise NotImplementedError


class Sqlite(Serialiser):

    """
    This is a `Serialiser` which reads and writes to a sqlite database.

    Each table in `~Serialiser.db` is dumped to a sqlite table with the
    same field names.  An additional field, *_uid_* is included which
    contains the record's *_uid*.  The sqlite database does not have any
    constraints, not even primary key constraints, as it is intended to
    be used purely for storage.

    The following methods are re-implemented from `Serialiser`:

    *   `~Serialiser.finalise_write` commits changes to the database.
    *   `~Serialiser.initialise_write` starts a database transaction and
        create tables.
    *   `~Serialiser.initialise_read` sets the `sqlite3` row factory.
    *   `~Serialiser.iterfile` yield records from each valid table in the
        file which matches a table in `~Serialiser.db`.
    *   `~Serialiser.open` returns an open database connection to *filename*.
    *   `~Serialiser.write_record` adds a record to the sqlite database.
    """

    def finalise_write(self):
        """
        Commit changes to the database.
        """
        self.fh.commit()

    def initialise_write(self):
        """
        Start a database transaction and create tables.

        The database schema is set here and assigned to a *schema* attribute.
        """
        self.fh.execute('BEGIN;')
        self.schema = {}
        for table in self.db:
            tname = table.__name__
            fields = list(table.fields())
            self.schema[tname] = fields
            fstr = '"_uid_", ' + ', '.join('"{}"'.format(f) for f in fields)
            try:
                self.fh.execute('DROP TABLE "{}"'.format(tname))
            except sqlite3.OperationalError:
                pass
            query = 'CREATE TABLE "{}" ({});\n'.format(tname, fstr)
            self.fh.execute(query)

    def initialise_read(self):
        self.fh.row_factory = sqlite3.Row

    def iterfile(self):
        """
        Yield records from each valid table in the file.

        Only tables which match those in *db* and have a *_uid_* field
        are read.
        """
        for table in self.db:
            tname = table.__name__
            query = 'SELECT * FROM "{}";'.format(tname)
            try:
                cursor = self.fh.execute(query)
            except sqlite3.OperationalError:
                logging.warning("Table '{}' not found".format(tname))
            else:
                for row in cursor:
                    row = dict(row)
                    if '_uid_' in row:
                        uid = row.pop('_uid_')
                        yield table, uid, row

    def open(self, filename):
        """
        Return a connection to the database *filename*
        """
        return sqlite3.connect(filename)

    def write_record(self, record):
        tname, uid, rdict = record
        values = [uid] + [rdict.get(f, None) for f in self.schema[tname]]
        qmarks = ', '.join('?' * len(values))
        query = 'INSERT INTO "{}" VALUES ({})'.format(tname, qmarks)
        self.fh.execute(query, values)


class CSV(Serialiser):

    """
    This is a `Serialiser` which reads and writes to a csv file.

    Since csv files can only represent a single table, this serialiser
    expects a `~norman.Table` in place of a `~norman.Database` as the
    required argument.  For internal consistency, *db* may still be specified,
    but is not required or used.  This means that `Serialiser`,
    `~Serialiser.load` and `~Serialiser.dump` can be called in two ways,
    although the first shown is preferred:

        CSV.load(MyTable, filename)
        CSV.load(db, MyTable, filename)

    *db* and *table* can also be set using keyword arguments.  Any additional
    keyword arguments and passed to `csv.DictReader` and `csv.DictWriter`.
    If *fieldnames*  as required by `csv.DictWriter` is missing, it will be
    set to a sorted list of the fields in the table.

    Note that this currently does not support any sort of complex objects in
    fields (such as other records), and all objects contained in the table
    are serialised as strings.  Likewise, all data is read in as text, and it
    is up to the table to format the data is required.

    The following methods are re-implemented from `Serialiser`:

    *   `~Serialiser.load`, `~Serialiser.dump` and `~Serialiser` require a
        `~norman.Table` instead of a `~norman.Database` (see above).
    *   `~Serialiser.initialise_write` writes the header row.
    *   `~Serialiser.isuid` always returns `False`.
    *   `~Serialiser.iterdb` iterates over records in the specified table.
    *   `~Serialiser.iterfile` yields records the csv file.
    *   `~Serialiser.open` opens the csv file in the appropriate mode for the
        current Python version (see `csv` for details) and returns a
        `csv.DictReader` or `csv.DictWriter` object.
    *   `~Serialiser.write_record` writes a row to the `csv.DictWriter` object.
    """

    def __init__(self, db=None, table=None, **kwargs):
        if isinstance(db, TableMeta):
            table = db
            db = None
        super(CSV, self).__init__(db, **kwargs)
        self._table = table

    @property
    def table(self):
        return self._table

    @classmethod
    def load(cls, db=None, table=None, **kwargs):
        super(CSV, cls).load(db, table, **kwargs)

    @classmethod
    def dump(cls, db=None, table=None, **kwargs):
        super(CSV, cls).dump(db, table, **kwargs)

    def initialise_write(self):
        fieldnames = self.options['fieldnames']
        self.fh.writerow(dict(zip(fieldnames, fieldnames)))

    def isuid(self, field, value):
        return False

    def iterdb(self):
        for record in self.table:
            yield record

    def iterfile(self):
        for record in self.fh:
            yield self.table, self.uid(), record

    def open(self, filename):
        import sys
        if sys.version >= '3':
            csvfile = open(filename, self.mode, newline='')
        else:
            csvfile = open(filename, self.mode + 'b')

        if self.mode == 'w':
            if 'fieldnames' not in self.options:
                self.options['fieldnames'] = sorted(self.table.fields())
            fh = csv.DictWriter(csvfile, **self.options)
        else:
            fh = csv.DictReader(csvfile, **self.options)
        fh.close = csvfile.close
        return fh

    def write_record(self, record):
        self.fh.writerow(record[2])


class Sqlite3:

    def load(self, db, filename):
        """
        The database supplied is read as follows:

        1.  Tables are searched for by name, if they are missing then
            they are ignored.

        2.  If a table is found, but does not have an "oid" field, it is
            ignored

        3.  Values in "oid" should be unique within the database, e.g.
            a record in "units" cannot have the same "oid" as a record
            in "cycles".

        4.  Records which cannot be added, for any reason, are ignored
            and a message logged.
        """
        with contextlib.closing(sqlite3.connect(filename)) as conn:
            conn.row_factory = sqlite3.Row
            # Extract the sql to a temporary dict structure, keyed by oid
            flat = {}
            for table in db:
                tname = table.__name__
                query = 'SELECT * FROM "{}";'.format(tname)
                try:
                    cursor = conn.execute(query)
                except sqlite3.OperationalError:
                    logging.warning("Table '{}' not found".format(tname))
                else:
                    for row in cursor:
                        row = dict(row)
                        if '_oid_' in row:
                            oid = row.pop('_oid_')
                            flat[oid] = (table, row)

            # Create correct types in flat
            for oid in flat.keys():
                self._makerecord(flat, oid)

    def dump(self, db, filename):
        """
        Dump the database to a sqlite database.

        Each table is dumped to a sqlite table, without any constraints.
        All values in the table are converted to strings and foreign objects
        are stored as an integer id (referring to another record). Each
        record has an additional field, '_oid_', which contains a unique
        integer.
        """
        with contextlib.closing(sqlite3.connect(filename)) as conn:
            conn.execute('BEGIN;')
            for table in db:
                tname = table.__name__
                fstr = ['"{}"'.format(f) for f in table.fields()]
                fstr = '"_oid_", ' + ', '.join(fstr)
                try:
                    conn.execute('DROP TABLE "{}"'.format(tname))
                except sqlite3.OperationalError:
                    pass
                query = 'CREATE TABLE "{}" ({});\n'.format(tname, fstr)
                conn.execute(query)
                for record in table:
                    values = [id(record)]
                    for fname in table.fields():
                        value = getattr(record, fname)
                        if isinstance(value, Table):
                            value = id(value)
                        elif value is NotSet:
                            value = 0
                        elif value is not None:
                            value = unicode(value)
                        values.append(value)
                    qmarks = ', '.join('?' * len(values))
                    query = 'INSERT INTO "{}" VALUES ({})'.format(tname, qmarks)
                    conn.execute(query, values)
            conn.commit()

    def _makerecord(self, flat, oid):
        """
        Create a new record for oid and return it.
        """
        table, row = flat[oid]
        if isinstance(row, table):
            return row
        keys = set(table.fields()) & set(row.keys())
        args = {}
        for key in keys:
            if isinstance(row[key], int):
                if row[key] == 0:
                    args[key] = NotSet
                else:
                    args[key] = self._makerecord(flat, row[key])
            else:
                args[key] = row[key]
        record = None
        try:
            record = table(**args)
        except ValueError as err:
            logging.warning(err)
        else:
            flat[oid] = (table, record)
        return record
