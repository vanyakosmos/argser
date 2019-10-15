# argser

[![PyPI version](https://badge.fury.io/py/argser.svg)](http://badge.fury.io/py/argser)
[![Build Status](https://github.com/vanyakosmos/argser/workflows/build/badge.svg)](https://github.com/vanyakosmos/argser/actions?workflow=build)
[![Coverage](https://codecov.io/gh/vanyakosmos/argser/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/argser)
[![License](https://img.shields.io/github/license/mashape/apistatus.svg)](https://pypi.python.org/pypi/argser/)
[![Downloads](https://pepy.tech/badge/argser)](https://pepy.tech/project/argser)

Arguments parsing without boilerplate.

------

## install

```
pip install argser
pip install argser tabulate  # for fancy table support
```


## simple example

```python
from argser import parse_args

class Args:
    a = 'a'
    foo = 1
    bar: bool


args = parse_args(Args)
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

```
python playground.py -a "aaa bbb" -f 100500 --no-b
>> Args(bar=False, a='aaa bbb', foo=100500)
```

```
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

## sub commands

```python
from argser import parse_args, sub_command

class Args:
    a: bool
    b = []
    c = 5
    
    class Sub1:
        d = 1
        e = '2'
    
    sub1 = sub_command(Sub1)
    
    class Sub2:
        f = 1
        g = '2'
    
    sub2 = sub_command(Sub2)


args = parse_args(Args, '-a -c 10')
assert args.a is True
assert args.c == 10
assert args.sub1 is None
assert args.sub2 is None

args = parse_args(Args, '-a -c 10 sub1 -d 5')
assert args.sub1.d == 5
assert args.sub2 is None

args = parse_args(Args, '-a -c 10 sub2 -g "foo bar"')
assert args.sub1 is None
assert args.sub2.g == "foo bar"
```

```
❯ python playground.py -h
usage: playground.py [-h] [-a] [--no-a] [-b [B [B ...]]] [-c [C]]
                     {sub1,sub2} ...

positional arguments:
  {sub1,sub2}

optional arguments:
  -h, --help      show this help message and exit
  -a              bool, default: None.
  --no-a
  -b [B [B ...]]  List[str], default: [].
  -c [C]          int, default: 5.
```

```
❯ python playground.py sub1 -h
usage: playground.py sub1 [-h] [-d [D]] [-e [E]]

optional arguments:
  -h, --help  show this help message and exit
  -d [D]      int, default: 1.
  -e [E]      str, default: '2'.
```


## more examples

for more usage examples check out [tests.py](tests.py) file


## arguments

```python
from typing import List
from argser import Arg, PosArg

class Args:
    # str / int / float
    a1: str  # default is None
    a2 = 2  # default is 2
    a3: float = Arg(default=3.0, help="a3")  # default is 3.0, with additional help text

    # bool
    b1: bool  # default is None, to change use flags: --b1 or --no-b1
    b2 = True  # default is True, to change to False: ./script.py --no-b2
    b3 = False  # default is False, to change to True: ./script.py --b3
    b4: bool = Arg(bool_flag=False)  # to change - specify value after flag: `--b4 1` or `--b4 false` or ...
    
    # list
    l1 = []  # default = [], type = str, nargs = *
    l2: List[int] = []  # default = [], type = int, nargs = *
    l3 = [1.0]  # default = [], type = float, nargs = +
    l4: List[int] = Arg(default=[], nargs='+')  # default = [], type = int, nargs = +

    # positional args
    c1: float = PosArg()  # ./script.py 12.34

    # one dash
    d1: int = Arg(one_dash=True)  # ./script.py -d1 1
    
    # help
    h1 = Arg()  # only default help message: "str, default: None."
    h2 = Arg(help="foo bar")  # default + custom: "str, default: None. foo bar"
    h3 = Arg(help="foo bar", keep_default_help=False)  # just custom: "foo bar"
```

## parse

Use `parse_args` to parse arguments from string or command line.

Params:
 - `args_cls`: class with defined arguments
 - `args`: arguments to parse. Either string or list of strings or None (to read from sys.args)
 
Display params:
 - `show`:
    - if True - print arguments in one line
    - if 'table' - print arguments as table
 - `print_fn`:
 - `tabulate_kwargs`: additional kwargs for `tabulate` + some custom fields:
    - cols: number of columns: 
        - 'auto' - len(args)/N
        - int - just number of columns
        - 'sub' / 'sub-auto' (default) / 'sub-INT' - split by sub-commands
    - gap: string, space between tables/columns

Extra params for all arguments:
 - `make_shortcuts`: make short version of arguments: `--abc -> -a`, `--abc_def -> --ad`
 - `bool_flag`:
    - if True then read bool from argument flag: `--arg` is True, `--no-arg` is False,
    - otherwise check if arg value and truthy or falsy: `--arg 1` is True `--arg no` is False
 - `one_dash`: use one dash for long names: `-name` instead of `--name`
 - `keep_default_help`: prepend autogenerated help message to your help message
 - `help_format`: default help format
 - `override`: override values above on arguments defined as instance of `Arg` class


## notes

1. explicitly specify type for arguments defined with `Arg` class to help your IDE

```python
class Args:
    a: int = Arg(default=3)
```

`argser` will know about type of `a` without annotation (it can be determined by default value or type hint), 
but if you want your IDE to know that `args.a` is `int` and not `Arg` then you need explicit annotation.
