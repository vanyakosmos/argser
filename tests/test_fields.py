from argparse import ArgumentParser
from typing import List

import pytest

from argser import Opt


def test_opt_replace():
    o = Opt()
    assert o._replace('aa', ('_', '-')) == 'aa'
    assert o._replace('aa_aa', ('_', '-')) == 'aa-aa'
    assert o._replace('aa__bb_cc', ('_', '+')) == 'aa++bb+cc'
    assert o._replace('a-b-c', ('-', '_')) == 'a_b_c'
    assert o._replace('a_b_c', None) == 'a_b_c'


def test_opt_prefix():
    o = Opt()
    assert o._prefix('aa', '') == 'aa'
    assert o._prefix('aa', '-') == '-aa'
    assert o._prefix('aa', '--') == '--aa'
    assert o._prefix('a', '--') == '-a'
    assert o._prefix('+aa', '--') == '+aa'


def test_set_options():
    o = Opt()
    assert o.make_options('a', 'aa', 'aa_bb') == ['-a', '--aa', '--aa-bb']
    assert o.make_options('a', 'aa', 'aa_bb', prefix='+', repl=('_', '+')) == ['+a', '+aa', '+aa+bb']


def test_no_options():
    assert Opt('a', 'aa', 'aa_bb').no_options == ['--no-a', '--no-aa', '--no-aa-bb']
    assert Opt('++aa').no_options == ['++no-aa']
    assert Opt('++aa', prefix='').no_options == ['++no-aa']
    assert Opt('++aa', prefix='').no_options == ['++no-aa']
    assert Opt('++aa', repl=('_', '+')).no_options == ['++no+aa']
    assert Opt('aa', prefix='+').no_options == ['+no-aa']
    assert Opt('aa', prefix='+', repl=('_', '+')).no_options == ['+no+aa']


def test_init():
    o = Opt()
    assert o.dest is None
    assert o.options == []

    o = Opt(dest='foo')
    assert o.dest == 'foo'
    assert o.options == ['--foo']
    assert o.metavar == 'F'
    o.set_dest('bar')  # dest already specified
    assert o.dest == 'foo'
    assert o.options == ['--foo']
    assert o.metavar == 'F'

    o = Opt('bar', dest='foo')
    assert o.dest == 'foo'
    assert set(o.options) == {'--foo', '--bar'}
    assert o.metavar == 'F'

    o = Opt('bar', 'baz')
    assert o.dest is None
    assert o.options == ['--bar', '--baz']
    assert o.metavar is None

    o = Opt('bar', 'baz')
    o.set_dest('foo')
    assert o.dest == 'foo'
    assert set(o.options) == {'--foo', '--bar', '--baz'}
    assert o.metavar == 'F'


class TestGuessType:
    def test_simple(self):
        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=None)
        assert o.type is typ is str
        assert o.constructor is str
        assert o.nargs is nargs is None

        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=int)
        assert o.type is typ is int
        assert o.constructor is int
        assert o.nargs is nargs is None

        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=List[float])
        assert o.type == List[float]
        assert o.constructor is typ is float
        assert o.nargs is nargs is '*'

    def test_with_type(self):
        o = Opt(type=int)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is int
        assert o.constructor is int
        assert o.nargs is None

        o = Opt(type=List[int])
        o.guess_type_and_nargs(annotation=None)
        assert o.type is List[int]
        assert o.constructor is int
        assert o.nargs == '*'

        o = Opt(type=List[int])
        o.guess_type_and_nargs(annotation=int)  # try override type with annotation
        assert o.type is List[int]  # but fail miserably
        assert o.constructor is int
        assert o.nargs is None

    def test_with_default(self):
        o = Opt(default=1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is int
        assert o.constructor is int
        assert o.nargs is None

        o = Opt(default=1)
        o.guess_type_and_nargs(annotation=float)
        assert o.type is float
        assert o.constructor is float
        assert o.nargs is None

        o = Opt(default=[])
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.constructor is str
        assert o.nargs == '*'

        o = Opt(default=[])
        o.guess_type_and_nargs(annotation=List[bool])
        assert o.type == List[bool]
        assert o.constructor is bool
        assert o.nargs == '*'

        o = Opt(default=[1.1])
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[float]
        assert o.constructor is float
        assert o.nargs == '+'

    def test_with_constructor(self):
        o = Opt(constructor=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.constructor('a') == 'A'
        assert o.nargs is None

        # user error: type and constructor result mismatch
        o = Opt(constructor=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=int)
        assert o.type is int
        assert o.constructor('a') == 'A'
        assert o.nargs is None

        o = Opt(constructor=lambda x: float(x) + 2.2)
        o.guess_type_and_nargs(annotation=float)
        assert o.type is float
        assert o.constructor('1.1') == pytest.approx(3.3)
        assert o.nargs is None

        o = Opt(constructor=lambda x: list(map(int, x)))
        o.guess_type_and_nargs(annotation=List[int])
        assert o.type is List[int]
        assert o.constructor('123') == [1, 2, 3]
        assert o.nargs == '*'

    def test_with_nargs(self):
        o = Opt(nargs='?')
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.constructor is str
        assert o.nargs == '?'

        o = Opt(nargs='*')
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.constructor is str
        assert o.nargs == '*'

        o = Opt(nargs='+')
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.constructor is str
        assert o.nargs == '+'

        o = Opt(nargs=2)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.constructor is str
        assert o.nargs == 2

    def test_complex(self):
        o = Opt(type=str, constructor=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.constructor('a') == 'A'
        assert o.nargs is None

        o = Opt(default=1.1, constructor=lambda x: float(x) + 1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is float
        assert o.constructor('1.1') == pytest.approx(2.1)
        assert o.nargs is None

        o = Opt('o', type=bool, constructor=lambda x: x == 'foo')
        o.guess_type_and_nargs(annotation=None)
        assert o.type is bool
        assert o.constructor('foo') is True
        assert o.nargs is None
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o foo'.split()).o is True
        assert p.parse_args('-o bar'.split()).o is False

        o = Opt('o', default=[1, 2], constructor=lambda x: int(x) + 1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[int]
        assert o.constructor('1') == 2
        assert o.nargs == '+'
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o 1 2'.split()).o == [2, 3]
        assert p.parse_args('-o 5 1 2'.split()).o == [6, 2, 3]

    def test_list_from_single_value(self):
        o = Opt('o', constructor=lambda x: [int(e) + 1 for e in list(x)], nargs='?', default=[-1])
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[int]
        assert o.constructor('123') == [2, 3, 4]
        assert o.nargs == '?'
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o 123'.split()).o == [2, 3, 4]
