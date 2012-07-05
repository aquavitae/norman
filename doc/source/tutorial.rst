.. module:: norman

.. testsetup::

    from norman import *


Tutorial
========

This tutorial shows how to create a simple library database which manages
books and authors using Norman.

.. contents::


Creating Tables
---------------

The first step is to create a `Table` containing all the books in the library.
New tables are created by subclassing `Table`, and defining fields as
class attributes using `Field`::

    class Book(Table):
        name = Field()
        author = Field()

New books can be added to this table by creating instances of it::

    Book(name='The Hobbit' author='Tolkien')

However, at this stage there are no restrictions on the data that is entered,
so it is possible to create something like this::

    Book(name=42, author=['This', 'is', 'not', 'an', 'author'])


Constraints
-----------

We want to add some restrictions, such as ensuring that the name is always a
unique string.  The way to add these constraints is to set the `!name`
field as unique and to add a `!validate` method to the table::

    class Book(Table):
        name = Field(unique=True)
        author = Field()

        def validate(self):
            assert isinstance(self.refno, int)
            assert isinstance(self.name, str)

Now, trying to create an invalid book as in the previous example will raise a
`ValueError`.


Joined Tables
-------------

The next exercise is to add some background information about each author.
The best way to do this is to create a new table of authors which can be linked
to the books::

    class Author(Table):
        surname = Field(unique=True)
        initials = Field(unique=True, default='')
        dob = Field()
        nationality = Field()

Two new concepts are used here.  Default values can be assigned to a `Field`
as illustrated by `!surname`, and more than one field can be unique.  This
means that authors cannot have the same surname and initials, so ``'A. Adams'``
and ``'D. Adams'`` is ok, but two ``'D. Adams'`` is not.

We can also add a list of books by the author, by using a `Join`.  This is
similar to a `Field`, but is created with a reference to foreign field
containing the link, and contains an iterable rather than a single value::

    class Author(Table):
        surname = Field(unique=True)
        initials = Field(unique=True, default='')
        nationality = Field()
        books = Join(Book.author)

This tells the `!Author` table that its `!books` attribute should contain all
`!Book` instances with a matching `!author` field::

    class Book(Table):
        refno = Field(unique=True)
        name = Field()
        author = Field()

        def validate(self):
            assert isinstance(self.refno, int)
            assert isinstance(self.name, str)
            assert isinstance(self.author, str)

This is dynamic link, so every time the `!books` attribute is queried, the
`!Book` table is scanned for matching values.  Since each record has to be
checked individually this can become very slow, so the `!author` field
can be indexed to improve performance by adding an *index* argument to
its definition.  It is worth noting that unique fields are automatically
indexed, so `!Book.name` already supports fast lookups::

    class Book(Table):
        ...
        author = Field(index=True)
        ...


Databases
---------

These tables are perfectly usable as they are, but for convenience they can be
grouped into a `Database`.  This becomes more important when serialising them::

    db = Database()
    db.add(Book)
    db.add(Author)

`Database.add` can also be used as a class decorator, so the complete code
becomes::

    db = Database()

    @db.add
    class Book(Table):
        name = Field()
        author = Field(index=True)

        def validate(self):
            assert isinstance(self.refno, int)
            assert isinstance(self.name, str)
            assert isinstance(self.author, str)

    @db.add
    class Author(Table):
        surname = Field(unique=True)
        initials = Field(unique=True, default='')
        nationality = Field()
        books = Join(Book.author)


Adding records
--------------

Now that the database is set up, we can add some records to it::

    dickens = Author(surname='Dickens', initials='C', nationality='British')
    tolkien = Author(surname='Tolkien', initials='JRR', nationality='South African')
    pratchett = Author(surname='Pratchett', initials='T', nationality='British')
    Book(name='Wyrd Sisters', author=pratchett)
    Book(name='The Hobbit', author=tolkien)
    Book(name='Lord of the Rings', author=tolkien)
    Book(name='Great Expectations', author=dickens)
    Book(name='David Copperfield', author=dickens)
    Book(name='Guards, guards', author=pratchett)


Queries
-------

Queries are constructed by comparing and combining fields.  The following
examples show how to extract various bit of information from the database.

.. seealso:: :doc:`queries`

1.  Listing all records in a table is as simple as iterating over it, so
    generator expressions can be used to extract a list of fields.  For
    example, to get a sorted list of author's surnames::

        >>> sorted(a.surname for a in Author)
        ['Dickens', 'Pratchett', 'Tolkien']

2.  Records can be queried based on their field values.  For example,
    to list all South African authors::

        >>> for a in (Author.nationality == 'South African'):
        ...     print(a.surname)
        Tolkien

3.  Queries can be combined and nested, so to get all books by authors who's
    initials are in the first half of the alphabet::

        books = Books.authors & (Author.initials <= 'L')