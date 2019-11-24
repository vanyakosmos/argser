import textwrap

from argser import parse_args, sub_command, Opt
from argser.display import make_table, make_tree, stringify


def _norm(text: str):
    text = text.strip()
    return '\n'.join([line.rstrip() for line in text.splitlines()])


def test_prints():
    class Args:
        n: str
        a = '1'
        b = 1
        c = 1.0
        d = True
        e = Opt(default=[1, 1], help='foo bar')
        just_long_long_argument = 'foo bar baz'

        class Sub:
            f = True

        sub = sub_command(Sub)

    # just check that they run without errors
    parse_args(Args, '', show=True, shorten=True)
    parse_args(Args, '', show=True)

    parse_args(Args, '', show='table', shorten=True)
    parse_args(Args, '-a 5 sub', show='table', tabulate_preset='fancy')

    parse_args(Args, '', show='tree', shorten=True)
    parse_args(Args, '-a 5 sub', show='tree')


class TestStringifier:
    def test_simple(self):
        class Args:
            a = 1

        args = parse_args(Args, '-a 2')
        assert stringify(args) == 'Args(a=2)'
        assert str(args) == 'Args(a=2)'

    def test_sub_cmd(self):
        class Args:
            a = 1

            class Sub:
                a = '2'

            sub = sub_command(Sub)

        args = parse_args(Args, '-a 2 sub -a 4')
        assert stringify(args) == "Args(a=2, sub=Sub(a='4'))"
        assert str(args) == "Args(a=2, sub=Sub(a='4'))"

    def test_with_custom_str_method(self):
        class Args:
            a = 1

            class Sub:
                a = 2

                def __init__(self, b):
                    self.b = b

                def __str__(self):
                    return f"SSS({self.a}-{self.b})"

            sub = sub_command(Sub(42))

        args = parse_args(Args, '-a 2 sub -a 4')
        assert stringify(args) == 'Args(a=2, sub=Sub(b=42, a=4))'
        assert str(args) == 'Args(a=2, sub=Sub(b=42, a=4))'
        assert str(args.sub) == 'SSS(4-42)'


def test_wide_table():
    class Args:
        a1 = None
        a2 = 1
        a3 = '1'
        a4 = 1
        a5 = [1, 2]
        a6 = '1111111'
        a8 = 1
        a7 = 1

        class Sub:
            a1 = 1
            a2 = 1
            a3 = '1'
            a4 = 1
            a5 = [1, 2]
            a6 = '1111111'
            a7 = 1
            a8 = 1
            a9 = 1

            class Sub2:
                b1 = 2
                b2 = 2

            sub2 = sub_command(Sub2)

        sub = sub_command(Sub)

    args = parse_args(Args, 'sub sub2')
    table = make_table(args, cols=None)
    assert len(table.splitlines()[0]) < 40

    table = make_table(args, cols='auto')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, cols=1)
    assert len(table.splitlines()[0]) < 40

    table = make_table(args, cols=3)
    assert len(table.splitlines()[0]) > 40

    # be careful with trailing spaces after sub__a5 [1, 2]
    print(table)
    result = textwrap.dedent(
        """
        arg    value       arg      value       arg              value
        -----  ---------   -------  ---------   -------------  -------
        a1     -           a7       1           sub__a7              1
        a2     1           sub__a1  1           sub__a8              1
        a3     '1'         sub__a2  1           sub__a9              1
        a4     1           sub__a3  '1'         sub__sub2__b1        2
        a5     [1, 2]      sub__a4  1           sub__sub2__b2        2
        a6     '1111111'   sub__a5  [1, 2]
        a8     1           sub__a6  '1111111'
        """
    )
    assert _norm(table) == _norm(result)

    table = make_table(args, cols='sub')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, cols='sub-auto')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, cols='sub-3')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, preset='fancy')
    assert len(table.splitlines()[0]) > 40


class TestTree:
    def test_simple(self):
        class Args:
            a = 1
            b = None

        args = parse_args(Args, '')

        t = make_tree(args)
        r = textwrap.dedent(
            """
            Args
            ├ a = 1
            └ b = -
        """
        ).strip()
        assert t == r

    def test_sub_cmd(self):
        class Args:
            a = 1
            b = None

            class Sub:
                c = 'c'
                d = True

                class Sub1:
                    e = 'e'
                    f = 1.23

                sub1 = sub_command(Sub1)

            sub = sub_command(Sub)

        args = parse_args(Args, 'sub sub1')

        t = make_tree(args)
        print(t)
        r = textwrap.dedent(
            """
            Args
            ├ a = 1
            ├ b = -
            └ sub = Sub
              ├ c = 'c'
              ├ d = True
              └ sub1 = Sub1
                ├ e = 'e'
                └ f = 1.23
        """
        ).strip()
        assert _norm(t) == _norm(r)

    def test_multiline(self):
        big_text = "foo bar baz\n " * 10

        class Args:
            a = 1
            b = big_text

            class Sub:
                d = True
                c = big_text  # keep this as last arg to test prefix

            sub = sub_command(Sub)

        args = parse_args(Args, 'sub')
        t = make_tree(args)
        print(t)
        r = textwrap.dedent(
            r"""
            Args
            ├ a = 1
            ├ b = 'foo bar baz\n foo bar baz\n foo bar
            │     baz\n foo bar baz\n foo bar baz\n foo
            │     bar baz\n foo bar baz\n foo bar baz\n
            │     foo bar baz\n foo bar baz\n '
            └ sub = Sub
              ├ d = True
              ├ c = 'foo bar baz\n foo bar baz\n foo bar
              │     baz\n foo bar baz\n foo bar baz\n foo
              │     bar baz\n foo bar baz\n foo bar baz\n
              └     foo bar baz\n foo bar baz\n '
        """
        ).strip()
        assert t == r
