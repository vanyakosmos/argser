import textwrap
from typing import List

from argser import Opt, sub_command
# noinspection PyProtectedMember
from argser.parser import _read_args, _make_parser
from argser.utils import is_list_like_type


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


class TestHelpFormatting:
    def compare(self, args_cls, help_text: str):
        args_cls, args, sub_commands = _read_args(args_cls)
        parser = _make_parser('root', args, sub_commands, prog='prog')
        help_msg = parser.format_help()
        print(help_msg)
        real_help = textwrap.dedent(help_text)
        assert real_help.strip('\n ') == help_msg.strip('\n ')

    def test_lists(self):  # disable colorization of help message
        class Args:
            l0 = []
            l1 = [1]
            l2: List[float] = None
            ap: List[str] = Opt(action='append')

        # sometime python3.6 behave strangely and miss inner type in List
        try:
            self.compare(
                Args,
                """
                usage: prog [-h] [--l0 [L [L ...]]] [--l1 L [L ...]] [--l2 [L [L ...]]] [--ap A]
    
                optional arguments:
                    -h, --help        show this help message and exit
                    --l0 [L [L ...]]  List[str], default: []
                    --l1 L [L ...]    List[int], default: [1]
                    --l2 [L [L ...]]  List[float], default: None
                    --ap A            List[str], default: None
                """,
            )
        except AssertionError:
            self.compare(
                Args,
                """
                usage: prog [-h] [--l0 [L [L ...]]] [--l1 L [L ...]] [--l2 [L [L ...]]] [--ap A]

                optional arguments:
                    -h, --help        show this help message and exit
                    --l0 [L [L ...]]  List, default: []
                    --l1 L [L ...]    List, default: [1]
                    --l2 [L [L ...]]  List, default: None
                    --ap A            List, default: None
                """,
            )

    def test_with_base(self):
        class Base:
            bb: bool = Opt(default=True, help="foo bar")

        class Args(Base):
            b: bool
            b1 = True

        self.compare(
            Args,
            """
            usage: prog [-h] [-b] [--no-b] [--b1] [--no-b1] [--bb] [--no-bb]

            optional arguments:
                -h, --help  show this help message and exit
                -b          bool, default: None
                --no-b
                --b1        bool, default: True
                --no-b1
                --bb        bool, default: True. foo bar
                --no-bb
            """,
        )

    def test_sub_command(self):
        class Args:
            a = 1.1

            class Sub:
                d = 1
                e = '2'

            sub = sub_command(Sub, help='sub1 help')

        self.compare(
            Args,
            """
            usage: prog [-h] [-a A] {sub} ...

            positional arguments:
                {sub}
                    sub     sub1 help
            
            optional arguments:
                -h, --help  show this help message and exit
                -a A        float, default: 1.1
            """,
        )

    def test_actions(self):
        class Args:
            v: int = Opt(action='count', default=0)
            v1: int = Opt(action='count', help='bar')
            v2: int = Opt(action='count', help="foo")
            ap: list = Opt(action='append')

        self.compare(
            Args,
            """
            usage: prog [-h] [-v] [--v1] [--v2] [--ap A]

            optional arguments:
                -h, --help  show this help message and exit
                -v          int, default: 0
                --v1        int, default: None. bar
                --v2        int, default: None. foo
                --ap A      list, default: None
            """,
        )

    def test_mix(self):
        class Args:
            b: bool
            b1 = True
            f = 2.3
            c = Opt(default=5, metavar='N', choices=[1, 2, 5])
            dddd = 3
            foo_bar_baaaaaaaaz = 3

        self.compare(
            Args,
            """
            usage: prog [-h] [-b] [--no-b] [--b1] [--no-b1] [-f F] [-c N] [--dddd D] [--foo-bar-baaaaaaaaz F]

            optional arguments:
                -h, --help              show this help message and exit
                -b                      bool, default: None
                --no-b
                --b1                    bool, default: True
                --no-b1
                -f F                    float, default: 2.3
                -c N                    int, default: 5
                --dddd D                int, default: 3
                --foo-bar-baaaaaaaaz F  int, default: 3
            """,
        )
