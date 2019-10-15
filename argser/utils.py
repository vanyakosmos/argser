from argparse import ArgumentTypeError, HelpFormatter

from argser.consts import TRUE_VALUES, FALSE_VALUES


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
    return list in getattr(t, '__orig_bases__', []) or orig and issubclass(list, orig)


def add_color(text, fg, bg='', style=''):
    """
    :param text:
    :param fg: [30, 38)
    :param bg: [40, 48)
    :param style: [0, 8)
    :return:
    """
    format = ';'.join([str(style), str(fg), str(bg)])
    text = text or format
    return f'\x1b[{format}m{text}\x1b[0m'


def _green(text):
    return add_color(text, fg=32)


def _yellow(text):
    return add_color(text, fg=33)


class ColoredHelpFormatter(HelpFormatter):
    def __init__(self, prog, indent_increment=4, max_help_position=32, width=120):
        super().__init__(prog, indent_increment, max_help_position, width)

    def start_section(self, heading):
        heading = _yellow(heading)
        return super().start_section(heading)

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = _yellow('usage') + ': '
        return super().add_usage(usage, actions, groups, prefix)

    def _format_action_invocation(self, action):
        # noinspection PyProtectedMember
        header = super()._format_action_invocation(action)
        return _green(header)
