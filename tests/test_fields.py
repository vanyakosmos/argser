from argparse import ArgumentParser
from typing import List

import pytest

from argser import Opt
from argser.exceptions import ArgserException


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
    opts = o.make_options('a', 'aa', 'aa_bb')
    assert opts == ['-a', '--aa', '--aa-bb']
    opts = o.make_options('a', 'aa', 'aa_bb', prefix='+', repl=('_', '+'))
    assert opts == ['+a', '+aa', '+aa+bb']


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
        assert o.factory is str
        assert o.nargs is nargs is None

        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=int)
        assert o.type is typ is int
        assert o.factory is int
        assert o.nargs is nargs is None

        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=List[float])
        assert o.type == List[float]
        assert o.factory is typ is float
        assert o.nargs == nargs == '*'

    def test_with_type(self):
        o = Opt(type=int)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is int
        assert o.factory is int
        assert o.nargs is None

        o = Opt(type=List[int])
        o.guess_type_and_nargs(annotation=None)
        assert o.type is List[int]
        assert o.factory is int
        assert o.nargs == '*'

        o = Opt(type=List[int])
        o.guess_type_and_nargs(annotation=int)  # try override type with annotation
        assert o.type is List[int]  # but fail miserably
        assert o.factory is int
        assert o.nargs is None

    def test_with_default(self):
        o = Opt(default=1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is int
        assert o.factory is int
        assert o.nargs is None

        o = Opt(default=1)
        o.guess_type_and_nargs(annotation=float)
        assert o.type is float
        assert o.factory is float
        assert o.nargs is None

        o = Opt(default=[])
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.factory is str
        assert o.nargs == '*'

        o = Opt(default=[])
        o.guess_type_and_nargs(annotation=List[bool])
        assert o.type == List[bool]
        assert o.factory is bool
        assert o.nargs == '*'

        o = Opt(default=[1.1])
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[float]
        assert o.factory is float
        assert o.nargs == '+'

    def test_with_factory(self):
        o = Opt(factory=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.factory('a') == 'A'
        assert o.nargs is None

        # user error: type and factory result mismatch
        o = Opt(factory=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=int)
        assert o.type is int
        assert o.factory('a') == 'A'
        assert o.nargs is None

        o = Opt(factory=lambda x: float(x) + 2.2)
        o.guess_type_and_nargs(annotation=float)
        assert o.type is float
        assert o.factory('1.1') == pytest.approx(3.3)
        assert o.nargs is None

        o = Opt(factory=lambda x: list(map(int, x)))
        o.guess_type_and_nargs(annotation=List[int])
        assert o.type is List[int]
        assert o.factory('123') == [1, 2, 3]
        assert o.nargs == '*'

    def test_with_nargs(self):
        o = Opt(nargs='?')
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.factory is str
        assert o.nargs == '?'

        o = Opt(nargs='*')
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.factory is str
        assert o.nargs == '*'

        o = Opt(nargs='+')
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.factory is str
        assert o.nargs == '+'

        o = Opt(nargs=2)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[str]
        assert o.factory is str
        assert o.nargs == 2

    def test_complex(self):
        o = Opt(type=str, factory=lambda x: x.upper())
        o.guess_type_and_nargs(annotation=None)
        assert o.type is str
        assert o.factory('a') == 'A'
        assert o.nargs is None

        o = Opt(default=1.1, factory=lambda x: float(x) + 1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type is float
        assert o.factory('1.1') == pytest.approx(2.1)
        assert o.nargs is None

        o = Opt('o', type=bool, factory=lambda x: x == 'foo')
        o.guess_type_and_nargs(annotation=None)
        assert o.type is bool
        assert o.factory('foo') is True
        assert o.nargs is None
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o foo'.split()).o is True
        assert p.parse_args('-o bar'.split()).o is False

        o = Opt('o', default=[1, 2], factory=lambda x: int(x) + 1)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[int]
        assert o.factory('1') == 2
        assert o.nargs == '+'
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o 1 2'.split()).o == [2, 3]
        assert p.parse_args('-o 5 1 2'.split()).o == [6, 2, 3]

    def test_list_from_single_value(self):
        o = Opt(
            'o',
            factory=lambda x: [int(e) + 1 for e in list(x)],
            nargs='?',
            default=[-1],
        )
        o.guess_type_and_nargs(annotation=None)
        assert o.type == List[int]
        assert o.factory('123') == [2, 3, 4]
        assert o.nargs == '?'
        p = ArgumentParser()
        o.inject(p)
        assert p.parse_args('-o 123'.split()).o == [2, 3, 4]


def test_pick_factory():
    def foo():
        pass

    assert Opt()._pick_factory(1, 2, foo) is foo
    assert Opt()._pick_factory(1, foo, 2) is foo
    assert Opt()._pick_factory(None) is None
    with pytest.raises(ArgserException):
        Opt()._pick_factory(1, 2, 3)


def test_pretty_format():
    o = Opt(dest='oo', default=1, help="foo")
    o.guess_type_and_nargs(int)
    o.option_names = ['o', 'oo']
    assert o.pretty_format().startswith("Opt(-o, --oo,\n")
