import textwrap

from argser import parse_args, sub_command, Opt
from argser.display import make_table


def test_prints():
    # just check that they work
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

    parse_args(Args, '', show=True, shorten=True)
    parse_args(Args, '', show=True, shorten=True)
    args = parse_args(Args, '', show=True)
    assert args.a == '1'

    parse_args(Args, '', show='table', shorten=True)
    args = parse_args(Args, '-a 5 sub', show='table', tabulate_preset='fancy')
    assert args.a == '5'
    assert args.sub.f is True


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
    result = textwrap.dedent(
        """
        arg    value     arg      value     arg              value
        -----  -------   -------  -------   -------------  -------
        a1     -         a7       1         sub__a7              1
        a2     1         sub__a1  1         sub__a8              1
        a3     1         sub__a2  1         sub__a9              1
        a4     1         sub__a3  1         sub__sub2__b1        2
        a5     [1, 2]    sub__a4  1         sub__sub2__b2        2
        a6     1111111   sub__a5  [1, 2]                          
        a8     1         sub__a6  1111111
        """
    )
    assert table.strip('\n ') == result.strip('\n ')

    table = make_table(args, cols='sub')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, cols='sub-auto')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, cols='sub-3')
    assert len(table.splitlines()[0]) > 40

    table = make_table(args, preset='fancy')
    assert len(table.splitlines()[0]) > 40
