from argparse import ArgumentParser
from typing import Any, List, Union, Iterable

DEFAULT_HELP_FORMAT = "{type}, default: {default!r}."
TRUE_VALUES = {'1', 'true', 't', 'okay', 'ok', 'affirmative', 'yes', 'y', 'totally'}
FALSE_VALUES = {'0', 'false', 'f', 'no', 'n', 'nope', 'nah'}


class AutoHelp:
    def __init__(self, extra=None):
        self.extra = extra

    def __add__(self, other: str):
        return AutoHelp(other)

    def format(self, help_format=DEFAULT_HELP_FORMAT, **kwargs):
        help_text = help_format.format(**kwargs)
        if self.extra:
            help_text = f"{help_text} {self.extra}"
        return help_text


autohelp = AutoHelp()


class Argument:
    def __init__(
        self,
        dest: str = None,
        default: Any = None,
        type=str,
        aliases: Iterable[str] = (),
        help=autohelp,
        help_format=DEFAULT_HELP_FORMAT,
    ):
        self.dest = dest
        self.default = default
        self.type = type
        self.aliases = aliases
        self.help = self.make_help(help, help_format)

    def make_help(self, help: Union[None, str, AutoHelp], help_format: str):
        if isinstance(help, str) or help is None:
            return help
        return help.format(help_format, type=self.type.__name__, default=self.default)

    @property
    def names(self):
        names = [self.dest, *self.aliases]
        for name in names:
            if len(name) > 1:
                yield f"--{name}"
            else:
                yield f"-{name}"


class Separator:
    pass


class ArgsParser:
    def __init__(
        self,
        shortcuts=True,
        help_format=DEFAULT_HELP_FORMAT,
    ):
        self.help_format = help_format
        self.shortcuts = shortcuts
        self._parser = ArgumentParser()
        self._data = {}
        self.args: List[Argument] = []

        self.setup_args()
        self.setup_parser()

    def __getattribute__(self, item):
        if item == '_data' or item not in self._data:
            return object.__getattribute__(self, item)
        return self._data[item]

    def __str__(self):
        params = ", ".join(map(lambda x: f"{x[0]}={x[1]!r}", self._data.items()))
        return f"{self.__class__.__name__}({params})"

    def setup_args(self):
        ann = self.__class__.__annotations__
        for key, value in self.__class__.__dict__.items():  # type: str, Any
            if key.startswith('__'):
                continue
            if isinstance(value, Argument):
                value.dest = key
                self.args.append(value)
                continue
            typ = ann.get(key, type(value))
            self.args.append(Argument(
                dest=key,
                default=value,
                type=typ,
                help_format=self.help_format,
            ))
        if self.shortcuts:
            self.make_shortcuts()

    def make_shortcuts(self):
        for arg in self.args:
            if arg.aliases != ():
                continue
            # aaa -> a, aaa_bbb -> ab
            a = ''.join(map(lambda e: e[0], arg.dest.split('_')))
            arg.aliases = (a,)

    def setup_parser(self):
        for arg in self.args:
            self._parser.add_argument(
                *arg.names,
                dest=arg.dest,
                default=arg.default,
                type=arg.type,
                help=arg.help,
            )

    def parse(self, args=None):
        namespace = self._parser.parse_args(args)
        for key, value in namespace.__dict__.items():
            self._data[key] = value
        return self

    def tabulate(self, cols=1, **kwargs):
        from tabulate import tabulate
        kwargs.setdefault('headers', ['arg', 'value'])
        return tabulate(self._data.items(), **kwargs)

    def print_table(self, cols=1, **kwargs):
        print(self.tabulate(cols, **kwargs))
        return self

    def print(self):
        print(self)
        return self


class Args(ArgsParser):
    aaaa = 5
    aaa_bbb = ['str']
    b: int = None
    c = 'foo'
    d = False
    e: str = Argument(default='fds', aliases=('e1', 'e2'), help=autohelp + "foo bar")


def main():
    args = Args().parse().print_table(tablefmt='psql')
    print(args)


if __name__ == '__main__':
    main()
