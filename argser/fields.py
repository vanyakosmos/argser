import logging
import re
import textwrap
from argparse import ArgumentParser, SUPPRESS
from functools import partial
from typing import Tuple, Optional, List

from argser.exceptions import ArgserException
from argser.logging import VERBOSE
from argser.utils import str2bool, is_list_like_type

RE_OPT_PREFIX = re.compile(r'^([^\w]*)\w.*$')
logger = logging.getLogger(__name__)


class Opt:
    """Optional Argument (eg: --arg, -a)"""

    def __init__(
        self,
        *options: str,
        dest: str = None,
        default=None,
        type=None,
        nargs=None,
        help=None,
        metavar=None,
        action=None,
        # argcomplete
        completer=None,
        # extra
        factory=None,
        bool_flag=True,
        prefix='--',
        repl=('_', '-'),
        **kwargs,
    ):
        """
        :param options: list of strings to be used as arguments name. Can be modified
            by :attr:`prefix` and :attr:`repl`
        :param dest: destination in the namespace, can be prefixed with sub-parser name
        :param default: default value
        :param type: type of value that will be displayed in help message and used for
            type hints.
        :param nargs: number of values
        :param help: help text to display in help message alongside arguments
        :param metavar: thingy that will be displayed near options with values: --args
            METAVAR
        :param action: argparse action: count, append, store_const, version
        :param completer: argcomplete completion function
        :param factory: callable that accepts a string and returns desirable value,
            default is :attr:`type`
        :param bool_flag: if True then read bool from argument flag: `--arg` is True,
            `--no-arg` is False, otherwise check if arg value and truthy or falsy:
            `--arg 1` is True `--arg no` is False
        :param prefix: automatically prefix options with prefix.
            If option is single letter then prefix will also be shortened.
            See :meth:`set_options`
        :param repl: update provided options: replace first value in tuple with second
            value
        :param kwargs: extra arguments for `parser.add_argument`
        """
        assert (
            len(set(prefix)) < 2
        ), "prefix should consist from the same characters, eg: --, ++, ..."

        self.prefix = prefix
        self.repl = repl
        self.option_names = list(options)
        self.metavar = metavar
        self.dest = self.set_dest(dest)
        self.type = type
        self.default = default
        self.nargs = nargs
        self.help = help
        self.action = action
        # argcomplete
        self.completer = completer
        # extra
        self.factory = self._pick_factory(factory)
        self.bool_flag = bool_flag
        self.extra = kwargs

    def __str__(self):
        cls_name = self.__class__.__name__
        names = ', '.join(self.options) or '-'
        type_name = getattr(self.type, '__name__', None)
        return f"{cls_name}({names}, type={type_name}, default={self.default!r})"

    def __repr__(self):
        return str(self)

    def pretty_format(self):
        # moved from __repr__ because it is too long
        cls_name = self.__class__.__name__
        start = f'{cls_name}('
        names = ', '.join(self.options) or '-'
        pairs = [names]
        for field, value in self.__dict__.items():
            pairs.append(f'{field}={value!r}')
        pairs = ',\n'.join(pairs)
        pairs = textwrap.indent(pairs, ' ' * len(start)).strip()
        return f'{start}{pairs})'

    @property
    def name(self):
        """Destination w/o parser prefix."""
        if self.dest:
            return self.dest.split('__')[-1]

    @property
    def options(self):
        return self.make_options(*self.option_names)

    @property
    def no_options(self):
        sep = self.repl[1] if self.repl else '-'
        res = []
        for opt in self.options:
            # prefix defined and used in this option
            if self.prefix and opt.startswith(self.prefix[:1]):
                prefix = self.prefix
            else:
                m = RE_OPT_PREFIX.match(opt)
                prefix = m[1]
            base = opt.lstrip(prefix)
            key = f'{prefix}no{sep}{base}'
            res.append(key)
        return res

    def set_dest(self, dest: str):
        """Setup destination and related attributes. Should be called only once."""
        if not dest:
            return
        if getattr(self, 'dest', None):
            logger.warning("destination was already defined")
            return
        self.dest = dest
        self.option_names += [self.name]
        self.metavar = self.metavar or self.make_metavar()
        return self.dest

    def _replace(self, opt: str, repl: Optional[Tuple[str, str]]):
        if not repl:
            return opt
        sub, join = repl
        return join.join(opt.split(sub))

    def _prefix(self, opt: str, prefix: str):
        if not opt[0].isalpha():
            return opt
        if len(opt) == 1:
            return f'{prefix[:1]}{opt}'
        return f'{prefix}{opt}'

    def make_options(self, *options: str, prefix=None, repl=None):
        """
        >>> Opt().make_options(
        ...     'aaa', 'a', 'foo_bar', '+already_has', prefix='--', repl=('_', '+')
        ... )
        ['--aaa', '-a', '--foo+bar', '+already+has']
        """
        prefix = prefix or self.prefix
        repl = repl or self.repl
        options = map(partial(self._replace, repl=repl), options)
        options = map(partial(self._prefix, prefix=prefix), options)
        options = list(options)
        return options

    def make_metavar(self):
        if self.dest:
            return self.name[0].upper()

    def _guess_nargs(self, typ, default):
        """
        if type is list then generate new type and nargs based on default value
        if type in typing List[...] then extract inner type
        """
        # just list
        if typ is list:
            if len(default or []) == 0:
                nargs = '*'
                typ = str
            else:
                nargs = '+'
                typ = type(default[0])
            return typ, nargs
        #  List or List[str] or similar
        if is_list_like_type(typ):
            if typ.__args__ and isinstance(typ.__args__[0], type):
                typ = typ.__args__[0]
            else:
                typ = str
            nargs = '*' if len(default or []) == 0 else '+'
            return typ, nargs
        # non list type
        return typ, None

    def _guess_type_and_nargs(self, annotation, default, default_type):
        # get type from annotation or from default value or fallback to str
        if not default_type:
            default_type = str if default is None else type(default)
        typ = annotation or default_type
        logger.log(VERBOSE, f"init type {typ}, default: {default}")
        typ, nargs = self._guess_nargs(typ, default)
        logger.log(VERBOSE, f"type {typ}, nargs {nargs!r}")
        return typ, nargs

    def _restore_type(self, typ, nargs, default):
        if isinstance(nargs, int) or nargs in ('*', '+') or isinstance(default, list):
            return List[typ]
        return typ

    def _pick_factory(self, *values):
        if len(values) == 1 and (values[0] is None or isinstance(values[0], str)):
            return values[0]
        for val in values:
            if callable(val):
                return val
        else:
            raise ArgserException(f"Invalid factories: {values}.")

    def guess_type_and_nargs(self, annotation=None):
        """Based on annotation and default value guess type, nargs and factory."""
        typ, nargs = self._guess_type_and_nargs(annotation, self.default, self.type)
        if self.action == 'append':
            nargs = None
        self.nargs = self.nargs or nargs
        # user specified type -> annotation -> guessed type
        self.type = self.type or annotation or self._restore_type(typ, self.nargs, self.default)
        self.factory = self._pick_factory(self.factory, typ)
        return typ, nargs

    def _params(self, exclude=(), **kwargs):
        params = dict(
            dest=self.dest,
            default=self.default,
            type=self.factory,
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
            params = self._params(exclude=('type', 'nargs', 'metavar', 'action'))
            action = parser.add_argument(*self.options, action='store_true', **params)
            parser.set_defaults(**{self.dest: self.default})
            params['default'] = SUPPRESS  # don't print help message for second flag
            if 'help' in params:
                del params['help']
            parser.add_argument(*self.no_options, action='store_false', **params)
            return action
        params = self._params(type=str2bool)
        return parser.add_argument(*self.options, **params)

    def _inject(self, parser: ArgumentParser):
        params = self._params()
        action = params.get('action')
        if (
            action
            in ('store_const', 'store_true', 'store_false', 'append_const', 'version', 'count',)
            and 'type' in params
        ):
            params.pop('type')
        if action in ('store_true', 'store_false', 'count', 'version') and 'metavar' in params:
            params.pop('metavar')
        logger.log(VERBOSE, f"option: {self.options}")
        logger.log(VERBOSE, f"params: {params}")
        action = parser.add_argument(*self.options, **params)
        return action

    def inject(self, parser: ArgumentParser):
        logger.log(VERBOSE, f"adding {self.dest} to the parser")
        if self.factory is bool:
            action = self.inject_bool(parser)
        else:
            action = self._inject(parser)
        if callable(self.completer):
            action.completer = self.completer
        logger.log(VERBOSE, action)
        setattr(action, '__meta', self)  # will be useful in help formatter
        return action


class Arg(Opt):
    """Positional Argument"""

    def __init__(self, **kwargs):
        kwargs.update(bool_flag=False)
        super().__init__(**kwargs)

    def make_metavar(self):
        return self.name

    def make_options(self, *options: str, prefix=None, repl=None):
        return []
