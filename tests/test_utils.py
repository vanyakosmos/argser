import textwrap
from typing import List

from argser import Opt, sub_command
# noinspection PyProtectedMember
from argser.parser import _read_args, _make_parser
from argser.utils import is_list_like_type, ColoredHelpFormatter, colors


def test_is_list_typing():
    assert is_list_like_type(List)
    assert is_list_like_type(List[str])
    assert is_list_like_type(List[int])
    assert not is_list_like_type(list)
    assert not is_list_like_type(str)


def test_cli():
    from argser.__main__ import autocomplete, AutoArgs
    args = AutoArgs()
    args.executables = ['foo.py']
    args.complete_arguments = None
    args.shell = 'bash'
    # run without errors:
    autocomplete(args)


def test_help():
    class Args:
        b: bool
        b1 = True
        l0 = []
        l1 = [1]
        l2: List[float] = None
        f = 2.3
        c = Opt(default=5, metavar='N', choices=[1, 2, 5])
        dddd = 3
        foo_bar_baaaaaaaaz = 3
        v: int = Opt(action='count', default=0)
        v1: int = Opt(action='count', help='bar')
        v2: int = Opt(action='count', help="foo")
        ap: List[str] = Opt(action='append')

        class Sub:
            d = 1
            e = '2'

        sub = sub_command(Sub, help='sub1 help')

    class HelpFormatter(ColoredHelpFormatter):
        header_color = colors.no
        invoc_color = colors.no
        type_color = colors.no
        default_color = colors.no

    args_cls, args, sub_commands = _read_args(Args)
    parser = _make_parser('root', args, sub_commands, formatter_class=HelpFormatter, prog='prog')
    help_msg = parser.format_help()
    real_help = textwrap.dedent(
        """
        usage: prog [-h] [-b] [--no-b] [--b1] [--no-b1] [--l0 [L [L ...]]] [--l1 L [L ...]] [--l2 [L [L ...]]] [-f F] [-c N]
                    [--dddd D] [--foo-bar-baaaaaaaaz F] [-v] [--v1] [--v2] [--ap A]
                    {sub} ...

        positional arguments:
            {sub}
                sub                 sub1 help

        optional arguments:
            -h, --help              show this help message and exit
            -b                      bool, default: None
            --no-b
            --b1                    bool, default: True
            --no-b1
            --l0 [L [L ...]]        List[str], default: []
            --l1 L [L ...]          List[int], default: [1]
            --l2 [L [L ...]]        List[float], default: None
            -f F                    float, default: 2.3
            -c N                    int, default: 5
            --dddd D                int, default: 3
            --foo-bar-baaaaaaaaz F  int, default: 3
            -v                      int, default: 0
            --v1                    int, default: None. bar
            --v2                    int, default: None. foo
            --ap A                  List[str], default: None
        """
    )

    assert help_msg.strip('\n ') == real_help.strip('\n ')
