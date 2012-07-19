Norman
======

Norman provides a framework for creating complex data structures using
an database-like approach.  The range of potential application is wide,
for example in-memory databases, multi-keyed dictionaries or node graphs.
These applications are illustrated in the following examples.

Database
--------

This is a small database for a personal library::

    db = Database()

    @db.add
    class Book(Table):
        name = Field(unique=True)
        author = Field(index=True)

        def validate(self):
            assert isinstance(self.name, str)
            assert isinstance(self.author, Author)

    @db.add
    class Author(Table):
        surname = Field(unique=True)
        initials = Field(unique=True, default='')
        nationality = Field()
        books = Join(Book.author)


Multi-keyed Dictionary
----------------------

This table can be used as a dictionary with three keys::

    class MultiDict(Table):
        key1 = Field(unique=True)
        key2 = Field(unique=True)
        key3 = Field(unique=True)
        value = Field()

Values can be added by::

    MultiDict(key1=4, key2='abc', key3=0, value='efg')

And queried by::

    for m in (MultiDict.key1 == 4 & Multidict.key2 == 'abc'):
        print(m.value)


Node Graph
----------

This is a graph, where each node can have many parent nodes and many
children nodes::

    class Link(Table):
        """
        Directional connections between nodes.
        """
        parent = Field(unique=True)
        child = Field(unique=True)

        def validate(self):
            assert isinstance(self.parent, Node)
            assert isinstance(self.child, Node)


    class Node(Table):
        """
        Nodes in the graph.
        """
        parents = Join(query=lambda n: (Link.child == n).field('parent'))
        children = Join(query=lambda n: (Link.parent == n).field('child'))

        def validate_delete(self):
            # Delete all connecting links if a node is deleted
            (Link.parent == self).delete()
            (Link.child == self).delete()
