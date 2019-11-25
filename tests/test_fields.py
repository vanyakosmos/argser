from argparse import ArgumentParser
from typing import List

import pytest

from argser import Opt
from argser.exceptions import ArgserException
from tests.utils import params


@pytest.mark.parametrize(
    "opt, repl, expected",
    [
        ('aa', ('_', '-'), 'aa'),
        ('aa_aa', ('_', '-'), 'aa-aa'),
        ('aa__bb_cc', ('_', '+'), 'aa++bb+cc'),
        ('a-b-c', ('-', '_'), 'a_b_c'),
        ('a_b_c', None, 'a_b_c'),
    ],
)
def test_opt_replace(opt, repl, expected):
    o = Opt()
    assert o._replace(opt, repl) == expected


@pytest.mark.parametrize(
    "opt, prefix, expected",
    [
        ('aa', '', 'aa'),
        ('aa', '-', '-aa'),
        ('aa', '--', '--aa'),
        ('a', '--', '-a'),
        ('+aa', '--', '+aa'),
    ],
)
def test_opt_prefix(opt, prefix, expected):
    o = Opt()
    assert o._prefix(opt, prefix) == expected


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        (dict(), ['-a', '--aa', '--aa-bb']),
        (dict(prefix='+', repl=('_', '+')), ['+a', '+aa', '+aa+bb']),
    ],
)
def test_set_options(kwargs, expected):
    opts = Opt().make_options('a', 'aa', 'aa_bb', **kwargs)
    assert opts == expected


@pytest.mark.parametrize(
    "p, expected",
    [
        (params('a', 'aa', 'aa_bb'), ['--no-a', '--no-aa', '--no-aa-bb']),
        (params('++aa'), ['++no-aa']),
        (params('++aa', prefix=''), ['++no-aa']),
        (params('++aa', prefix=''), ['++no-aa']),
        (params('++aa', repl=('_', '+')), ['++no+aa']),
        (params('aa', prefix='+'), ['+no-aa']),
        (params('aa', prefix='+', repl=('_', '+')), ['+no+aa']),
    ],
)
def test_no_options(p, expected):
    assert Opt(*p.args, **p.kwargs).no_options == expected


@pytest.mark.parametrize(
    "p, dest, options, metavar",
    [
        (params(), None, [], None),
        (params('bar', dest='foo'), 'foo', {'--foo', '--bar'}, 'F'),
        (params('bar', 'baz'), None, {'--bar', '--baz'}, None),
    ],
)
def test_init(p, dest, options, metavar):
    o = Opt(*p.args, **p.kwargs)
    assert o.dest == dest
    assert set(o.options) == set(options)
    assert o.metavar == metavar


def test_with_new_dest():
    o = Opt('bar', 'baz')
    o.set_dest('foo')
    assert o.dest == 'foo'
    assert set(o.options) == {'--foo', '--bar', '--baz'}
    assert o.metavar == 'F'


def test_init_with_dest():
    o = Opt(dest='foo')
    assert o.dest == 'foo'
    assert o.options == ['--foo']
    assert o.metavar == 'F'
    o.set_dest('bar')  # dest already specified
    assert o.dest == 'foo'
    assert o.options == ['--foo']
    assert o.metavar == 'F'


class TestGuessType:
    @pytest.mark.parametrize(
        "annotation, out_type, opt_type, opt_factory, opt_nargs",
        [
            (None, str, str, str, None),
            (int, int, int, int, None),
            (List[float], float, List[float], float, '*'),
        ],
    )
    def test_simple(self, annotation, out_type, opt_type, opt_factory, opt_nargs):
        o = Opt()
        typ, nargs = o.guess_type_and_nargs(annotation=annotation)
        assert typ == out_type
        assert o.type == opt_type
        assert o.factory == opt_factory
        assert o.nargs == nargs == opt_nargs

    @pytest.mark.parametrize(
        "key_type, annotation, opt_type, opt_factory, opt_nargs",
        [
            (int, None, int, int, None),
            (List[int], None, List[int], int, '*'),
            (List[int], int, List[int], int, None),  # try override type with annotation
        ],
    )
    def test_with_type(self, key_type, annotation, opt_type, opt_factory, opt_nargs):
        o = Opt(type=key_type)
        o.guess_type_and_nargs(annotation=annotation)
        assert o.type == opt_type
        assert o.factory == opt_factory
        assert o.nargs == opt_nargs

    @pytest.mark.parametrize(
        "default, annotation, opt_type, opt_factory, opt_nargs",
        [
            (1, None, int, int, None),
            (1, float, float, float, None),
            ([], None, List[str], str, '*'),
            ([], List[bool], List[bool], bool, '*'),
            ([1.1], None, List[float], float, '+'),
        ],
    )
    def test_with_default(self, default, annotation, opt_type, opt_factory, opt_nargs):
        o = Opt(default=default)
        o.guess_type_and_nargs(annotation=annotation)
        assert o.type == opt_type
        assert o.factory == opt_factory
        assert o.nargs == opt_nargs

    @pytest.mark.parametrize(
        "factory, annotation, opt_type, opt_nargs, value, expected",
        [
            (str.upper, None, str, None, 'a', 'A'),
            # user error, type and factory result mismatch:
            (str.upper, int, int, None, 'a', 'A',),
            (lambda x: float(x) + 2.2, float, float, None, '1.1', pytest.approx(3.3)),
            (lambda x: list(map(int, x)), List[int], List[int], '*', '123', [1, 2, 3]),
        ],
    )
    def test_with_factory(
        self, factory, annotation, opt_type, opt_nargs, value, expected
    ):
        o = Opt(factory=factory)
        o.guess_type_and_nargs(annotation=annotation)
        assert o.type == opt_type
        assert o.nargs == opt_nargs
        assert o.factory(value) == expected

    @pytest.mark.parametrize(
        "nargs, opt_type, opt_factory, opt_nargs",
        [
            ('?', str, str, '?'),
            ('*', List[str], str, '*'),
            ('+', List[str], str, '+'),
            (2, List[str], str, 2),
        ],
    )
    def test_with_nargs(self, nargs, opt_type, opt_factory, opt_nargs):
        o = Opt(nargs=nargs)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == opt_type
        assert o.factory == opt_factory
        assert o.nargs == opt_nargs

    # fmt: off
    @pytest.mark.parametrize(
        "opt_kwargs, opt_type, opt_nargs, factory_value, factory_expected, args, expected",
        [
            (dict(type=str, factory=lambda x: x.upper()), str, None, 'a', 'A', None, None),
            (dict(default=1.1, factory=lambda x: float(x) + 1), float, None, '1.1', pytest.approx(2.1), None, None),
            (dict(type=bool, factory=lambda x: x == 'foo'), bool, None, 'foo', True, '-o foo', True),
            (dict(type=bool, factory=lambda x: x == 'foo'), bool, None, 'foo', True, '-o bar', False),
            (dict(default=[1, 2], factory=lambda x: int(x) + 1), List[int], '+', '1', 2, '-o 1 2', [2, 3]),
            (dict(default=[1, 2], factory=lambda x: int(x) + 1), List[int], '+', '1', 2, '-o 5 1 2', [6, 2, 3]),
        ],
    )
    def test_complex(self, opt_kwargs, opt_type, opt_nargs, factory_value, factory_expected, args, expected):
        o = Opt('o', **opt_kwargs)
        o.guess_type_and_nargs(annotation=None)
        assert o.type == opt_type
        assert o.nargs == opt_nargs
        assert o.factory(factory_value) == factory_expected
        if args and expected:
            p = ArgumentParser()
            o.inject(p)
            assert p.parse_args(args.split()).o == expected
    # fmt: on

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
