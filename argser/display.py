import math
import re
from collections import defaultdict
from typing import List

from argser.consts import Args, SUB_COMMAND_MARK


def stringify(args: Args):
    pairs = ', '.join(map(lambda x: f"{x[0]}={x[1]!r}", args.__dict__.items()))
    return f"{args.__class__.__name__}({pairs})"


def _get_table(args: Args):
    data = []
    for key, value in args.__dict__.items():
        if hasattr(value.__class__, SUB_COMMAND_MARK):
            sub_data = _get_table(value)
            data.extend([(f"{key}__{k}", v) for k, v in sub_data])
        else:
            data.append((key, value))
    return data


def _merge_str_cols(columns: List[str], gap='   '):
    parts = [c.splitlines() for c in columns]
    res = []
    for i in range(max(map(len, parts))):
        row = ''
        for j, part in enumerate(parts):
            if i < len(part):
                row += part[i]
            else:
                row += ' ' * len(part[0])
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


def make_table(args: Args, preset=None, cols='sub-auto', gap='   ', **kwargs):
    from tabulate import tabulate
    kwargs.setdefault('headers', ['arg', 'value'])
    data = _get_table(args)

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


def print_args(args: Args, variant=None, print_fn=None, **kwargs):
    if variant == 'table':
        s = make_table(args, **kwargs)
    elif variant:
        s = stringify(args)
    else:
        s = None
    if s:
        print_fn = print_fn or print
        print_fn(s)
