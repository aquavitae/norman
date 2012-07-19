.. module:: norman.validate


Validators
==========

.. function:: ifset(func)

    Return ``func(value)`` if *value* is not `NotSet, otherwise return `NotSet`.

    This is normally used as a wrapper around another validator to permit
    `NotSet` values to pass.  For example::

        >>> validator = ifset(istype(float))
        >>> validator(4.3)
        4.3
        >>> validator(NotSet)
        NotSet
        >>> validator(None)
        Traceback (most recent call last):
            ...
        TypeError: None


.. function:: isfalse(func[, default])

    Return a `Field` validator which passes if *func* returns `False`.

    :param func:     A callable which returns `False` if the value passes.
    :param default:  The value to return if *func* returns `True`.  If this is
                     omitted, an exception is raised.


.. function:: istrue(func[, default])

    Return a `Field` validator which passes if *func* returns `True`.

    :param func:     A callable which returns `True` if the value passes.
    :param default:  The value to return if *func* returns `False`.  If this is
                     omitted, an exception is raised.


.. function:: istype(t[, t2[, t3[, ...]]])

    Return a `Field` validator which raises an exception on an invalid type.

    :param t: The expected type, or types.


.. function:: settype(t, default)

    Return a `Field` validator which converts the value to a type

    :param t:       The required type.
    :param default: If the value cannot be converted, then use this value
                    instead.


.. function:: todate([fmt])

    Return a validator which converts a string to a `datetime.date`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.date.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *date*
    component is returned.  If it is a `datetime.date` it is returned
    unchanged.

    The return value is always a `datetime.date` object.  If the value
    cannot be converted an exception is raised.


.. function:: todatetime([fmt])

    Return a validator which converts a string to a `datetime.datetime`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.datetime.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime` it is
    returned unchanged.  If it is a `datetime.date` or `datetime.time`,
    it is converted to a `datetime.datetime`, replacing missing the missing
    information with ``1900-1-1`` or ``00:00:00``.

    The return value is always a `datetime.datetime` object.  If the value
    cannot be converted an exception is raised.


.. function:: totime([fmt])

    Return a validator which converts a string to a `datetime.time`.

    If *fmt* is omitted, the ISO representation used by
    `datetime.time.__str__` is used, otherwise it should be a format
    string for `datetime.strptime`.

    If the value passed to the validator is a `datetime.datetime`, the *time*
    component is returned.  If it is a `datetime.time` it is returned
    unchanged.

    The return value is always a `datetime.time` object.  If the value
    cannot be converted an exception is raised.
