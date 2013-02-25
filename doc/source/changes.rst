.. currentmodule:: norman


What's New
==========

This file lists new features and major changes to **Norman**.  For a detailed
changelog, see the mercurial log.

Norman-0.7.2
------------

*Release Date: 2012-02-25*

-   Support for Python 2.6 added.
-   Fixed Issue #1: Using ``uidname=None`` in `serialise.Sqlite` does not
    behave as documented.
-   Documentation updated, and installation instructions added.


Norman-0.7.1
------------

*Release Date: 2012-02-12*

-   `Query.table` exposed, resulting in a major implementation change in
    `Query.add`.  This function now exists for all queries, but raises
    an error if called when it cannot be used.
-   `Query.add` can now be used for queries of whole tables.
-   Add `AutoDatabase` and `AutoTable` classes.
-   Make `Field.readonly` and `Field.unique` mutable.
-   Allow `Field` definitions to be copied to another `Table`.
-   Add `Database.delete` method.
-   Allow a `None` return value from `serialise.Reader.create_record`.
-   Fix issue in python2 where uuids cannot be converted to strings.
-   Documentation updated.


Norman-0.7.0
------------

*Release Date: 2012-12-14*

-   Many internal changes in the way data is stored and indexed, centred
    around the introduction of two new classes, `Store` and `Index`.
-   All fields are now automatically indexed.  As a results the *index*
    parameter to `Field` objects falls away, and a new *key* argument
    is introduced.
-   `Table` objects have a new attribute, ~`Table._store`, which refers
    to the `Store` used for the table.  This may be changed when the
-   The `serialise` framework has been completely overhauled and the API
    simplified.  Extensive changes in this module.
-   Add a new `~serialise.CSV` serialiser.
-   Add `validate.map` validator to convert values.
-   Improved the string representation of `Query` and `Field` instances.
-   Deprecated functionality removed


Norman-0.6.2
------------

*Release Date: 2012-09-03*

-   Add built-in support for many-to-many joins.
-   Hooks added to `Table` to allow more control over validation.
-   Add `Query.field`, allowing queries to traverse tables.
-   Add `Query.add`, allowing records to be created based on query criteria.
-   Add a return value when calling `Query` objects.
-   `Field` level validation added, including some validator factories.
-   Add `validate.todatetime`, `validate.todate` and `validate.totime`.
-   Deprecated the `!tools` module.


Norman-0.6.1
------------

*Release Date: 2012-07-12*

-   New serialiser framework added, based on `serialise.Serialiser`.
    A sample serialiser, `serialise.Sqlite` is included.
-   `!serialise.Sqlite3` has been deprecated.
-   Documentation overhauled introducing major changes to the documentation
    layout.
-   Add boolean comparisons, `Query.delete` and `Query.one` methods to `Query`.
-   `Table` now supports inheritance by copying its fields.
-   Several changes to implementations, generally to improve performance and
    consistency.


Norman-0.6.0
------------

*Release Date: 2012-06-12*

-   Python 2.6 support by Ilya Kutukov
-   Move serialisation functions to a new serialise module.  This module
    will be expanded and updated in the near future.
-   Add sensible `repr` to `Table` and `NotSet` objects
-   `Query` object added, introducing a new method of querying tables,
    involving `Field` and `Query` comparison operators.
-   `Join` class created, which will replace `!Group` in 0.7.0.
-   `Field.name` and `Field.owner`, which previously existed, have now been
    formalised and documented.
-   `Field.default` is respected when initialising tables
-   `Table._uid` property added for Table objects.
-   Allow `Table.validate_delete` to make changes.
-   Two new `!tools` functions added: `!tools.dtfromiso` and `!tools.reduce2`.
-   `Database.add` method added.
-   Documentation updated to align with docstrings.
-   Fix a bunch of style and PEP8 related issues
-   Minor bugfixes


Norman-0.5.2
------------

*Release Date: 2012-04-20*

-   Fixed failing tests
-   `!Group.add` implemented and documented
-   Missing documentation fixed


Norman-0.5.1
------------

*Release Date: 2012-04-20*

-   Exceptions raised by validation errors are now all ValueError
-   Group object added to represent sub-collections
-   Deletion validation added to tables through `Table.validate_delete`
-   Minor documentation updates
-   Minor bugfixes


Norman-0.5.0
------------

*Release Date: 2012-04-13*

-   First public release, repository imported from private project.
