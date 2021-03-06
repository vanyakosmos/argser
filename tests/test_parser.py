import shlex
from argparse import Action, ArgumentParser, Namespace
from typing import Callable, List

import pytest

import argser
from argser import Arg, Opt, parse_args, sub_command
from argser.exceptions import ArgserException
from argser.parser import (
    _make_shortcuts_sub_wise as make_shortcuts,
    _read_args as read_args,
)
from argser.utils import args_to_dict


@pytest.mark.parametrize(
    "args, a, bb, ccc_ddd, e",
    [
        ('', None, 'foo', [1.1, 2.2], []),
        ('-a 2 --bb "foo bar" --ccc-ddd 3.3 4.4 -e 1 0', 2, 'foo bar', [3.3, 4.4], [True, False]),
    ],
)
def test_simple(args, a, bb, ccc_ddd, e):
    class Args:
        a: int
        bb = 'foo'
        ccc_ddd = [1.1, 2.2]
        e: List[bool] = []

    args = parse_args(Args, args)
    assert args.a == a
    assert args.bb == bb
    assert args.ccc_ddd == ccc_ddd
    assert args.e == e


@pytest.mark.parametrize(
    "args, a, bb, ccc_ddd, sub_d, sub_ee",
    [
        ('', None, 'foo', [1.1, 2.2], None, None),
        ('-a 1 --bb "foo bar" sub -d 1 2 --ee baz', 1, 'foo bar', [1.1, 2.2], [1, 2], 'baz',),
    ],
)
def test_sub_command(args, a, bb, ccc_ddd, sub_d, sub_ee):
    class Args:
        a: int
        bb = 'foo'
        ccc_ddd = [1.1, 2.2]

        class SubArgs:
            d: List[int]
            ee = ''

        sub = sub_command(SubArgs)

    args = parse_args(Args, args)
    assert args.a == a
    assert args.bb == bb
    assert args.ccc_ddd == ccc_ddd
    if sub_d and sub_ee:
        assert args.sub.d == sub_d
        assert args.sub.ee == sub_ee
    else:
        assert args.sub is None


@pytest.mark.parametrize(
    "args, a, bb, ccc_ddd, e",
    [
        ('', None, 'foo', [1.1, 2.2], [True]),
        ('-a 2 --bb "foo bar" --ccc-ddd 3.3 4.4 -e 1 0', 2, 'foo bar', [3.3, 4.4], [True, False],),
    ],
)
def test_complex_args(args, a, bb, ccc_ddd, e):
    class Args:
        a: int = Opt(metavar='AA')
        bb: str = Opt(default='foo')
        ccc_ddd: List[float] = Opt(default=[1.1, 2.2])
        e: List[bool] = Opt(default=[True])

    args = parse_args(Args, args)
    assert args.a == a
    assert args.bb == bb
    assert args.ccc_ddd == ccc_ddd
    assert args.e == e


class TestNargs:
    @pytest.fixture()
    def args_cls(self):
        class Args:
            a: str = Opt()
            # b = Opt(nargs=0)  # can't be used with default action
            c = Opt(nargs=1)
            d = Opt(nargs=3)
            e = Opt(nargs='?')
            f = Opt(nargs='*', required=True)
            g = Opt(nargs='+', required=True)

        return Args

    @pytest.mark.parametrize("args", ['', '-f 1', '-g 1 -c 1 2', '-g 1 -d 1 2 3 4'])
    def test_error(self, args_cls, args):
        with pytest.raises(SystemExit):
            parse_args(args_cls, args)

    def test_ok(self, args_cls):
        args = parse_args(args_cls, '-a 1 -c 2 -d 3 4 5 -e 6 -f -g 9 10')
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


@pytest.mark.parametrize(
    "args, a, b, c",
    [
        ('', None, 'b', None),
        ('-a 1 -b 2 -c 3', '1', '2', '3'),
        ('-a "foo bar"', 'foo bar', 'b', None),
    ],
)
def test_parse_str(args, a, b, c):
    class Args:
        a: str
        b = 'b'
        c = None

    args = parse_args(Args, args)
    assert args.a == a
    assert args.b == b
    assert args.c == c


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


class TestBooleans:
    @pytest.fixture()
    def args_cls(self):
        class Args:
            a: bool
            b = True
            c = False
            d = [True, False]

        return Args

    def test_default(self, args_cls):
        args = parse_args(args_cls, [])
        assert args.a is None
        assert args.b is True
        assert args.c is False

    @pytest.mark.parametrize(
        "args, prefix, a, b, c, d",
        [
            ('', '--', None, True, False, [True, False]),
            ('-a', '--', True, True, False, [True, False]),
            ('--no-a', '--', False, True, False, [True, False]),
            ('-no-a', '-', False, True, False, [True, False]),
            ('-no-b -c', '-', None, False, True, [True, False]),
            ('-d 1 1', '--', None, True, False, [True, True]),
        ],
    )
    def test_bool_flag_true(self, args_cls, args, prefix, a, b, c, d):
        args = parse_args(args_cls, args, bool_flag=True, prefix=prefix)
        assert args.a == a
        assert args.b == b
        assert args.c == c
        assert args.d == d

    def test_bool_flag_false(self, args_cls):
        args = parse_args(args_cls, '-a 1 -b false -c yes', bool_flag=False)
        assert args.a is True
        assert args.b is False
        assert args.c is True

        with pytest.raises(SystemExit):
            parse_args(args_cls, '-a a', bool_flag=False)


class TestList:
    @property
    def args_cls(self):
        class Args:
            a: list
            b: List
            c: List[int]
            d: List[bool] = []
            e = [1.1, 2.2]

        return Args

    def test_default(self):
        args = parse_args(self.args_cls, '')
        assert args.a is None
        assert args.b is None
        assert args.c is None
        assert args.d == []
        assert args.e == [1.1, 2.2]

    def test_complex(self):
        args = parse_args(self.args_cls, '-a 1 a "a b" -b b -c 1 -d true 0 -e 1.0 2.2')
        assert args.a == ['1', 'a', 'a b']
        assert args.b == ['b']
        assert args.c == [1]
        assert args.d == [True, False]
        assert args.e == [1.0, 2.2]

    def test_nargs(self):
        args = parse_args(self.args_cls, '-a -b -c -d -e 1.0')
        assert args.a == []
        assert args.b == []
        assert args.c == []
        assert args.d == []
        assert args.e == [1.0]

        args_cls, (a, b, c, d, e), sub_commands = read_args(self.args_cls())
        # a, b, c, d, e = args_as_list(args)
        assert a.nargs == '*'
        assert b.nargs == '*'
        assert c.nargs == '*'
        assert d.nargs == '*'
        assert e.nargs == '+'

        # -e has default value with >0 elements and that's why nargs is + instead of *
        with pytest.raises(SystemExit):
            parse_args(self.args_cls, '-a 1 -e')

    def test_types(self):
        args_cls, (a, b, c, d, e), sub_commands = read_args(self.args_cls())
        assert a.type is list  # because of annotation
        assert a.factory is str
        assert b.type == List  # ^ same
        assert b.factory is str
        assert c.type == List[int]
        assert c.factory is int
        assert d.type == List[bool]
        assert d.factory is bool
        assert e.type == List[float]
        assert e.factory is float


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

    make_shortcuts([a, aa, bc, ab_cd, ab_cde, bcd, f1, f2_3], {'sub': (None, [aaa, ab_cd2], {})})
    assert a.dest == 'a' and comp_names(a, 'a')  # already short name
    assert aa.dest == 'aa' and comp_names(aa, 'aa')  # name 'a' already exists
    assert bc.dest == 'bc' and comp_names(bc, 'b', 'bc')
    assert ab_cd.dest == 'ab_cd' and comp_names(ab_cd, 'ac', 'ab_cd')
    assert ab_cde.dest == 'ab_cde' and comp_names(ab_cde, 'ab_cde')  # ac is taken
    # alias was already defined and override is false
    assert bcd.dest == 'bcd' and comp_names(bcd, 'foo', 'bcd')
    assert comp_names(f1, 'f1', 'f3')
    assert comp_names(f2_3, 'f2_3')

    assert aaa.dest == 'aaa' and comp_names(aaa, 'a', 'aaa')
    # dest was changed
    assert ab_cd2.dest == 'ab_cd' and comp_names(ab_cd2, 'ac', 'ab_cd')


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


def test_quick_help():
    class Args:
        # default, help
        a = 1, "help for a"
        # with annotation parenthesis are required
        b: str = (None, "help for b")
        # default, factory, help
        c: float = (5.0, lambda x: float(x) * 2, "help for b")

    args = parse_args(Args, '')
    assert args.a == 1
    assert args.b is None
    assert args.c == pytest.approx(5.0)

    args = parse_args(Args, '-a 2 -b "foo bar" -c 10')
    assert args.a == 2
    assert args.b == 'foo bar'
    assert args.c == pytest.approx(20.0)

    class Args:
        e = ('foo', str, "help", "some trash no one asked for")

    with pytest.raises(ArgserException) as context:
        parse_args(Args, '')
    assert '(default, help) or (default, factory, help)' in str(context.value)


def test_sub_cmd_with_same_arguments():
    # use factory because parse_args will remove static sub-cmd attributes from
    # inner classed
    def make_args():
        class Args:
            a = 1
            b = 2

            class Sub:
                a = 3
                b = 4

                class Sub2:
                    a = -1
                    b = -2

                sub = sub_command(Sub2)

            sub = sub_command(Sub)

        return Args()

    args = parse_args(make_args(), '')
    assert args.a == 1
    assert args.b == 2
    assert args.sub is None

    args = parse_args(make_args(), 'sub')
    assert args.a == 1
    assert args.b == 2
    assert args.sub.a == 3
    assert args.sub.b == 4

    args = parse_args(make_args(), '-a 5 -b 6 sub -a 7 -b 8')
    assert args.a == 5
    assert args.b == 6
    assert args.sub.a == 7
    assert args.sub.b == 8

    args = parse_args(make_args(), '-a 5 -b 6 sub -a 7 -b 8 sub -a 9 -b 10')
    assert args.a == 5
    assert args.b == 6
    assert args.sub.a == 7
    assert args.sub.b == 8
    assert args.sub.sub.a == 9
    assert args.sub.sub.b == 10


class TestPredefinedParser:
    def test_namespace_injection(self):
        parser = ArgumentParser(prog='prog')
        parser.add_argument('--foo', default=42, type=int)

        class Args:
            __namespace__: Namespace  # just for hint in IDE
            a = 1
            b = True

        args = parse_args(Args, '--foo 100 -a 5 --no-b', parser=parser)
        assert args.a == 5
        assert args.b is False
        assert args.__namespace__.foo == 100

    def test_parser_params_are_untouched(self):
        parser = ArgumentParser(prog='prog')
        parser.add_argument('--foo', default=42, type=int)

        class Args:
            a = 1

        parse_args(Args, '', parser=parser, parser_prog='NOT PROG')
        assert parser.prog == 'prog'

    def test_make_parser(self):
        parser = ArgumentParser(prog='prog')
        parser.add_argument('--foo', default=42, type=int)

        class Args:
            __namespace__: Namespace
            a = 1
            b = True

        parser, options = argser.make_parser(Args(), parser=parser)
        args = shlex.split('--foo 100 -a 5 --no-b')
        ns = parser.parse_args(args)
        assert isinstance(ns, Namespace)
        assert ns.foo == 100

        args = argser.populate_holder(Args(), parser, options, args)
        assert args.a == 5
        assert args.b is False

    def test_sub_command(self):
        parser = ArgumentParser(prog='prog')
        parser.add_argument('--foo', default=42, type=int)

        class Args:
            __namespace__: Namespace
            a = 1

            class Sub:
                b = False

            sub = sub_command(Sub, parser=parser)

        args = parse_args(Args, '-a 5 sub --foo 100 --no-b')
        assert args.a == 5
        assert args.sub.b is False
        assert args.__namespace__.foo == 100


def test_ignored_fields():
    class Args:
        foo = 1
        bar: int = 1
        baz: int = Opt(default=1)
        _foo = 1
        _bar: int = 1
        _baz: int = Opt(default=1)
        __foo = 1
        __bar: int = 1
        __baz: int = Opt(default=1)

    args = parse_args(Args, '')
    d = args_to_dict(args)
    assert 'foo' in d
    assert 'bar' in d
    assert 'baz' in d
    assert '_foo' not in d
    assert '_bar' not in d
    assert '_baz' not in d
    assert '__foo' not in d
    assert '__bar' not in d
    assert '__baz' not in d


def test_updated_arguments_on_holder():
    class Args:
        a: int
        b = 1.1
        c = True, 'help c'
        dd = [1], 'help dd'
        ee_ee: int = Opt(default=1)
        f = Arg()

    args = parse_args(Args, '-a 1 -b 2 --no-c --dd 3 --ee 5 foo')
    assert isinstance(Args.a, Opt)
    assert Args.a.type is int
    assert Args.a.default is None
    assert args.a == 1

    assert isinstance(Args.b, Opt)
    assert Args.b.type is float
    assert Args.b.default == pytest.approx(1.1)
    assert args.b == pytest.approx(2.0)

    assert isinstance(Args.c, Opt)
    assert Args.c.type == bool
    assert Args.c.default is True
    assert Args.c.help == 'help c'
    assert args.c is False

    assert isinstance(Args.dd, Opt)
    assert Args.dd.type == List[int]
    assert Args.dd.factory is int
    assert Args.dd.default == [1]
    assert Args.dd.help == 'help dd'
    assert args.dd == [3]

    assert isinstance(Args.ee_ee, Opt)
    assert Args.ee_ee.type is int
    assert Args.ee_ee.default == 1
    assert args.ee_ee == 5

    assert isinstance(Args.f, Arg)
    assert Args.f.type is str
    assert Args.f.default is None
    assert args.f == 'foo'


class TestFactory:
    @pytest.mark.parametrize("args, value", [('', 1), ('-a 5', 6)])
    def test_simple(self, args, value):
        class Args:
            a = 1

            def read_a(self, x: str):
                return int(x) + 1

        args = parse_args(Args, args)
        assert args.a == value

    @pytest.mark.parametrize("args, value", [('', 1), ('-a 5', 6)])
    def test_string(self, args, value):
        class Args:
            a = Opt(default=1, factory='read_b')

            def read_b(self, x: str):
                return int(x) + 1

        args = parse_args(Args, args)
        assert args.a == value

    @pytest.mark.parametrize("args, value", [('', 1), ('-a 5', 6)])
    def test_function(self, args, value):
        def read_a(x: str):
            return int(x) + 1

        class Args:
            a = Opt(default=1, factory=read_a)

        args = parse_args(Args, args)
        assert args.a == value

    def test_invalid_string(self):
        class Args:
            a = Opt(default=1, factory='read_A')

            def read_a(self, x: str):
                return int(x) + 1

        with pytest.raises(ArgserException):
            parse_args(Args, '')

    @pytest.mark.parametrize("args, a, b", [('', [-1], None), ('-a 123 -b 5', [2, 3, 4], 7)])
    def test_lambdas(self, args, a, b):
        class Args:
            a: List[int] = Opt(
                factory=lambda x: [int(e) + 1 for e in list(x)], nargs='?', default=[-1]
            )
            b: int = Opt(factory=lambda x: int(x) + 2)

        args = parse_args(Args, args)
        assert args.a == a
        assert args.b == b


class TestInstanceOfArgs:
    def test_factory(self):
        class Args:
            a = 1

            def read_a(self, x: str):
                assert self  # should be available
                return int(x) + 1

        parse_args(Args, '-a 2')

    def test_instance(self):
        class Args:
            a = 1

        original = Args()
        args = parse_args(original, '-a 2')
        assert args is original
        assert original.a == 2

    @pytest.mark.parametrize("args, b, a", [('-a 2', 1, 3), ('-a 40', 2, 42)])
    def test_initialized(self, args, a, b):
        class Args:
            a = 1

            def __init__(self, b):
                self.b = b

            def read_a(self, x):
                return int(x) + self.b

        args = parse_args(Args(b), args)
        assert args.a == a

    def test_sub_cmd(self):
        class Sub:
            def __init__(self, a):
                self.a = a

        class Args:
            a = 1

            sub = sub_command(Sub(4))

            def read_a(self, x):
                return int(x) + self.sub.a

        args = parse_args(Args, '-a 38')
        assert args.a == 42
