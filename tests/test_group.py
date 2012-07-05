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

from __future__ import with_statement
from __future__ import unicode_literals

from nose.tools import assert_raises
from norman import Field, Group, Table


class T(Table):
    oid = Field(unique=True)
    name = Field()


def test_init():
    'Test a group definition'
    class Object(object): pass
    g = Group(Object)
    assert g.table is Object


def test_init_matcher():
    Group(int, lambda: None)

def test_init_kwargs():
    Group(int, a=1, b=2)


class TestAPI(object):

    def setup(self):
        self.g = Group(T, name='a')
        self.r = [T(oid=oid, name=name) for oid, name in enumerate('abacadb')]

    def teardown(self):
        T.delete()

    def test_meta_len(self):
        assert len(self.g) == 3

    def test_meta_contains(self):
        assert self.r[0] in self.g

    def test_meta_contains_false(self):
        class Other(Table):
            name = Field()
        other = Other(name='a')
        assert other not in self.g

    def test_meta_iter(self):
        r = set(iter(self.g))
        assert r == set([self.r[0], self.r[2], self.r[4]])

    def test_contains_true(self):
        assert self.g.contains(oid=0)

    def test_contains_false(self):
        assert not self.g.contains(oid=1)

    def test_get_noargs(self):
        assert set(self.g.get()) == set([self.r[0], self.r[2], self.r[4]])

    def test_get_args(self):
        assert set(self.g.get(oid=0)) == set([self.r[0]])

    def test_iter_noargs(self):
        assert set(self.g.iter()) == set([self.r[0], self.r[2], self.r[4]])

    def test_iter_args(self):
        assert set(self.g.iter(oid=0)) == set([self.r[0]])

    def test_delete_noargs(self):
        self.g.delete()
        assert set(T) == set([self.r[1], self.r[3], self.r[5], self.r[6]])

    def test_delete_args(self):
        self.g.delete(oid=0)
        assert set(T) == set(self.r[1:])

    def test_delete_records(self):
        self.g.delete(self.r[0])
        assert set(T) == set(self.r[1:])

    def test_delete_fails(self):
        with assert_raises(ValueError):
            self.g.delete(self.r[1])
        assert set(T) == set(self.r)

    def test_add(self):
        r = self.g.add(oid= -1)
        assert isinstance(r, T)
        assert r.oid == -1
        assert r.name == 'a'
        assert r in T


def test_in_class():
    'Test usage in an owning class'
    class Child(Table):
        parent = Field()

    class Parent(Table):
        children = Group(Child, lambda s: {'parent': s})

    p = Parent()
    a = Child(parent=p)
    result = set(p.children)
    assert result == set([a])
