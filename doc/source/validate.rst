.. module:: norman.validate


Validators
==========

This module provides some validators and validator factories, intended mainly
for use in the *validate* parameter of `~norman.Field`\ s.


.. autofunction:: ifset(func)


.. autofunction:: isfalse(func[, default])


.. autofunction:: istrue(func[, default])


.. autofunction:: istype(t[, t2[, t3[, ...]]])


.. autofunction:: map(mapping)


.. autofunction:: settype(t, default)


The following three functions return validators which convert a value to
a `datetime` object using a format string.  See
:ref:`strftime-strptime-behavior` for more information of format strings.

.. autofunction:: todate([fmt])


.. autofunction:: todatetime([fmt])


.. autofunction:: totime([fmt])
