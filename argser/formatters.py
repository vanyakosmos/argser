import argparse
from argparse import Action

from argser.utils import colored
from argser.fields import Opt


class HelpFormatter(argparse.HelpFormatter):
    header_color = None
    invoc_color = None
    type_color = None
    default_color = None

    def __init__(self, prog, indent_increment=4, max_help_position=32, width=120):
        super().__init__(prog, indent_increment, max_help_position, width)

    def start_section(self, heading):
        heading = colored(heading, self.header_color)
        return super().start_section(heading)

    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = colored('usage', self.header_color) + ': '
        return super().add_usage(usage, actions, groups, prefix)

    def _get_type(self, action: Action):
        meta: Opt = getattr(action, '__meta', None)
        if not meta:
            return
        if isinstance(meta.type, type):
            typ = getattr(meta.type, '__name__', '-')
        else:
            typ = str(meta.type)
            typ = typ.replace('typing.', '')  # typing.List[str] -> List[str]
        return str(typ)

    def format_default_help(self, action: Action):
        # skip if current action is sub-parser
        if action.nargs == argparse.PARSER:
            return
        typ = self._get_type(action)
        if not typ:
            return
        typ = colored(typ, self.type_color)
        default = colored(repr(action.default), self.default_color)
        res = str(typ)
        if action.option_strings or action.default is not None:
            res += f", default: {default}"
        return res

    def format_action_help(self, action):
        if action.default == argparse.SUPPRESS:
            return action.help
        default_help_text = self.format_default_help(action)
        if default_help_text:
            if action.help:
                return f"{default_help_text}. {action.help}"
            return default_help_text
        return action.help

    def _format_action(self, action):
        action.help = self.format_action_help(action)
        # noinspection PyProtectedMember
        text = super()._format_action(action)
        invoc = self._format_action_invocation(action)
        s = len(invoc) + self._current_indent
        text = colored(text[:s], self.invoc_color) + text[s:]
        return text


class ColoredHelpFormatter(HelpFormatter):
    header_color = 'yellow'
    invoc_color = 'green'
    type_color = 'red'
    default_color = 'red'
