import re
from argparse import ArgumentTypeError
from functools import partial

import termcolor

from argser.consts import FALSE_VALUES, TRUE_VALUES, Args

RE_INV_CODES = re.compile(r"\x1b\[\d+[;\d]*m|\x1b\[\d*;\d*;\d*m")


def colored(text, color=None):
    if color is None:
        return text
    return termcolor.colored(text, color=color)


def vlen(s: str):
    """
    Visible width of a printed string. ANSI color codes are removed.
    Short version of private function from tabulate. Copied just in case.

    >>> vlen("world")
    5
    >>> vlen('\x1b[31mhello\x1b[0m')
    5
    """
    return len(RE_INV_CODES.sub("", s))


def str2bool(v: str):
    """Convert string to boolean."""
    v = v.lower()
    if v in TRUE_VALUES:
        return True
    elif v in FALSE_VALUES:
        return False
    raise ArgumentTypeError('Boolean value expected.')


def is_list_like_type(t):
    """Check if provided type is List or List[str] or similar."""
    orig = getattr(t, '__origin__', None)
    return list in getattr(t, '__orig_bases__', []) or bool(orig) and issubclass(list, orig)


class colors:
    red = partial(colored, color='red')
    green = partial(colored, color='green')
    yellow = partial(colored, color='yellow')
    blue = partial(colored, color='blue')
    # partial will prevent 'self' injection when called from ColoredHelpFormatter
    no = partial(lambda x: x)


def args_to_dict(args: Args) -> dict:
    return {key: value for key, value in args.__dict__.items() if not key.startswith('_')}


def with_args(func, options, *args, **kwargs):
    data = args_to_dict(options)
    data.update(kwargs)
    return func(*args, **data)
