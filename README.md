# argser

[![PyPI version](https://badge.fury.io/py/argser.svg)](http://badge.fury.io/py/argser)
[![Build Status](https://github.com/vanyakosmos/argser/workflows/test-publish/badge.svg)](https://github.com/vanyakosmos/argser/actions?workflow=test-publish)
[![Coverage](https://codecov.io/gh/vanyakosmos/argser/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/argser)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/argser/)
[![Downloads](https://pepy.tech/badge/argser)](https://pepy.tech/project/argser)

[GitHub](https://github.com/vanyakosmos/argser) | 
[PyPI](https://pypi.org/project/argser/) | 
[Docs](https://argser.readthedocs.io/en/latest) | 
[Examples](https://argser.readthedocs.io/en/latest/examples.html) | 
[Changelog](CHANGELOG.md)

Arguments parsing without boilerplate.

## Features:
- arguments and type hints in IDE
- easy nested sub-commands
- sane defaults for arguments' params (ie if default of arg is 3 then type should be int, or when annotation/type/default is `bool` then generate 2 arguments: for true value `--arg` and for false `--no-arg`, ...)
- 𝕡𝕣𝕖𝕥𝕥𝕪 𝕡𝕣𝕚𝕟𝕥𝕚𝕟𝕘
- support for argparse actions
- common options/arguments reusability
- auto shortcuts generation: `--verbose -> -v, --foo_bar -> --fb`
- [auto completion](https://argser.readthedocs.io/en/latest/examples.html#auto-completion) in shell (tnx to [argcomplete](https://argcomplete.readthedocs.io/en/latest/))


## Installation

```text
pip install argser
pip install argser[tabulate]  # for fancy tables support
pip install argser[argcomplete]  # for shell auto completion
pip install argser[all]
```


## Simple example

```python
from argser import parse_args

class Args:
    a = 'a'
    foo = 1
    bar: bool


args = parse_args(Args, show=True)
```

<details>
<summary>argparse alternative</summary>
    
```python
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('-a', type=str, default='a', help="str, default: 'a'")
parser.add_argument('--foo', '-f', dest='foo', type=int, default=1, help="int, default: 1")
parser.add_argument('--bar', '-b', dest='bar', action='store_true', help="bool, default: None")
parser.add_argument('--no-bar', '--no-b', dest='bar', action='store_false')
parser.set_defaults(bar=None)

args = parser.parse_args()
print(args)
```
</details>

```text
❯ python playground.py -a "aaa bbb" -f 100500 --no-b
>> Args(bar=False, a='aaa bbb', foo=100500)
```

```text
❯ python playground.py -h
usage: playground.py [-h] [--bar] [--no-bar] [-a [A]] [--foo [FOO]]

optional arguments:
  -h, --help            show this help message and exit
  --bar, -b             bool, default: None.
  --no-bar, --no-b
  -a [A]                str, default: 'a'.
  --foo [FOO], -f [FOO]
                        int, default: 1.
```


## Sub-commands

```python
from argser import parse_args, sub_command
    
class SubArgs:
    d = 1
    e = '2'

class Args:
    a: bool
    b = []
    c = 5
    sub = sub_command(SubArgs, help='help message for sub-command')

args = parse_args(Args, '-a -c 10', parser_help='help message for root parser')
assert args.a is True
assert args.c == 10
assert args.sub is None

args = parse_args(Args, '--no-a -c 10 sub -d 5 -e "foo bar"')
assert args.a is False
assert args.sub.d == 5
assert args.sub.e == 'foo bar'
```

```text
❯ python playground.py -h
usage: playground.py [-h] [-a] [--no-a] [-b [B [B ...]]] [-c C] {sub} ...

positional arguments:
    {sub}

optional arguments:
    -h, --help      show this help message and exit
    -a              bool, default: None
    --no-a
    -b [B [B ...]]  List[str], default: []
    -c C            int, default: 5
```

```text
❯ python playground.py sub1 -h
usage: playground.py sub [-h] [-d D] [-e E]

help message for sub-command

optional arguments:
    -h, --help  show this help message and exit
    -d D        int, default: 1
    -e E        str, default: '2'
```

Can be deep nested:
```python
from argser import parse_args, sub_command

class Args:
    a = 1
    class Sub1:
        b = 1
        class Sub2:
            c = 1
            class Sub3:
                d = 1
            sub3 = sub_command(Sub3)
        sub2 = sub_command(Sub2)
    sub1 = sub_command(Sub1)

args = parse_args(Args, '-a 1 sub1 -b 2 sub2 -c 3 sub3 -d 4')
```
