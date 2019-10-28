import logging
from argparse import ArgumentParser, SUPPRESS
from typing import Iterable

from argser.logging import VERBOSE
from argser.utils import str2bool

logger = logging.getLogger(__name__)


class Opt:
    """Option"""
    def __init__(
        self,
        dest: str = None,
        default=None,
        type=None,
        nargs=None,
        aliases: Iterable[str] = (),
        help=None,
        metavar=None,
        action='store',
        # argcomplete
        completer=None,
        # extra
        bool_flag=True,
        one_dash=False,
        replace_underscores=True,
        **kwargs,
    ):
        """
        :param dest:
        :param default:
        :param type:
        :param nargs:
        :param aliases:
        :param help:
        :param bool_flag:
            if True then read bool from argument flag: `--arg` is True, `--no-arg` is False,
            otherwise check if arg value and truthy or falsy: `--arg 1` is True `--arg no` is False
        :param one_dash: use one dash for long names: `-name` instead of `--name`
        :param replace_underscores: replace underscores in argument names with dashes
        :param kwargs: extra arguments for `parser.add_argument`
        """
        self.dest = dest
        self.type = type
        self.default = default
        self.nargs = nargs
        self.aliases = aliases
        self.help = help
        self._metavar = metavar
        self.action = action
        # argcomplete
        self.completer = completer
        # extra
        self.bool_flag = bool_flag
        self.one_dash = one_dash
        self.replace_underscores = replace_underscores
        self.extra = kwargs

    def __str__(self):
        names = ', '.join(self.keys()) or '-'
        type_name = getattr(self.type, '__name__', None)
        return f"Arg({names}, type={type_name}, default={self.default!r})"

    def __repr__(self):
        return str(self)

    @property
    def metavar(self):
        if self._metavar:
            return self._metavar
        if self.dest:
            return self.dest[0].upper()

    @property
    def names(self):
        names = [self.dest, *self.aliases]
        return [n for n in names if n]

    def keys(self, prefix=None):
        names = self.names
        if self.replace_underscores:
            names = ['-'.join(n.split('_')) for n in names]
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
            metavar=self.metavar,
            action=self.action,
        )
        params.update(**kwargs)
        params.update(**self.extra)
        logger.log(VERBOSE, params)
        for key in exclude:
            params.pop(key)
        return {k: v for k, v in params.items() if v is not None}

    def inject_bool(self, parser: ArgumentParser):
        if self.bool_flag and self.nargs not in ('*', '+'):
            params = self.params(exclude=('type', 'nargs', 'metavar', 'action'))
            action = parser.add_argument(*self.keys(), action='store_true', **params)
            parser.set_defaults(**{self.dest: self.default})
            params['default'] = SUPPRESS  # don't print help message for second flag
            if 'help' in params:
                del params['help']
            parser.add_argument(*self.keys(prefix='no-'), action='store_false', **params)
            return action
        params = self.params(type=str2bool)
        return parser.add_argument(*self.keys(), **params)

    def inject(self, parser: ArgumentParser):
        logger.log(VERBOSE, f"adding {self.dest} to the parser")
        if self.type is bool:
            action = self.inject_bool(parser)
        else:
            params = self.params()
            action = params.get('action')
            if action in (
                'store_const', 'store_true', 'store_false', 'append_const', 'version', 'count'
            ) and 'type' in params:
                params.pop('type')
            if action in ('store_true', 'store_false', 'count', 'version') and 'metavar' in params:
                params.pop('metavar')
            action = parser.add_argument(*self.keys(), **params)
        if callable(self.completer):
            action.completer = self.completer
        return action


class Arg(Opt):
    """Positional Argument"""
    def __init__(self, **kwargs):
        kwargs.update(bool_flag=False)
        super().__init__(**kwargs)

    @property
    def metavar(self):
        if self._metavar:
            return self._metavar

    def params(self, exclude=(), **kwargs):
        exclude += ('dest',)
        return super().params(exclude=exclude, **kwargs)

    def keys(self, prefix=None):
        return [self.dest]
