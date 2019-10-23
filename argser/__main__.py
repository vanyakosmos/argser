import argparse
import glob
import os
import re
import sys
from pathlib import Path
from typing import List

import argser

argcomplete_desc = "Add auto completion for scripts. Ex: eval \"$(python -m argser auto foo.py)\""


class AutoArgs:
    executables: List[str] = argser.Arg(
        default=[],
        help=(
            "List of python scripts to add autocompletes to. If none is specified then argser "
            "will search for scripts with PYTHON_ARGCOMPLETE_OK mark."
        )
    )
    use_defaults = True
    complete_arguments = argser.Opt(nargs=argparse.REMAINDER)
    shell: str = argser.Opt(choices=('bash', 'tcsh', 'fish'), default='bash')
    mark: bool = argser.Opt(default=True, help="Add only scripts with PYTHON_ARGCOMPLETE_OK mark.")


def _find_scripts(path: str, mark=True):
    for fp in glob.glob(path, recursive=True):
        fp = os.path.abspath(fp)
        if mark:
            with open(fp) as f:
                if 'PYTHON_ARGCOMPLETE_OK' in f.read(1024):
                    yield fp
        else:
            yield fp


def find_scripts(mark=True):
    res = list(_find_scripts(os.path.join('.', '**', '*.py'), mark))
    if not res:
        raise FileNotFoundError(f"no python files with PYTHON_ARGCOMPLETE_OK marker")
    return res


def extract_scripts(executables: List[str], mark=True):
    res = []
    for i, ex in enumerate(executables):
        executables[i] = os.path.abspath(ex)
        if os.path.isdir(ex):
            res.extend(_find_scripts(os.path.join(ex, '*.py'), mark))
        elif os.path.exists(ex):
            res.append(os.path.abspath(ex))
    if not res:
        files = '\n'.join(map(lambda x: f'- {x}', executables))
        raise FileNotFoundError(f"no python files were found in:\n{files}")
    return res


def autocomplete(args: AutoArgs):
    import argcomplete

    try:
        if args.executables:
            exs = extract_scripts(args.executables, args.mark)
        else:
            exs = find_scripts(args.mark)
    except FileNotFoundError as e:
        sys.stderr.write(f"{e}\n")
        return

    # noinspection PyTypeChecker
    print(argcomplete.shellcode(exs, args.use_defaults, args.shell, args.complete_arguments))

    print("added autocompletion to files (if you ran this with eval):", file=sys.stderr)
    for file in exs:
        print(f"- {file}", file=sys.stderr)


def get_version():
    pyproj = Path(__file__).parent.parent / 'pyproject.toml'
    with open(pyproj, 'r') as f:
        return re.search(r'version\s+=\s+"(.*)"', f.read(128), flags=re.MULTILINE).group(1)


class Args:
    auto = argser.sub_command(AutoArgs, help=argcomplete_desc, description=argcomplete_desc)
    version = argser.Opt(action='version', version=f'%(prog)s {get_version()}')


def main():
    args = argser.parse_args(Args, parser_prog='argser')
    if args.auto:
        autocomplete(args.auto)


if __name__ == '__main__':
    main()
