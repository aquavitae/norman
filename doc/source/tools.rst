.. module:: norman.tools

.. testsetup:: tools

    from norman.tools import *


Tools
=====

Some useful tools for use with Norman are provided in `norman.tools`.


.. function:: dtfromiso(iso)

    Return a `datetime` object from a string representation in ISO format.

    The database serialisation procedures store `datetime` objects as strings,
    in ISO format.  This provides an easy way to reverse this.
    `~datetime.datetime`, `~datetime.date` and `~datetime.time` objects are
    all supported.

    Note that this assumes naive datetimes.

    .. doctest:: tools

        >>> import datetime
        >>> dt = datetime.date(2001, 12, 23)
        >>> isodt = str(dt)
        >>> dtfromiso(isodt)
        datetime.date(2001, 12, 23)


.. function:: float2(s[, default=0.0])

    Convert *s* to a float, returning *default* if it cannot be converted.

    .. doctest:: tools

        >>> float2('33.4', 42.5)
        33.4
        >>> float2('cannot convert this', 42.5)
        42.5
        >>> float2(None, 0)
        0
        >>> print(float2('default does not have to be a float', None))
        None


.. function:: int2(s[, default=0])

    Convert *s* to an int, returning *default* if it cannot be converted.

    .. doctest:: tools

        >>> int2('33', 42)
        33
        >>> int2('cannot convert this', 42)
        42
        >>> print(int2('default does not have to be an int', None))
        None


.. function:: reduce2(func, seq, default)

    Similar to `functools.reduce`, but return *default* if *seq* is empty.

    The third argument to `functools.reduce` is an *initializer*, which
    essentially acts as the first item in *seq*.  In this function,
    *default* is returned if *seq* is empty, otherwise it is ignored.

    .. doctest:: tools

        >>> reduce2(lambda a, b: a + b, [1, 2, 3], 4)
        6
        >>> reduce2(lambda a, b: a + b, [], 'default')
        'default'
