import argparse
import glob
import os
import sys
from typing import List

import argser

argcomplete_desc = "Add auto completion for scripts. Ex: eval \"$(python -m argser auto foo.py)\""


class AutoArgs:
    executables: List[str] = argser.PosArg()
    use_defaults = True
    complete_arguments = argser.Arg(nargs=argparse.REMAINDER)
    shell: str = argser.Arg(choices=('bash', 'tcsh', 'fish'), default='bash')


def autocomplete(args: AutoArgs):
    import argcomplete

    exs = []
    for i, ex in enumerate(args.executables):
        if os.path.isdir(ex):
            exs.extend(glob.glob(os.path.join(ex, '*.py')))
        else:
            exs.append(ex)
    # noinspection PyTypeChecker
    sys.stdout.write(argcomplete.shellcode(exs, args.use_defaults, args.shell, args.complete_arguments))


class Args:
    auto = argser.sub_command(AutoArgs, help=argcomplete_desc, description=argcomplete_desc)


def main():
    args = argser.parse_args(Args, parser_prog='argser')
    if args.auto:
        autocomplete(args.auto)


if __name__ == '__main__':
    main()
