import logging
import shlex
from argparse import ArgumentParser, ArgumentTypeError
from collections import defaultdict
from pprint import pformat
from typing import Any, List, Iterable, Dict

DEFAULT_HELP_FORMAT = "{type}, default: {default!r}."
TRUE_VALUES = {'1', 'true', 't', 'okay', 'ok', 'affirmative', 'yes', 'y', 'totally'}
FALSE_VALUES = {'0', 'false', 'f', 'no', 'n', 'nope', 'nah'}

logger = logging.getLogger(__name__)


def str2bool(v: str):
    v = v.lower()
    if v in TRUE_VALUES:
        return True
    elif v in FALSE_VALUES:
        return False
    raise ArgumentTypeError('Boolean value expected.')


class Command:
    def __init__(self, name=None, help=None, aliases=()):
        self.name = name
        self.aliases = aliases
        self.help = help

    def __str__(self):
        names = {self.name, *self.aliases}
        names = ', '.join(names - {None})
        return f"Command({names})"

    def __repr__(self):
        return str(self)

    def make_parser(self, subparser):
        return subparser.add_parser(self.name, aliases=self.aliases, help=self.help)


class Argument:
    def __init__(
        self,
        dest: str = None,
        default: Any = None,
        type_=None,
        aliases: Iterable[str] = (),
        nargs=None,
        help: str = None,
        help_format=DEFAULT_HELP_FORMAT,
        keep_default_help=True,
        bool_flag=True,
        one_dash=False,
    ):
        self.dest = dest
        self.default = default
        self.type = type_ or (str if default is None else type(default))
        self.aliases = aliases
        self.nargs = nargs
        self.bool_flag = bool_flag
        self.help_text = help
        self.help_format = help_format
        self.keep_default_help = keep_default_help
        self.one_dash = one_dash

    def __str__(self):
        names = {self.dest, *self.aliases}
        names = ', '.join(names - {None})
        return f"Argument({names}, type={self.type.__name__}, default={self.default!r})"

    def __repr__(self):
        return str(self)

    def names(self, prefix=None):
        names = [self.dest, *self.aliases]
        if prefix:
            names = [f'{prefix}{n}' for n in names]
        for name in names:
            if len(name) == 1 or self.one_dash:
                yield f"-{name}"
            else:
                yield f"--{name}"

    def params(self, exclude=(), **kwargs):
        params = dict(
            dest=self.dest,
            default=self.default,
            type=self.type,
            nargs=self.nargs,
            help=self.help,
        )
        params.update(**kwargs)
        for key in exclude:
            params.pop(key)
        return params

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
        if self.bool_flag and self.nargs not in ('*', '+'):
            params = self.params(exclude=('type', 'nargs'))
            if self.default is False:
                parser.add_argument(*self.names(), action='store_true', **params)
            elif self.default is True:
                parser.add_argument(*self.names(prefix='no-'), action='store_false', **params)
            else:
                parser.add_argument(*self.names(), action='store_true', **params)
                del params['help']
                parser.add_argument(*self.names(prefix='no-'), action='store_false', **params)
            parser.set_defaults(**{self.dest: self.default})
        else:
            params = self.params(type=str2bool)
            parser.add_argument(*self.names(), **params)

    def inject(self, parser: ArgumentParser):
        if self.type is bool:
            return self.inject_bool(parser)
        parser.add_argument(*self.names(), **self.params())


class PosArgument(Argument):
    def __init__(self, **kwargs):
        kwargs['bool_flag'] = False
        super(PosArgument, self).__init__(**kwargs)

    def params(self, exclude=(), **kwargs):
        exclude += ('dest',)
        return super().params(exclude=exclude, **kwargs)

    def names(self, prefix=None):
        return [self.dest]


class ArgsParser:
    def __init__(
        self,
        shortcuts=True,
        bool_flag=True,
        help_format=DEFAULT_HELP_FORMAT,
        keep_default_help=True,
        one_dash=False,
        override=False,
        parser_kwargs=None,
        subparser_kwargs=None,
    ):
        self._data = {}
        self._shortcuts = shortcuts
        self._bool_flag = bool_flag
        self._help_format = help_format
        self._keep_default_help = keep_default_help
        self._one_dash = one_dash
        self._override = override

        parser_kwargs = parser_kwargs or {}
        self._parser = ArgumentParser(**parser_kwargs)
        self._subparser = None

        commands, self._args_map = commands, args_map = self._read_args()
        if self._shortcuts:
            self._make_shortcuts([arg for values in args_map.values() for arg in values])
        subparser_kwargs = subparser_kwargs or dict(dest='command')
        self._setup_parser(commands, args_map, subparser_kwargs)

    def __getattribute__(self, item):
        if item == '_data' or item not in self._data:
            return object.__getattribute__(self, item)
        return self._data[item]

    def __str__(self):
        params = ", ".join(map(lambda x: f"{x[0]}={x[1]!r}", self._data.items()))
        return f"{self.__class__.__name__}({params})"

    @property
    def args_(self) -> List[Argument]:
        res = []
        for args in self._args_map.values():
            res.extend(args)
        return res

    def _get_nargs(self, typ, default):
        # just list
        if isinstance(typ, type) and issubclass(typ, list):
            if len(default or []) == 0:
                nargs = '*'
                typ = str
            else:
                nargs = '+'
                typ = type(default[0])
            return typ, nargs
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

    def _read_args(self):
        commands = []
        args = []
        args_map = {'base': args}
        # ann = self.__class__.__annotations__
        ann = getattr(self.__class__, '__annotations__', {})
        fields_with_value = self.__class__.__dict__
        fields = {k: None for k in ann if k not in fields_with_value}
        for key, value in fields_with_value.items():
            fields[key] = value
        for key, value in fields.items():  # type: str, Any
            if key.startswith('__'):
                continue
            if isinstance(value, Command):
                value.name = value.name or key
                commands.append(value)
                args = []
                args_map[value.name] = args
                continue
            if isinstance(value, Argument):
                value.dest = value.dest or key
                if self._override:
                    value.bool_flag = self._bool_flag
                    value.help_format = self._help_format
                    value.keep_default_help = self._keep_default_help
                    value.one_dash = self._one_dash
                args.append(value)
                continue
            # get from annotation or from default value or fallback to str
            typ = ann.get(key, str if value is None else type(value))

            typ, nargs = self._get_nargs(typ, value)
            args.append(
                Argument(
                    dest=key,
                    default=value,
                    type_=typ,
                    nargs=nargs,
                    help_format=self._help_format,
                    keep_default_help=self._keep_default_help,
                    bool_flag=self._bool_flag,
                    one_dash=self._one_dash,
                )
            )
        return commands, args_map

    def _make_shortcuts(self, args: List[Argument]):
        """
        Add shortcuts to arguments without defined aliases.
        """
        used = defaultdict(int)
        for arg in self.args_:
            used[arg.dest] += 1
        for arg in args:
            if arg.aliases != ():
                continue
            # aaa -> a, aaa_bbb -> ab
            a = ''.join(map(lambda e: e[0], arg.dest.split('_')))
            if a == arg.dest:
                continue
            used[a] += 1
            if used[a] > 1:
                a = f"{a}{used[a]}"
            arg.aliases = (a,)
        return args

    def _setup_parser(self, commands: List[Command], args_map: Dict[str, List[Argument]], subparser_kwargs: dict):
        _log_lines(logger.debug, pformat(commands))
        _log_lines(logger.debug, pformat(args_map))
        for arg in args_map['base']:
            arg.inject(self._parser)
        if commands:
            self._subparser = self._parser.add_subparsers(**subparser_kwargs)
            for command in commands:
                args = args_map[command.name]
                parser = command.make_parser(self._subparser)
                for arg in args:
                    arg.inject(parser)

    def parse(self, args=None):
        if isinstance(args, str):
            args = shlex.split(args)
        namespace = self._parser.parse_args(args)
        logger.debug(namespace)
        for key, value in namespace.__dict__.items():
            self._data[key] = value
        return self

    def tabulate(self, **kwargs):
        from tabulate import tabulate
        kwargs.setdefault('headers', ['arg', 'value'])
        return tabulate(self._data.items(), **kwargs)

    def print_table(self, **kwargs):
        print(self.tabulate(**kwargs))
        return self

    def print(self):
        print(self)
        return self


def _log_lines(log, text: str):
    for line in text.splitlines():
        log(line)
