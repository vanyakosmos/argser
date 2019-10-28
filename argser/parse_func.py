import inspect

from types import FunctionType
from argser.fields import Arg, Opt
from argser.parser import parse_args, _get_type_and_nargs


def _get_default_args(func):
    signature = inspect.signature(func)
    return {k: v.default for k, v in signature.parameters.items() if v.default is not inspect.Parameter.empty}


def _make_argument(name, annotations: dict, defaults: dict):
    if name in defaults:
        arg = Opt(default=defaults[name])
    else:
        arg = Arg()
    typ, nargs = _get_type_and_nargs(annotations, name, arg.default)
    arg.type = typ
    arg.nargs = nargs
    return arg


def _call(func: FunctionType, *parser_args, **parser_kwargs):
    ann = func.__annotations__
    args = func.__code__.co_varnames
    args = args[:func.__code__.co_argcount]  # arguments excluding *args, **kwargs and kw only args
    defaults = _get_default_args(func)

    parser_kwargs.setdefault('parser_prog', func.__name__)

    Args = type('Args', (), {arg: _make_argument(arg, ann, defaults) for arg in args})
    args = parse_args(Args, *parser_args, **parser_kwargs)
    return func(**args.__dict__)


def call(func=None, *args, **kwargs):
    """
    Call provided function with arguments from command line.
    Parser will be generated based on function arguments.

    :attr:`*args`, :attr:`**kwargs` and keywords only arguments are currently not supported.

    :param func: function to call with parsed arguments.
    :param args: positional arguments for :func:`parse_args`
    :param kwargs: keyword arguments for :func:`parse_args`
    :return: result of :attr:`func` call with parsed parameters

    Example:

    >>> def foo(a, b: int, c=3.3, d=True):
    ...     return [a, b, c, d]
    >>> call(foo, '1 2 -c 3.4 --no-d')
    ['1', 2, 3.4, False]

    Can be used as decorator. Function will be called immediately with arguments provided in string or command line.

    >>> @call('1 2')
    ... def foo(a, b: int):
    ...     assert a == '1' and b == 2
    """
    if isinstance(func, FunctionType):
        return _call(func, *args, **kwargs)
    args = (func,) + args
    return lambda f: _call(f, *args, **kwargs)
