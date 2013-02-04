.. module:: norman

.. testsetup::

    from norman import *


Introduction
============

Norman is designed to make it easy and efficient to implement any data
structure more complex than a `dict`.  The structures are stored entirely
in memory, and most operations on them are significantly faster than *O(n)*,
often *O(log n)*.


Features
--------

**Database-like API**

    Norman uses a database approach and terminology, allowing it to be used to
    prototype a formal database.  The basic data object is a `Table` which
    can be instantiated to create records.  This is the same approach used
    by `sqlalchemy <www.sqlalchemy.org>`_.

**Validation**

    Data validation is easy to apply on either `fields <Field.validators>`
    or `tables <Table.hooks>`, and can be implemented using the full power
    of Python.

**Complex structures**

    Tables can be linked together using a `Join`.  This is similar in concept
    to a typical database join, but is far more flexible as it allows
    any `Query` to be used as the join definition.

**Mutable structure definitions**

    Data structures are completely mutable, and every aspect of them can be
    changed at any time.  This feature is especially useful for `AutoTable`,
    which dynamically creates fields as data is added.

**Powerful queries**

    Norman provides a powerful and efficient :doc:`query <queries>` mechanism
    which can be customised to allow rapid, indexed lookups on arbitrary
    queries (e.g. records where ``record.text.endswith('z')``).

**Serialisation framework**

    The `serialise` module provides a framework for easily developing
    readers and writers for any file format.  This allows norman to be
    used as a file type converter.


Examples
--------

Norman is designed for working with relatively small amounts of data (i.e.
which can fit into memory), but which have complex structures and
relationships.  A few examples of how Norman can be used are:

1.  Extending python data structures, e.g. a multi-keyed dictionary.

        >>> class MultiDict(Table):
        ...     key1 = Field(unique=True)
        ...     key2 = Field(unique=True)
        ...     key3 = Field(unique=True)
        ...     value = Field()
        ...
        >>> MultiDict(key1=4, key2='abc', key3=0, value='a')
        MultiDict(key1=4, key2='abc', key3=0, value='a')
        >>> MultiDict(key1=5, key2='abc', key3=5, value='b')
        MultiDict(key1=5, key2='abc', key3=5, value='b')
        >>> MultiDict(key1=6, key2='def', key3=0, value='c')
        MultiDict(key1=6, key2='def', key3=0, value='c')
        >>> MultiDict(key1=4, key2='abc', key3=5, value='d')
        MultiDict(key1=4, key2='abc', key3=5, value='d')
        >>> query = (MultiDict.key1 == 4) & (MultiDict.key2 == 'abc')
        >>> for item in sorted(query, key=lambda r: r.value):
        ...     print(item)
        MultiDict(key1=4, key2='abc', key3=0, value='a')
        MultiDict(key1=4, key2='abc', key3=5, value='d')

2.  A tree, where each node has a parent.

    >>> class Node(Table):
    ...     parent = Field()
    ...     children = Join(parent)
    ...     node_data = Field()
    ...
    >>> root = Node(node_data='root node')
    >>> child1 = Node(node_data='child1', parent=root)
    >>> child2 = Node(node_data='child2', parent=root)
    >>> subchild1 = Node(node_data='2nd level child', parent=child1)
    >>> sorted(n.node_data for n in root.children())
    ['child1', 'child2']


3.  A node graph, where nodes are directionally connected by edges:

        >>> class Edge(Table):
        ...     from_node = Field(unique=True)
        ...     to_node = Field(unique=True)
        ...
        >>> class Node(Table):
        ...     edges_out = Join(Edge.from_node)
        ...     edges_in = Join(Edge.to_node)
        ...     all_edges = Join(query=lambda me: \
        ...                      (Edge.from_node == me) | (Edge.to_node == me))
        ...
        ...     def validate_delete(self):
        ...         # Delete all connecting links if a node is deleted
        ...         self.edges.delete()


3.  Even a lightweight database for a personal library:

        >>> db = Database()
        >>>
        >>> @db.add
        ... class Book(Table):
        ...     name = Field(unique=True, validators=[validate.istype(str)])
        ...     author = Field()
        ...
        ...     def validate(self):
        ...         assert isinstance(self.author, Author)
        ...
        >>> @db.add
        ... class Author(Table):
        ...     surname = Field(unique=True)
        ...     initials = Field(unique=True, default='')
        ...     nationality = Field()
        ...     books = Join(Book.author)


4.  Norman provides a sophisticated serialisation system for writing data
    to and loading it from virtually any source.  This example shows how
    it can be used as a converter data from CSV files to a sqlite
    database:

        >>> db = AutoDatabase()
        >>> serialise.CSV().read('source files', db)
        >>> serialise.Sqlite().write('output.sqlite', db)
