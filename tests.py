from typing import List

import pytest

from argser import (
    Arg, PosArg, _make_shortcuts, _read_args, is_list_like_type, parse_args, sub_command, _make_parser,
    ColoredHelpFormatter
)


def test_simple():
    class Args:
        a: int
        bb = 'foo'
        ccc_ddd = [1.1, 2.2]
        e: List[bool] = []

    args = parse_args(Args, '')
    assert args.a is None
    assert args.bb == 'foo'
    assert args.ccc_ddd == [1.1, 2.2]
    assert args.e == []

    args = parse_args(Args, '-a 2 --bb "foo bar" --ccc_ddd 3.3 4.4 -e 1 0')
    assert args.a == 2
    assert args.bb == 'foo bar'
    assert args.ccc_ddd == [3.3, 4.4]
    assert args.e == [True, False]


def test_sub_command():
    class Args:
        a: int
        bb = 'foo'
        ccc_ddd = [1.1, 2.2]

        class SubArgs:
            d: List[int]
            ee = ''

        sub = sub_command(SubArgs)

    args = parse_args(Args, '')
    assert args.a is None
    assert args.bb == 'foo'
    assert args.ccc_ddd == [1.1, 2.2]
    assert args.sub is None

    args = parse_args(Args, '-a 1 --bb "foo bar" sub -d 1 2 --ee baz')
    assert args.a == 1
    assert args.bb == 'foo bar'
    assert args.ccc_ddd == [1.1, 2.2]
    assert args.sub.d == [1, 2]
    assert args.sub.ee == 'baz'


def test_complex_args():
    class Args:
        a: int = Arg()
        bb: str = Arg(default='foo')
        ccc_ddd: List[float] = Arg(default=[1.1, 2.2])
        e: List[bool] = Arg(default=[])

    args = parse_args(Args, '')
    assert args.a is None
    assert args.bb == 'foo'
    assert args.ccc_ddd == [1.1, 2.2]
    assert args.e == []

    args = parse_args(Args, '-a 2 --bb "foo bar" --ccc_ddd 3.3 4.4 -e 1 0')
    assert args.a == 2
    assert args.bb == 'foo bar'
    assert args.ccc_ddd == [3.3, 4.4]
    assert args.e == [True, False]


def test_positional_args():
    class Args:
        a = 1
        bb: str = PosArg()
        ccc: List[int] = PosArg()
        d = True

    args = parse_args(Args, '"foo bar" 1 2 -a 5 --no-d')
    assert args.a == 5
    assert args.bb == 'foo bar'
    assert args.ccc == [1, 2]
    assert args.d is False


def test_make_shortcuts():
    a = Arg(dest='a', type_=str)
    aa = Arg(dest='aa', type_=str)
    bc = Arg(dest='bc', type_=str)
    ab_cd = Arg(dest='ab_cd', type_=str)
    ab_cde = Arg(dest='ab_cde', type_=str)
    bcd = PosArg(dest='bcd', type_=str, aliases=('foo',))

    _make_shortcuts([a, aa, bc, ab_cd, ab_cde, bcd])
    assert a.dest == 'a' and a.aliases == ()  # already short name
    assert aa.dest == 'aa' and aa.aliases == ('a2',)  # name 'a' already exists
    assert bc.dest == 'bc' and bc.aliases == ('b',)
    assert ab_cd.dest == 'ab_cd' and ab_cd.aliases == ('ac',)
    assert ab_cde.dest == 'ab_cde' and ab_cde.aliases == ('ac2',)
    assert bcd.dest == 'bcd' and bcd.aliases == ('foo',)  # alias was already defined and override is false


def test_parse_str():
    class Args:
        a: str
        b = 'b'
        c = None

    args = parse_args(Args, '')
    assert args.a is None
    assert args.b == 'b'
    assert args.c is None

    args = parse_args(Args, '-a 1 -b 2 -c 3')
    assert args.a == '1'
    assert args.b == '2'
    assert args.c == '3'

    args = parse_args(Args, '-a "foo bar"')
    assert args.a == 'foo bar'


def test_parse_int():
    class Args:
        a: int
        b = 5

    args = parse_args(Args, [])
    assert args.a is None
    assert args.b == 5

    args = parse_args(Args, '-a 1 -b -1')
    assert args.a == 1
    assert args.b == -1

    with pytest.raises(SystemExit):
        parse_args(Args, '-a a')


def test_parse_float():
    class Args:
        a: float
        b = 5.2

    args = parse_args(Args, [])
    assert args.a is None
    assert args.b == 5.2

    args = parse_args(Args, '-a 1.1 -b -1.1')
    assert args.a == 1.1
    assert args.b == -1.1

    with pytest.raises(SystemExit):
        parse_args(Args, '-a a')


def test_parse_bool():
    class Args:
        a: bool
        b = True
        c = False

    args = parse_args(Args, [])
    assert args.a is None
    assert args.b is True
    assert args.c is False

    args = parse_args(Args, '-a', bool_flag=True)
    assert args.a is True
    args = parse_args(Args, '--no-a', bool_flag=True)
    assert args.a is False
    args = parse_args(Args, '-no-a', bool_flag=True, one_dash=True)
    assert args.a is False

    args = parse_args(Args, '-no-b -c', bool_flag=True, one_dash=True)
    assert args.b is False
    assert args.c is True

    args = parse_args(Args, '-a 1 -b false -c yes', bool_flag=False)
    assert args.a is True
    assert args.b is False
    assert args.c is True

    with pytest.raises(SystemExit):
        parse_args(Args, '-a a', bool_flag=False)


@pytest.fixture()
def list_args():
    class Args:
        a: list
        b: List
        c: List[int]
        d: List[bool] = []
        e = [1.1, 2.2]

    return lambda args='': parse_args(Args, args)


def test_parse_list_default(list_args):
    args = list_args('')
    assert args.a is None
    assert args.b is None
    assert args.c is None
    assert args.d == []
    assert args.e == [1.1, 2.2]


def test_parse_list_complex(list_args):
    args = list_args('-a 1 a "a b" -b b -c 1 -d true 0 -e 1.0 2.2')
    assert args.a == ['1', 'a', 'a b']
    assert args.b == ['b']
    assert args.c == [1]
    assert args.d == [True, False]
    assert args.e == [1.0, 2.2]


def test_parse_list_nargs(list_args):
    args = list_args('-a -b -c -d -e 1.0')
    assert args.a == []
    assert args.b == []
    assert args.c == []
    assert args.d == []
    assert args.e == [1.0]

    (a, b, c, d, e), sub_commands = _read_args(args.__class__)
    # a, b, c, d, e = args_as_list(args)
    assert a.nargs == '*'
    assert b.nargs == '*'
    assert c.nargs == '*'
    assert d.nargs == '*'
    assert e.nargs == '+'

    # -e has default value with >0 elements and that's why nargs is + instead of *
    with pytest.raises(SystemExit):
        list_args('-a 1 -e')


def test_parse_list_types(list_args):
    (a, b, c, d, e), sub_commands = _read_args(list_args().__class__)
    assert a.type is str
    assert b.type is str
    assert c.type is int
    assert d.type is bool
    assert e.type is float


def test_prints():
    # just check that they work
    class Args:
        a = '1'
        b = 1
        c = 1.0
        d = True
        e = Arg(default=[1, 1], help='foo bar')

    args = parse_args(Args, [], show=True)
    assert args.a == '1'

    args = parse_args(Args, [], show='table')
    assert args.a == '1'

    args, sub_commands = _read_args(Args)
    parser = _make_parser('root', args, sub_commands, formatter_class=ColoredHelpFormatter)
    help = parser.format_help()
    print(help)
    assert help


def test_override():
    class Args:
        aa = Arg(default='foo', one_dash=True)
        bb = Arg(default='bar', one_dash=False)
        cc = 'baz'

    args = parse_args(Args, '-aa foo1 --bb bar1 -cc baz1', override=False, one_dash=True)
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    args = parse_args(Args, '--aa foo1 --bb bar1 --cc baz1', override=True, one_dash=False)
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    with pytest.raises(SystemExit):
        parse_args(Args, '-aa foo1 --bb bar1 -cc baz1', override=True, one_dash=False)


def test_is_list_typing():
    assert is_list_like_type(List)
    assert is_list_like_type(List[str])
    assert is_list_like_type(List[int])
    assert not is_list_like_type(list)
    assert not is_list_like_type(str)
