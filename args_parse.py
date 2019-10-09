from argparse import ArgumentParser, ArgumentTypeError
from typing import Any, List, Iterable

DEFAULT_HELP_FORMAT = "{type}, default: {default!r}."
TRUE_VALUES = {'1', 'true', 't', 'okay', 'ok', 'affirmative', 'yes', 'y', 'totally'}
FALSE_VALUES = {'0', 'false', 'f', 'no', 'n', 'nope', 'nah'}


def str2bool(v: str):
    v = v.lower()
    if v in TRUE_VALUES:
        return True
    elif v in FALSE_VALUES:
        return False
    raise ArgumentTypeError('Boolean value expected.')


class Argument:
    def __init__(
        self,
        dest: str = None,
        default: Any = None,
        type=str,
        aliases: Iterable[str] = (),
        nargs=None,
        help: str = None,
        help_format=DEFAULT_HELP_FORMAT,
        keep_default_help=True,
        bool_flag=True,
    ):
        self.dest = dest
        self.default = default
        self.type = type
        self.aliases = aliases
        self.nargs = nargs
        self.bool_flag = bool_flag
        self.help_text = help
        self.help_format = help_format
        self.keep_default_help = keep_default_help

    def names(self, prefix=None):
        names = [self.dest, *self.aliases]
        if prefix:
            names = [f'{prefix}{n}' for n in names]
        for name in names:
            if len(name) > 1:
                yield f"--{name}"
            else:
                yield f"-{name}"

    @property
    def params(self):
        return dict(
            dest=self.dest,
            default=self.default,
            type=self.type,
            nargs=self.nargs,
            help=self.help,
        )

    @property
    def help(self):
        help_text = self.help_text
        if self.keep_default_help:
            typ = self.type.__name__
            if self.nargs in ('*', '+'):
                typ = f"List[{typ}]"
            default_help_text = self.help_format.format(type=typ, default=self.default)
            if self.help_text:
                help_text = f"{default_help_text} {self.help_text}"
            else:
                help_text = default_help_text
        return help_text

    def inject_bool(self, parser: ArgumentParser):
        params = self.params
        if self.bool_flag:
            del params['type']
            del params['nargs']
            if self.default is False:
                parser.add_argument(*self.names(), action='store_true', **params)
            elif self.default is True:
                parser.add_argument(*self.names(prefix='no_'), action='store_false', **params)
            else:
                parser.add_argument(*self.names(), action='store_true', **params)
                del params['help']
                parser.add_argument(*self.names(prefix='no_'), action='store_false', **params)
            parser.set_defaults(**{self.dest: self.default})
        else:
            params['type'] = str2bool
            parser.add_argument(*self.names(), **params)

    def inject(self, parser: ArgumentParser):
        if self.type is bool:
            return self.inject_bool(parser)
        parser.add_argument(*self.names(), **self.params)


class Separator:
    pass


class ArgsParser:
    def __init__(
        self,
        shortcuts=True,
        bool_flag=True,
        help_format=DEFAULT_HELP_FORMAT,
        keep_default_help=True,
        override=False,
    ):
        self.shortcuts = shortcuts
        self.bool_flag = bool_flag
        self.help_format = help_format
        self.keep_default_help = keep_default_help
        self.override = override
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

    def get_nargs(self, typ, default):
        # just list
        if isinstance(typ, type) and issubclass(typ, list):
            nargs = '*' if len(default or []) == 0 else '+'
            return str, nargs
        #  List or List[str] or similar
        if not isinstance(typ, type) and hasattr(typ, '_name') and getattr(typ, '_name') == 'List':
            if isinstance(typ.__args__[0], type):
                typ = typ.__args__[0]
            else:
                typ = str
            nargs = '*' if len(default or []) == 0 else '+'
            return typ, nargs
        # non list type
        return typ, '?'

    def setup_args(self):
        ann = self.__class__.__annotations__
        fields = {k: None for k in ann}
        for key, value in self.__class__.__dict__.items():
            fields[key] = value
        for key, value in fields.items():  # type: str, Any
            if key.startswith('__'):
                continue
            if isinstance(value, Argument):
                value.dest = key
                if self.override:
                    value.bool_flag = self.bool_flag
                    value.help_format = self.help_format
                    value.keep_default_help = self.keep_default_help
                self.args.append(value)
                continue
            typ = ann.get(key, type(value))
            typ, nargs = self.get_nargs(typ, value)
            self.args.append(
                Argument(
                    dest=key,
                    default=value,
                    type=typ,
                    nargs=nargs,
                    help_format=self.help_format,
                    keep_default_help=self.keep_default_help,
                    bool_flag=self.bool_flag,
                )
            )
        if self.shortcuts:
            self.make_shortcuts()

    def make_shortcuts(self):
        """Add shortcuts to arguments without defined aliases."""
        used = set()
        for arg in self.args:
            if arg.aliases != ():
                continue
            # aaa -> a, aaa_bbb -> ab
            a = ''.join(map(lambda e: e[0], arg.dest.split('_')))
            if a not in used:
                arg.aliases = (a,)
                used.add(a)

    def setup_parser(self):
        for arg in self.args:
            arg.inject(self._parser)

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
    undef: bool
    foo = []
    aaaa = 5
    aaa_bbb = ['str']
    b: int = None
    c = 'foo'
    true = True
    false = False
    e: str = Argument(default='fds', aliases=('e1', 'e2'), help="foo bar", keep_default_help=False)


def main():
    args = Args(bool_flag=True, override=True).parse().print_table(tablefmt='psql')
    print(args)


if __name__ == '__main__':
    main()
