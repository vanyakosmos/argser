import re
from typing import TypeVar

Args = TypeVar('Args')

TRUE_VALUES = {'1', 'true', 't', 'okay', 'ok', 'affirmative', 'yes', 'y', 'totally'}
FALSE_VALUES = {'0', 'false', 'f', 'no', 'n', 'nope', 'nah'}
SUB_COMMAND_MARK = '__sub_command'
SUB_COMMAND_DEST_FMT = '__{name}_sub_command__'
RE_INV_CODES = re.compile(r"\x1b\[\d+[;\d]*m|\x1b\[\d*;\d*;\d*m")
