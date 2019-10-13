from typing import List

import pytest

from arse import ArgsParser, Argument, PosArgument, Command


def test_make_shortcust():
    class Args(ArgsParser):
        a: int
        aa: int
        bc: int
        ab_cd: int
        ab_cde: int
        bcd = Argument(aliases=('foo',))

    args = Args(shortcuts=True, override=False)
    a, aa, bc, ab_cd, ab_cde, bcd = args.args_
    assert a.dest == 'a' and a.aliases == ()  # already short name
    assert aa.dest == 'aa' and aa.aliases == ('a2',)  # name 'a' already exists
    assert bc.dest == 'bc' and bc.aliases == ('b',)
    assert ab_cd.dest == 'ab_cd' and ab_cd.aliases == ('ac',)
    assert ab_cde.dest == 'ab_cde' and ab_cde.aliases == ('ac2',)
    assert bcd.dest == 'bcd' and bcd.aliases == ('foo',)  # alias was already defined and override is false


def test_parse_str():
    class Args(ArgsParser):
        a: str
        b = 'b'
        c = None

    args = Args().parse([])
    assert args.a is None
    assert args.b == 'b'
    assert args.c is None

    args = Args().parse('-a 1 -b 2 -c 3')
    assert args.a == '1'
    assert args.b == '2'
    assert args.c == '3'

    args = Args().parse('-a "foo bar"')
    assert args.a == 'foo bar'


def test_parse_int():
    class Args(ArgsParser):
        a: int
        b = 5

    args = Args().parse([])
    assert args.a is None
    assert args.b == 5

    args = Args().parse('-a 1 -b -1')
    assert args.a == 1
    assert args.b == -1

    with pytest.raises(SystemExit):
        Args().parse('-a a')


def test_parse_float():
    class Args(ArgsParser):
        a: float
        b = 5.2

    args = Args().parse([])
    assert args.a is None
    assert args.b == 5.2

    args = Args().parse('-a 1.1 -b -1.1')
    assert args.a == 1.1
    assert args.b == -1.1

    with pytest.raises(SystemExit):
        Args().parse('-a a')


def test_parse_bool():
    class Args(ArgsParser):
        a: bool
        b = True
        c = False

    args = Args().parse([])
    assert args.a is None
    assert args.b is True
    assert args.c is False

    args = Args(bool_flag=True).parse('-a')
    assert args.a is True
    args = Args(bool_flag=True).parse('--no-a')
    assert args.a is False
    args = Args(bool_flag=True, one_dash=True).parse('-no-a')
    assert args.a is False

    args = Args(bool_flag=True, one_dash=True).parse('-no-b -c')
    assert args.b is False
    assert args.c is True

    args = Args(bool_flag=False).parse('-a 1 -b false -c yes')
    assert args.a is True
    assert args.b is False
    assert args.c is True

    with pytest.raises(SystemExit):
        Args(bool_flag=False).parse('-a a')


@pytest.fixture()
def list_args():
    class Args(ArgsParser):
        a: list
        b: List
        c: List[int]
        d: List[bool] = []
        e = [1.1, 2.2]

    return Args()


def test_parse_list_default(list_args: ArgsParser):
    args = list_args.parse([])
    assert args.a is None
    assert args.b is None
    assert args.c is None
    assert args.d == []
    assert args.e == [1.1, 2.2]


def test_parse_list_complex(list_args: ArgsParser):
    args = list_args.parse('-a 1 a "a b" -b b -c 1 -d true 0 -e 1.0 2.2')
    assert args.a == ['1', 'a', 'a b']
    assert args.b == ['b']
    assert args.c == [1]
    assert args.d == [True, False]
    assert args.e == [1.0, 2.2]


def test_parse_list_nargs(list_args: ArgsParser):
    args = list_args.parse('-a -b -c -d -e 1.0')
    assert args.a == []
    assert args.b == []
    assert args.c == []
    assert args.d == []
    assert args.e == [1.0]

    a, b, c, d, e = list_args.args_
    assert a.nargs == '*'
    assert b.nargs == '*'
    assert c.nargs == '*'
    assert d.nargs == '*'
    assert e.nargs == '+'

    # -e has default value with >0 elements and that's why nargs is + instead of *
    with pytest.raises(SystemExit):
        list_args.parse('-a 1 -e')


def test_parse_list_types(list_args: ArgsParser):
    a, b, c, d, e = list_args.args_
    assert a.type is str
    assert b.type is str
    assert c.type is int
    assert d.type is bool
    assert e.type is float


def test_command():
    class Args(ArgsParser):
        a: str
        sub1 = Command()
        b: int = None
        c = 3
        sub2 = Command()
        d: bool = None
        e = None

    args = Args().parse('-a "foo bar" sub1')
    assert args.sub == 'sub1'
    assert args.a == 'foo bar'

    args = Args().parse('sub1 -b 1 -c 3')
    assert args.sub == 'sub1'
    assert args.b == 1
    assert args.c == 3.0

    args = Args().parse('sub2 -d -e 3')
    assert args.sub == 'sub2'
    assert args.d is True
    assert args.e == '3'


def test_positional_argument():
    class Args(ArgsParser):
        a: str = PosArgument()
        b: int = PosArgument(default=3, help='3')
        c = True

    args = Args().parse('"foo bar" 5 --no-c')
    assert args.a == 'foo bar'
    assert args.b == 5
    assert args.c is False


def test_prints():
    # just check that they work
    class Args(ArgsParser):
        a = '1'
        b = 1
        c = 1.0
        d = True
        e = [1, 1]

    args = Args().parse([]).print()
    assert args.a == '1'

    args = Args().parse([]).print_table()
    assert args.a == '1'


def test_override():
    class Args(ArgsParser):
        aa = Argument(default='foo', one_dash=True)
        bb = Argument(default='bar', one_dash=False)
        cc = 'baz'

    args = Args(override=False, one_dash=True).parse('-aa foo1 --bb bar1 -cc baz1')
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    args = Args(override=True, one_dash=False).parse('--aa foo1 --bb bar1 --cc baz1')
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    with pytest.raises(SystemExit):
        Args(override=True, one_dash=False).parse('-aa foo1 --bb bar1 -cc baz1')


def test_nested_parsers():
    class Args(ArgsParser):
        class Sub(ArgsParser):
            c = 3

        a = 1
        sub = Sub(aliases=('sss',))
        b = 2
        sub2 = Command()
        d = 4

    args = Args().parse()
    assert args.a == 1
    assert args.b == 2
    assert 'c' not in args._data
    assert 'd' not in args._data

    args = Args().parse('sss')
    assert args.sub == 'sss'
    args = Args().parse('sub')
    assert args.sub == 'sub'
    assert args.c == 3
    assert args.d == 4

    args = Args().parse('sub2 -d 5')
    assert args.sub == 'sub2'
    assert 'c' not in args._data
    assert args.d == 5
