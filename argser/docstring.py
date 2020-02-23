import re
import textwrap
from typing import Optional


param_re = re.compile(r'^:param ([\w_]+): (.+)$')


def _normalize_docstring(doc: str):
    # dedent first line and the rest of the docstring separately because
    # docstring can start right after """
    lines = doc.splitlines()
    head = textwrap.dedent(lines[0])
    tail = textwrap.dedent('\n'.join(lines[1:]))
    res = f"{head}\n{tail}".strip()
    return res


def _leading_ws(t: str):
    """count leading whitespaces"""
    return len(t) - len(t.lstrip())


def parse_sphinx_docstring(doc: str):
    description = []
    params = {}
    end_of_desc = False
    prev_param = None
    prev_line = None
    for line in doc.splitlines():
        m = param_re.match(line)
        if m:
            prev_line = line
            prev_param = m[1]
            params[prev_param] = m[2]
            end_of_desc = True
        elif end_of_desc:
            if textwrap.dedent(line) == '':
                prev_line = None
                prev_param = None
            elif prev_param and _leading_ws(line) > _leading_ws(prev_line):
                params[prev_param] += ' ' + textwrap.dedent(line)
            # else: line unrelated to params documentation or main description
        else:
            description.append(line)
    desc = '\n'.join(description).strip()
    return {
        'description': desc or None,
        'params': params,
    }


def parse_docstring(doc: Optional[str]):
    """
    :param doc:
    :return:
    """
    if doc is None:
        return {'description': None, 'params': {}}
    doc = _normalize_docstring(doc)
    return parse_sphinx_docstring(doc)
