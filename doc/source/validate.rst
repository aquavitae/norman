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
