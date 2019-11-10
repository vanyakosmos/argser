import logging
import re
import shlex
from argparse import ArgumentParser, Namespace
from typing import Any, List, Type

from argser.consts import Args, SUB_COMMAND_MARK
from argser.display import print_args, stringify
from argser.fields import Opt
from argser.logging import VERBOSE
from argser.formatters import ColoredHelpFormatter, HelpFormatter

logger = logging.getLogger(__name__)


def _collect_annotations(cls: type):
    ann = getattr(cls, '__annotations__', {}).copy()  # don't modify class annotation
    for base in cls.__bases__:
        for name, typ in _collect_annotations(base).items():
            # update without touching redefined values in inherited classes
            if name not in ann:
                ann[name] = typ
    return ann


def _get_fields(cls: Type[Args]):
    ann = getattr(cls, '__annotations__', {})
    fields_with_value = {
        key: value
        for key, value in cls.__dict__.items()
        if not key.startswith('_')
        and not isinstance(value, type)  # skip built-ins and inner classes
    }
    fields = {
        k: None for k in ann if k not in fields_with_value and not k.startswith('_')
    }
    fields.update(**fields_with_value)
    # get fields from bases classes
    for base in cls.__bases__:
        if base is object:
            continue
        for name, value in _get_fields(base).items():
            # update without touching redefined values in inherited classes
            if name not in fields:
                fields[name] = value
    return fields


def _read_args(
    args_cls: Type[Args],
    parser_name='root',
    override=False,
    bool_flag=True,
    prefix='--',
    repl=('_', '-'),
):
    args = []
    sub_commands = {}
    ann = _collect_annotations(args_cls)
    fields = _get_fields(args_cls)
    for key, value in fields.items():  # type: str, Any
        logger.log(VERBOSE, f"reading {key!r}")
        annotation = ann.get(key)
        dest = _join_names(parser_name, key)

        if hasattr(value, SUB_COMMAND_MARK):
            sub_commands[key] = _read_args(
                value.__class__, dest, bool_flag=bool_flag, prefix=prefix, repl=repl
            )
            continue
        if isinstance(value, Opt):
            option = value
            option.guess_type_and_nargs(annotation)
            if not option.dest:
                option.set_dest(dest)
        else:
            default, constructor, help = value, None, None
            if isinstance(value, tuple):
                if len(value) == 2:
                    default, help = value
                elif len(value) == 3:
                    default, constructor, help = value
                else:
                    raise ValueError(
                        f"invalid value for {key}. "
                        f"Tuple structure should be: (default, help) or "
                        f"(default, constructor, help)"
                    )
            option = Opt(
                dest=dest,
                default=default,
                help=help,
                constructor=constructor,
                bool_flag=bool_flag,
                prefix=prefix,
                repl=repl,
            )
            option.guess_type_and_nargs(annotation)

        if override:
            option.bool_flag = bool_flag
            option.prefix = prefix
            option.repl = repl
        logger.log(VERBOSE, option.__dict__)
        args.append(option)
        setattr(args_cls, key, option)
    return args_cls, args, sub_commands


def _join_names(*names: str):
    return '__'.join(names)


def _uwrap(*names: str):
    return f'__{_join_names(*names)}__'


def _make_parser(
    name: str,
    args: List[Opt],
    sub_commands: dict,
    *,
    parser=None,
    formatter_class=HelpFormatter,
    **kwargs,
):
    """
    Recursively make parser and sub-parsers.

    :param name: name of parser prefixed with parent parser name
    :param args:
    :param sub_commands:
    :param formatter_class:
    :param kwargs:
    :return:
    """
    logger.log(VERBOSE, f"parser {name}:\n - {args}\n - {sub_commands}\n - {parser}")
    parser = parser or ArgumentParser(formatter_class=formatter_class, **kwargs)
    parser.prefix_chars = ''.join({a.prefix for a in args})  # get all possible prefixes

    for arg in args:
        arg.inject(parser)

    if not sub_commands:
        return parser

    sub_parser = parser.add_subparsers(dest=_uwrap(name))

    for sub_name, (args_cls, args, sub_p) in sub_commands.items():
        p = getattr(args_cls, '__parser', None)
        parser_kwargs = getattr(args_cls, '__kwargs', {})
        parser_kwargs.setdefault('formatter_class', formatter_class)

        p = _make_parser(
            _join_names(name, sub_name),
            args,
            sub_p,
            parser=p,
            formatter_class=formatter_class,
        )
        sub_parser.add_parser(sub_name, parents=[p], add_help=False, **parser_kwargs)

    return parser


def _set_values(
    parser_name: str,
    res: Args,
    namespace: Namespace,
    args: List[Opt],
    sub_commands: dict,
):
    """
    Recursively extract attributes from namespace and add them to :attr:`res`.

    :param parser_name: name of parser prefixed with parent parser name
    :param res:
    :param namespace:
    :param args:
    :param sub_commands:
    :return:
    """
    logger.log(VERBOSE, f'setting values for: {parser_name} ~ {res}')
    for arg in args:
        setattr(res, arg.name, namespace.__dict__.get(arg.dest))

    for name, (args_cls, args, sub_c) in sub_commands.items():
        # set values only if sub-command was chosen
        if getattr(namespace, _uwrap(parser_name)) == name:
            sub = getattr(res, name)
            # Reinitialize instance of sub-command so that nullification of attribute
            # would not touch original class and inner sub-commands. Mostly useful for
            # tests.
            sub = sub.__class__()
            setattr(res, name, sub)
            sub_parser_name = _join_names(parser_name, name)
            _set_values(sub_parser_name, sub, namespace, args, sub_c)
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
    Add shortcuts to arguments without defined options.
    """
    used = set()
    for arg in args:
        for n in arg.option_names:
            used.add(n)
    for arg in args:
        # user specified own options - skip shortcuts generation
        if arg.option_names != [arg.name]:
            continue
        a = _make_shortcut(arg.name)
        if a in used:
            continue
        used.add(a)
        arg.option_names += [a]


def _make_shortcuts_sub_wise(args: List[Opt], sub_commands: dict):
    _make_shortcuts(args)
    for name, (args_cls, args, sub_p) in sub_commands.items():
        _make_shortcuts_sub_wise(args, sub_p)


def sub_command(args_cls: Type[Args], parser=None, **kwargs) -> Args:
    """
    Add sub-command to the parser.

    :param args_cls: data holder
    :param parser: predefined parser
    :param kwargs: additional parser kwargs
    :return: instance of :attr:`args_cls` with added metadata

    >>> class Sub:
    ...     a = 1
    >>> class Data:
    ...     sub = sub_command(Sub)
    >>> args = parse_args(Data, 'sub -a 2')
    >>> assert args.sub.a == 2
    """
    setattr(args_cls, '__str__', stringify)
    setattr(args_cls, '__repr__', stringify)
    setattr(args_cls, '__parser', parser)
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
        logger.debug("Argcomplete is not installed. Skipping integration.")


def make_parser(
    args_cls: Type[Args],
    parser=None,
    make_shortcuts=True,
    bool_flag=True,
    prefix='--',
    repl=('_', '-'),
    override=False,
    parser_kwargs=None,
    argcomplete_kwargs=None,
    **kwargs,
):
    """
    Create arguments parser based on :attr:`args_cls`.

    :param args_cls: class with defined arguments
    :param parser: predefined parser
    :param make_shortcuts: make short version of arguments: ``--abc -> -a``,
        ``--abc_def -> --ad``
    :param bool_flag:
        if True then read bool from argument flag:
        ``--arg`` is True, ``--no-arg`` is False,
        otherwise check if arg value and truthy or falsy:
        `--arg 1` is True `--arg no` is False
    :param prefix: default prefix before options.
        For ``--``: ``aaa -> --aaa``, ``b -> -b``
    :param repl: auto-replace some char with another char in option names.
        For ``('_', '-')``: ``lang_name -> lang-name``
    :param override: override values above on Arg's
    :param parser_kwargs: root parser kwargs
    :param argcomplete_kwargs: argcomplete kwargs
    :param kwargs: additional params for parser or argcomplete,
        should be prefixed with target name
    :return: instance of ArgumentParser and tuple with options
        (main_options, sub_command_options)
    """

    args_cls, args, sub_commands = _read_args(
        args_cls, override=override, bool_flag=bool_flag, prefix=prefix, repl=repl
    )
    if make_shortcuts:
        _make_shortcuts_sub_wise(args, sub_commands)
    # setup parser
    parser_kwargs = parser_kwargs or {}
    _add_prefixed_key(kwargs, parser_kwargs, 'parser_')
    parser_kwargs.setdefault('formatter_class', ColoredHelpFormatter)
    parser = _make_parser('root', args, sub_commands, parser=parser, **parser_kwargs)
    # argcomplete
    argcomplete_kwargs = argcomplete_kwargs or {}
    _add_prefixed_key(kwargs, argcomplete_kwargs, 'argcomplete_')
    _setup_argcomplete(parser, **argcomplete_kwargs)
    return parser, (args, sub_commands)


def populate_holder(
    parser: ArgumentParser, args_cls: Type[Args], options: tuple, args=None
):
    """
    Parse provided string or command line and populate :attr:`args_cls`
    with parsed values.

    :param parser: generated parser
    :param args_cls: arguments holder
    :param options: tuple with root arguments and sub-command arguments
    :param args: string to parse or ``None``
    :return: instance of :attr:`args_cls` with populated fields.
    """
    if isinstance(args, str):
        args = shlex.split(args)
    namespace = parser.parse_args(args)
    logger.log(VERBOSE, namespace)

    result = sub_command(args_cls)
    args, sub_commands = options
    _set_values('root', result, namespace, args, sub_commands)
    setattr(result, '__namespace__', namespace)
    return result


def parse_args(
    args_cls: Type[Args],
    args=None,
    *,
    show=None,
    print_fn=None,
    shorten=False,
    fill=40,
    tabulate_kwargs=None,
    **kwargs,
) -> Args:
    """
    Parse arguments from string or command line and return populated
    instance of `args_cls`.

    :param args_cls: class with defined arguments
    :param args: arguments to parse. Either string or list of strings or None
        (to read from sys.args)
    :param show:
        if 'table' - print arguments as table
        if truthy value - print arguments in one line
        if falsy value - don't print anything
    :param print_fn:
    :param shorten: shorten long text (eg long default value)
    :param fill: max width of text, wraps long paragraph
    :param tabulate_kwargs: tabulate additional kwargs + some custom fields:
        cols: number of columns. Can be 'auto' - len(args)/N,
        int - just number of columns,
        'sub' / 'sub-auto' / 'sub-INT' - split by sub-commands,
        gap: string, space between tables/columns
    :param kwargs: parameters for parser generation.
        Check out :func:`make_parser` for more params
    :return: instance of :attr:`args_cls` with populated attributed based of command
        line arguments.

    >>> class Data:
    ...     a: int
    ...     b = 4.5
    ...     c = True
    >>> args = parse_args(Data, '-a 1 -b 2.2 --no-c')
    >>> assert args.a == 1 and args.b == 2.2 and args.c is False
    """
    parser, options = make_parser(args_cls, **kwargs)
    result = populate_holder(parser, args_cls, options, args)

    tabulate_kwargs = tabulate_kwargs or {}
    _add_prefixed_key(kwargs, tabulate_kwargs, 'tabulate_')
    if show:
        print_args(
            result,
            variant=show,
            print_fn=print_fn,
            shorten=shorten,
            fill=fill,
            **tabulate_kwargs,
        )
    return result
