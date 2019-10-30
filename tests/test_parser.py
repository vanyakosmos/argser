from argparse import Action
from typing import Callable, List

import pytest

import argser
from argser import Arg, Opt, parse_args, sub_command
# noinspection PyProtectedMember
from argser.parser import _make_shortcuts_sub_wise, _read_args


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

    args = parse_args(Args, '-a 2 --bb "foo bar" --ccc-ddd 3.3 4.4 -e 1 0')
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
        a: int = Opt(metavar='AA')
        bb: str = Opt(default='foo')
        ccc_ddd: List[float] = Opt(default=[1.1, 2.2])
        e: List[bool] = Opt(default=[True])

    args = parse_args(Args, '')
    assert args.a is None
    assert args.bb == 'foo'
    assert args.ccc_ddd == [1.1, 2.2]
    assert args.e == [True]

    args = parse_args(Args, '-a 2 --bb "foo bar" --ccc-ddd 3.3 4.4 -e 1 0')
    assert args.a == 2
    assert args.bb == 'foo bar'
    assert args.ccc_ddd == [3.3, 4.4]
    assert args.e == [True, False]


def test_nargs():
    class Args:
        a: str = Opt()
        # b = Opt(nargs=0)  # can't be used with default action
        c = Opt(nargs=1)
        d = Opt(nargs=3)
        e = Opt(nargs='?')
        f = Opt(nargs='*', required=True)
        g = Opt(nargs='+', required=True)

    with pytest.raises(SystemExit):
        parse_args(Args, '')  # g is required

    with pytest.raises(SystemExit):
        parse_args(Args, '-f 1')  # g is required

    with pytest.raises(SystemExit):
        parse_args(Args, '-g 1 -c 1 2')

    with pytest.raises(SystemExit):
        parse_args(Args, '-g 1 -d 1 2 3 4')

    args = parse_args(Args, '-a 1 -c 2 -d 3 4 5 -e 6 -f -g 9 10')
    assert args.a == '1'
    assert args.c == ['2']
    assert args.d == ['3', '4', '5']
    assert args.e == '6'
    assert args.f == []
    assert args.g == ['9', '10']


def test_positional_args():
    class Args:
        a = 1
        bb: str = Arg()
        ccc: List[int] = Arg(metavar='C')
        d = True
        dd: bool = Opt(help='foo')

    args = parse_args(Args, '"foo bar" 1 2 -a 5 --no-d')
    assert args.a == 5
    assert args.bb == 'foo bar'
    assert args.ccc == [1, 2]
    assert args.d is False


def test_argcomplete_integration():
    # just make sure that nothing breaks
    def comp(**kwargs):
        return ['foo', 'bar']

    class Args:
        c: str = Opt(metavar='C', completer=comp)

    args = parse_args(Args, '-c "foo bar"')
    assert args.c == "foo bar"


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
        d = [True, False]

    args = parse_args(Args, [])
    assert args.a is None
    assert args.b is True
    assert args.c is False

    args = parse_args(Args, '-a', bool_flag=True)
    assert args.a is True
    args = parse_args(Args, '--no-a', bool_flag=True)
    assert args.a is False
    args = parse_args(Args, '-no-a', bool_flag=True, prefix='-')
    assert args.a is False

    args = parse_args(Args, '-no-b -c', bool_flag=True, prefix='-')
    assert args.b is False
    assert args.c is True

    args = parse_args(Args, '-a 1 -b false -c yes', bool_flag=False)
    assert args.a is True
    assert args.b is False
    assert args.c is True

    with pytest.raises(SystemExit):
        parse_args(Args, '-a a', bool_flag=False)

    # trigger help
    with pytest.raises(SystemExit):
        parse_args(Args, '-h')


class TestList:
    def test_default(self, list_args):
        args = list_args('')
        assert args.a is None
        assert args.b is None
        assert args.c is None
        assert args.d == []
        assert args.e == [1.1, 2.2]

    def test_complex(self, list_args):
        args = list_args('-a 1 a "a b" -b b -c 1 -d true 0 -e 1.0 2.2')
        assert args.a == ['1', 'a', 'a b']
        assert args.b == ['b']
        assert args.c == [1]
        assert args.d == [True, False]
        assert args.e == [1.0, 2.2]

    def test_nargs(self, list_args):
        args = list_args('-a -b -c -d -e 1.0')
        assert args.a == []
        assert args.b == []
        assert args.c == []
        assert args.d == []
        assert args.e == [1.0]

        args_cls, (a, b, c, d, e), sub_commands = _read_args(args.__class__)
        # a, b, c, d, e = args_as_list(args)
        assert a.nargs == '*'
        assert b.nargs == '*'
        assert c.nargs == '*'
        assert d.nargs == '*'
        assert e.nargs == '+'

        # -e has default value with >0 elements and that's why nargs is + instead of *
        with pytest.raises(SystemExit):
            list_args('-a 1 -e')

    def test_types(self, list_args):
        args_cls, (a, b, c, d, e), sub_commands = _read_args(list_args().__class__)
        assert a.type is list  # because of annotation
        assert a.constructor is str
        assert b.type == List  # ^ same
        assert b.constructor is str
        assert c.type == List[int]
        assert c.constructor is int
        assert d.type == List[bool]
        assert d.constructor is bool
        assert e.type == List[float]
        assert e.constructor is float


def test_non_standard_type():
    class Args:
        integers: List[int] = Arg(nargs='+')
        accumulate: Callable = Opt(action='store_const', const=sum, default=max)

    args = parse_args(Args, '1 2 3')
    assert args.accumulate(args.integers) == 3

    args = parse_args(Args, '1 2 3 -a')
    assert args.accumulate(args.integers) == 6


def test_custom_type():
    class A:
        def __init__(self, v):
            self.v = v

        def __str__(self):
            return f"A({self.v})"

        def __eq__(self, other):
            return other.v == self.v

    class Args:
        a: A
        aa: List[A] = []

    args = parse_args(Args, '-a 1 --aa 2 3')
    assert args.a == A('1')
    assert args.aa == [A('2'), A('3')]

    args = parse_args(Args, '')
    assert args.a is None
    assert args.aa == []


def test_override():
    class Args:
        aa = Opt(default='foo', prefix='-')
        bb = Opt(default='bar', prefix='--')
        cc = 'baz'

    args = parse_args(Args, '-aa foo1 --bb bar1 -cc baz1', override=False, prefix='-')
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    args = parse_args(Args, '--aa foo1 --bb bar1 --cc baz1', override=True, prefix='--')
    assert args.aa == 'foo1'
    assert args.bb == 'bar1'
    assert args.cc == 'baz1'

    with pytest.raises(SystemExit):
        parse_args(Args, '-aa foo1 --bb bar1 -cc baz1', override=True, prefix='--')


def test_action_store():
    class Args:
        a = Opt(action='store', default='24')

    args = parse_args(Args, '-a 42')
    assert args.a == '42'


class TestAction:
    def test_store_const(self):
        class Args:
            a = Opt(action='store_const', default='42', const=42)

        args = parse_args(Args, '')
        assert args.a == '42'
        args = parse_args(Args, '-a')
        assert args.a == 42

    def test_store_bool(self):
        class Args:
            a = Opt(action='store_true', default=1)
            b = Opt(action='store_false')

        args = parse_args(Args, '')
        assert args.a == 1
        assert args.b is True

        args = parse_args(Args, '-a -b')
        assert args.a is True
        assert args.b is False

    def test_append(self):
        class Args:
            a: List[int] = Opt(action='append', default=[])

        args = parse_args(Args, '')
        assert args.a == []

        args = parse_args(Args, '-a 1')
        assert args.a == [1]

        args = parse_args(Args, '-a 1 -a 2')
        assert args.a == [1, 2]

    def test_count(self):
        class Args:
            verbose: int = Opt(action='count', default=0)

        args = parse_args(Args, '')
        assert args.verbose == 0

        args = parse_args(Args, '-vvv')
        assert args.verbose == 3

    def test_version(self):
        class Args:
            version: str = Opt('V', action='version', version='%(prog)s 0.0.1')

        with pytest.raises(SystemExit, match='0'):
            parse_args(Args, '-V', parser_kwargs=dict(prog='PROG'))

    def test_custom(self):
        # from python docs
        class FooAction(Action):
            def __init__(self, option_strings, dest, nargs=None, **kwargs):
                if nargs is not None:
                    raise ValueError("nargs not allowed")
                super(FooAction, self).__init__(option_strings, dest, **kwargs)

            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, f'[{values}]')

        class Args:
            a: str = Opt(action=FooAction, default='[]')

        args = parse_args(Args, '')
        assert args.a == '[]'

        args = parse_args(Args, '-a "foo bar"')
        assert args.a == '[foo bar]'


def test_make_shortcuts():
    a = Opt(dest='a', type=str)
    aa = Opt(dest='aa', type=str)
    bc = Opt(dest='bc', type=str)
    ab_cd = Opt(dest='ab_cd', type=str)
    ab_cde = Opt(dest='ab_cde', type=str)
    bcd = Opt('foo', dest='bcd', type=str)
    f1 = Opt('f3', dest='f1', type=str)
    f2_3 = Opt(dest='f2_3', type=str)
    # sub
    aaa = Opt(dest='aaa', type=str)
    ab_cd2 = Opt(dest='ab_cd', type=str)

    def comp_names(opt: Opt, *names):
        return set(opt.option_names) == set(names)

    _make_shortcuts_sub_wise([a, aa, bc, ab_cd, ab_cde, bcd, f1, f2_3], {'sub': (None, [aaa, ab_cd2], {})})
    assert a.dest == 'a' and comp_names(a, 'a')  # already short name
    assert aa.dest == 'aa' and comp_names(aa, 'aa')  # name 'a' already exists
    assert bc.dest == 'bc' and comp_names(bc, 'b', 'bc')
    assert ab_cd.dest == 'ab_cd' and comp_names(ab_cd, 'ac', 'ab_cd')
    assert ab_cde.dest == 'ab_cde' and comp_names(ab_cde, 'ab_cde')  # ac is taken
    assert bcd.dest == 'bcd' and comp_names(bcd, 'foo', 'bcd')  # alias was already defined and override is false
    assert comp_names(f1, 'f1', 'f3')
    assert comp_names(f2_3, 'f2_3')
    # sub
    assert aaa.dest == 'aaa' and comp_names(aaa, 'a', 'aaa')
    assert ab_cd2.dest == 'ab_cd' and comp_names(ab_cd2, 'ac', 'ab_cd')  # dest was changed


def test_reusability():
    class CommonArgs:
        a: int
        b: float
        c = 'c'
        g: bool = Opt(default=True, help="gg")

    class Args1(CommonArgs):
        a: str
        c = 2
        d: float

    class Args2(CommonArgs):
        e = 'foo'

    args = parse_args(CommonArgs, '-a 1 -b 2.2 -c cc')
    assert args.a == 1
    assert args.b == 2.2
    assert args.c == 'cc'
    assert args.g is True

    args = parse_args(Args1, '-a 1 -b 4.4 -c 5 -d 2.2')
    assert args.a == '1'
    assert args.b == 4.4
    assert args.c == 5
    assert args.d == 2.2
    assert args.g is True

    args = parse_args(Args2, '-a 1 -b 5.5 -e "foo bar" --no-g')
    assert args.a == 1
    assert args.b == 5.5
    assert args.c == 'c'
    assert args.e == 'foo bar'
    assert args.g is False


def test_prefix():
    class Args:
        aaa: int = Opt(prefix='-')
        bbb: int = Opt(prefix='++')

    args = parse_args(Args, '-aaa 42 ++bbb 42')
    assert args.aaa == 42
    assert args.bbb == 42


def test_constructor():
    class Args:
        a: List[int] = Opt(constructor=lambda x: [int(e) + 1 for e in list(x)], nargs='?', default=[-1])
        b: int = Opt(constructor=lambda x: int(x) + 2)

    args = parse_args(Args, '')
    assert args.a == [-1]
    assert args.b is None

    args = parse_args(Args, '-a 123 -b 5')
    assert args.a == [2, 3, 4]
    assert args.b == 7
