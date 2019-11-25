import math
import re
import textwrap
from collections import defaultdict
from typing import List

from argser.consts import Args, SUB_COMMAND_MARK
from argser.utils import colors, vlen, args_to_dict


def stringify(args: Args, shorten=False):
    pairs = []
    for key, value in args_to_dict(args).items():
        if hasattr(value, SUB_COMMAND_MARK):
            value = stringify(value, shorten)
        else:
            value = _format_value(value, shorten, fill=False)
        pairs.append(f"{colors.green(key)}={value}")

    pairs = ', '.join(pairs)
    cls_name = colors.yellow(args.__class__.__name__)
    return f"{cls_name}({pairs})"


def _get_table(args: Args):
    data = []
    for key, value in args_to_dict(args).items():
        if hasattr(value, SUB_COMMAND_MARK):
            sub_data = _get_table(value)
            data.extend([(f"{key}__{k}", v) for k, v in sub_data])
        else:
            data.append((key, value))
    return data


def _merge_str_cols(columns: List[str], gap='   '):
    parts = [c.splitlines() for c in columns]
    res = []
    col_widths = [max(map(vlen, part)) for part in parts]

    # for each line
    for i in range(max(map(len, parts))):
        row = ''
        # iterate over columns
        for j, part in enumerate(parts):
            # get row of current column
            chunk = part[i] if i < len(part) else ''
            row += chunk + ' ' * (col_widths[j] - vlen(chunk))
            if j != len(parts) - 1:
                row += gap
        res.append(row)
    return '\n'.join(res)


def _get_cols_value(data, cols) -> int:
    if cols == 'auto':
        return math.ceil(len(data) / 9)
    if isinstance(cols, str):
        return int(cols)
    if not cols:
        return 1
    return cols


def _split_by_cols(data: list, cols):
    cols = _get_cols_value(data, cols)
    parts = []
    part_size = math.ceil(len(data) / cols)
    while data:
        parts.append(data[:part_size])
        data = data[part_size:]
    return parts


def _split_by_sub(data: list, cols=1):
    store = defaultdict(list)
    for key, value in data:
        m = re.match(r'^(.+)__.+', key)
        store[m and m[1]].append((key, value))
    res = []
    for sub in store.values():
        res.extend(_split_by_cols(sub, cols))
    return res


def _colorize_table_headers(data, kwargs):
    h_arg, h_value = kwargs['headers']
    kwargs['headers'] = colors.yellow(h_arg), colors.yellow(h_value)
    for i, (key, value) in enumerate(data):
        data[i] = colors.green(key), value


def _get_shorten(shorten):
    if shorten is True:
        return 40
    if shorten is False:
        return 400
    return shorten


def _format_value(value, shorten=False, fill=40):
    if value is None:
        return colors.red('-')
    text = repr(value)
    shorten = _get_shorten(shorten)
    if shorten:
        text = textwrap.shorten(text, width=shorten, placeholder='...')
    if fill:
        text = textwrap.fill(text, width=fill)
    return text


def make_table(
    args: Args, preset=None, cols='sub-auto', gap='   ', shorten=False, fill=40, **kwargs,
):
    from tabulate import tabulate

    kwargs.setdefault('headers', ['arg', 'value'])
    data = _get_table(args)

    _colorize_table_headers(data, kwargs)

    for i, (key, value) in enumerate(data):
        value = _format_value(value, shorten, fill)
        data[i] = key, value

    if preset == 'fancy':
        cols = 'sub-auto'
        gap = ' ~ '
        kwargs['tablefmt'] = 'fancy_grid'

    if isinstance(cols, str) and cols.startswith('sub'):
        m = re.match(r'sub-(.+)', cols)
        c = m and m[1] or 1
        parts = _split_by_sub(data, cols=c)
        parts = [tabulate(sub, **kwargs) for sub in parts]
        return _merge_str_cols(parts, gap)
    parts = _split_by_cols(data, cols)
    parts = [tabulate(sub, **kwargs) for sub in parts]
    return _merge_str_cols(parts, gap)


def make_tree(args: Args, shorten=False, fill=40, indent=''):
    shorten = _get_shorten(shorten)

    parts = [colors.yellow(args.__class__.__name__)]
    data = args_to_dict(args)
    for i, (field, value) in enumerate(data.items()):
        field = colors.green(field)
        p = '└' if i == len(data) - 1 else '├'

        if hasattr(value, SUB_COMMAND_MARK):
            value = make_tree(value, shorten=shorten, fill=fill, indent=indent + '  ')
            parts.append(f"{indent}{p} {field} = {value}")
            continue

        lines = _format_value(value, shorten, fill).splitlines()
        if len(lines) > 1:
            p = '├'
        parts.append(f"{indent}{p} {field} = {lines[0]}")
        gap = ' ' * vlen(field)
        for j, line in enumerate(lines[1:]):
            if j == len(lines) - 2 and i == len(data) - 1:
                p = '└'
            else:
                p = '│'
            parts.append(f"{indent}{p} {gap}   {line}")

    return '\n'.join(parts)


def print_args(args: Args, variant=None, print_fn=None, shorten=False, fill=40, **kwargs):
    """
    Pretty print out data from :attr:`args`.

    :param args: some object with attributes
    :param variant:
        if 'table' - print arguments as table
        otherwise print arguments in one line
    :param print_fn:
    :param shorten: shorten long text (eg long default value)
    :param fill: max width of text, wraps long paragraph
    :param kwargs: additional kwargs for tabulate + some custom fields:
        cols: number of columns. Can be 'auto' - len(args)/N, int - just number of
        columns, 'sub' / 'sub-auto' / 'sub-INT' - split by sub-commands,
        gap: string, space between tables/columns
    """
    if variant == 'table':
        s = make_table(args, shorten=shorten, fill=fill, **kwargs)
    elif variant == 'tree':
        s = make_tree(args, shorten=shorten, fill=fill)
    else:
        s = stringify(args, shorten=shorten)
    print_fn = print_fn or print
    print_fn(s)
