import logging
import re
import shlex
from argparse import ArgumentParser, HelpFormatter, Namespace
from collections import defaultdict
from typing import Any, List, Type

from argser.consts import Args, SUB_COMMAND_DEST_FMT, SUB_COMMAND_MARK
from argser.display import print_args, stringify
from argser.fields import Opt
from argser.logging import VERBOSE
from argser.utils import ColoredHelpFormatter, is_list_like_type

logger = logging.getLogger(__name__)


def _get_nargs(typ, default):
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


def _get_fields(cls: Type[Args], ann: dict):
    fields_with_value = cls.__dict__
    fields = {k: None for k in ann if k not in fields_with_value}
    for key, value in fields_with_value.items():
        # skip built-ins and inner classes
        if key.startswith('__') or isinstance(value, type):
            continue
        fields[key] = value
    # get fields from bases classes
    for base in cls.__bases__:
        for name, value in _get_fields(base, ann).items():
            # update without touching redefined values in inherited classes
            if name not in fields:
                fields[name] = value
    return fields


def _get_type_and_nargs(ann: dict, field_name: str, default):
    # get type from annotation or from default value or fallback to str
    default_type = None if default is None else type(default)
    typ = ann.get(field_name, default_type)
    logger.log(VERBOSE, f"init type {typ}, default: {default}")
    typ, nargs = _get_nargs(typ, default)
    logger.log(VERBOSE, f"type {typ}, nargs {nargs!r}")
    return typ, nargs


def _collect_annotations(cls: type):
    ann = getattr(cls, '__annotations__', {})
    for base in cls.__bases__:
        for name, typ in _collect_annotations(base).items():
            # update without touching redefined values in inherited classes
            if name not in ann:
                ann[name] = typ
    return ann


def _read_args(
    args_cls: Type[Args],
    override=False,
    bool_flag=True,
    one_dash=False,
    replace_underscores=True,
):
    args = []
    sub_commands = {}
    ann = _collect_annotations(args_cls)
    fields = _get_fields(args_cls, ann)
    for key, value in fields.items():  # type: str, Any
        logger.log(VERBOSE, f"reading {key!r}")
        if hasattr(value, SUB_COMMAND_MARK):
            sub_commands[key] = _read_args(
                value.__class__,
                bool_flag=bool_flag,
                one_dash=one_dash,
            )
            continue
        if isinstance(value, Opt):
            typ, nargs = _get_type_and_nargs(ann, key, value.default)
            value.dest = value.dest or key
            value.type = value.type or typ
            if value.action != 'append':
                value.nargs = nargs if value.nargs is None else value.nargs
            if override:
                value.bool_flag = bool_flag
                value.one_dash = one_dash
                value.replace_underscores = replace_underscores
            logger.log(VERBOSE, value.__dict__)
            args.append(value)
            continue
        typ, nargs = _get_type_and_nargs(ann, key, value)
        args.append(
            Opt(
                dest=key,
                type=typ,
                default=value,
                nargs=nargs,
                # extra
                bool_flag=bool_flag,
                one_dash=one_dash,
                replace_underscores=replace_underscores,
            )
        )
    return args_cls, args, sub_commands


def _make_parser(name: str, args: List[Opt], sub_commands: dict, formatter_class=HelpFormatter, **kwargs):
    logger.log(VERBOSE, f"parser {name}:\n - {args}\n - {sub_commands}")
    parser = ArgumentParser(formatter_class=formatter_class, **kwargs)
    for arg in args:
        arg.inject(parser)

    if not sub_commands:
        return parser

    sub_parser = parser.add_subparsers(dest=SUB_COMMAND_DEST_FMT.format(name=name))

    for name, (args_cls, args, sub_p) in sub_commands.items():
        p = _make_parser(name, args, sub_p)
        parser_kwargs = getattr(args_cls, '__kwargs', {})
        parser_kwargs.setdefault('formatter_class', formatter_class)
        sub_parser.add_parser(name, parents=[p], add_help=False, **parser_kwargs)

    return parser


def _set_values(parser_name: str, res: Args, namespace: Namespace, args: List[Opt], sub_commands: dict):
    logger.log(VERBOSE, f'setting values for: {res}')
    for arg in args:
        setattr(res, arg.dest, namespace.__dict__.get(arg.dest))
    for name, (args_cls, args, sub_c) in sub_commands.items():
        # set values only if sub-command was chosen
        if getattr(namespace, SUB_COMMAND_DEST_FMT.format(name=parser_name)) == name:
            sub = getattr(res, name)
            setattr(res, name, sub)
            _set_values(name, sub, namespace, args, sub_c)
        # otherwise nullify sub-command
        else:
            setattr(res, name, None)
    logger.log(VERBOSE, f'setting complete: {res}')


def _make_shortcut(name: str):
    """aaa -> a, aaa_bbb -> ab"""
    parts = name.split('_')
    return ''.join([p[0] for p in parts if len(p) > 0])


def _make_shortcuts(args: List[Opt]):
    """
    Add shortcuts to arguments without defined aliases.
    todo: deal with duplicated names
    """
    used = defaultdict(lambda: False)
    for arg in args:
        for n in arg.names:
            used[n] = True
    for arg in args:
        if arg.aliases != ():
            continue
        a = _make_shortcut(arg.dest)
        if used[a] > 0:
            continue
        used[a] = True
        arg.aliases = (a,)


def _make_shortcuts_sub_wise(args: List[Opt], sub_commands: dict):
    _make_shortcuts(args)
    for name, (args_cls, args, sub_p) in sub_commands.items():
        _make_shortcuts_sub_wise(args, sub_p)


def sub_command(args_cls: Type[Args], **kwargs) -> Args:
    """
    :param args_cls: data holder
    :param kwargs: additional parser kwargs
    :return:
    """
    setattr(args_cls, '__str__', stringify)
    setattr(args_cls, '__repr__', stringify)
    setattr(args_cls, '__kwargs', kwargs)
    setattr(args_cls, SUB_COMMAND_MARK, True)
    return args_cls()


def _add_prefixed_key(source: dict, target: dict, prefix: str):
    for key, value in source.items():
        m = re.match(f'{prefix}(.+)', key)
        if m:
            target[m[1]] = value


def _setup_argcomplete(parser, **kwargs):
    try:
        import argcomplete
        argcomplete.autocomplete(parser, **kwargs)
    except ImportError:
        logger.log(VERBOSE, "argcomplete is not installed")


def parse_args(
    args_cls: Type[Args],
    args=None,
    show=None,
    print_fn=None,
    colorize=True,
    shorten=False,
    make_shortcuts=True,
    replace_underscores=True,
    bool_flag=True,
    one_dash=False,
    override=False,
    parser_kwargs=None,
    tabulate_kwargs=None,
    argcomplete_kwargs=None,
    **kwargs,
) -> Args:
    """
    Parse arguments from string or command line and return populated instance of `args_cls`.

    :param args_cls: class with defined arguments
    :param args: arguments to parse. Either string or list of strings or None (to read from sys.args)
    :param show:
        if True - print arguments in one line
        if 'table' - print arguments as table
    :param print_fn:
    :param colorize: add colors to the help message and arguments printing
    :param shorten: shorten long text (eg long default value)
    :param make_shortcuts: make short version of arguments: --abc -> -a, --abc_def -> --ad
    :param replace_underscores: replace underscores in argument names with dashes
    :param bool_flag:
        if True then read bool from argument flag: `--arg` is True, `--no-arg` is False,
        otherwise check if arg value and truthy or falsy: `--arg 1` is True `--arg no` is False
    :param one_dash: use one dash for long names: `-name` instead of `--name`
    :param override: override values above on Arg's
    :param parser_kwargs: root parser kwargs
    :param tabulate_kwargs: tabulate additional kwargs + some custom fields:
        cols: number of columns. Can be 'auto' - len(args)/N, int - just number of columns,
        'sub' / 'sub-auto' / 'sub-INT' - split by sub-commands,
        gap: string, space between tables/columns
    :param argcomplete_kwargs: argcomplete kwargs
    :param kwargs: params for tabulate and parser - tabulate_ARG=VAL or parser_ARG=VAL
    """
    tabulate_kwargs = tabulate_kwargs or {}
    _add_prefixed_key(kwargs, tabulate_kwargs, 'tabulate_')
    parser_kwargs = parser_kwargs or {}
    _add_prefixed_key(kwargs, parser_kwargs, 'parser_')
    argcomplete_kwargs = argcomplete_kwargs or {}
    _add_prefixed_key(kwargs, argcomplete_kwargs, 'argcomplete_')

    if isinstance(args, str):
        args_to_parse = shlex.split(args)
    else:
        args_to_parse = args

    args_cls, args, sub_commands = _read_args(
        args_cls,
        override=override,
        bool_flag=bool_flag,
        one_dash=one_dash,
        replace_underscores=replace_underscores,
    )
    if make_shortcuts:
        _make_shortcuts_sub_wise(args, sub_commands)
    if colorize:
        parser_kwargs.setdefault('formatter_class', ColoredHelpFormatter)
    parser = _make_parser('root', args, sub_commands, **parser_kwargs)
    _setup_argcomplete(parser, **argcomplete_kwargs)

    namespace = parser.parse_args(args_to_parse)
    logger.log(VERBOSE, namespace)

    result = sub_command(args_cls)
    _set_values('root', result, namespace, args, sub_commands)

    print_args(result, variant=show, print_fn=print_fn, colorize=colorize, shorten=shorten, **tabulate_kwargs)
    return result
