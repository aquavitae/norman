# Copyright (c) 2011 David Townshend
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

from distutils.core import setup
import sys

import norman

version = norman.__version__
author = norman.__author__
description = '''
Norman is a framework for advanced data structures in python using
an database-like approach.  The range of potential applications is wide,
for example in-memory databases, multi-keyed dictionaries or node graphs.
'''

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.0',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Topic :: Database',
    'Topic :: Database :: Database Engines/Servers',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Python Modules'
]


def run_setup(*argv):
    if len(argv) > 0:
        sys.argv = [sys.argv[0]] + list(argv)

    setup(name='norman',
          version=version,
          description=description,
          author=author,
          author_email='aquavitae69@gmail.com',
          url='http://bitbucket.org/aquavitae/norman',
          download_url='http://bitbucket.org/aquavitae/norman/downloads',
          packages=['norman'],
          classifiers=classifiers,
          test_suite='nose.collector'
         )

if __name__ == '__main__':
    run_setup()
