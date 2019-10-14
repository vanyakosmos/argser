# argser

[![Build Status](https://github.com/vanyakosmos/argser/workflows/build/badge.svg)](https://github.com/vanyakosmos/argser/actions?workflow=build)
[![Coverage](https://codecov.io/gh/vanyakosmos/argser/branch/master/graph/badge.svg)](https://codecov.io/gh/vanyakosmos/argser)

argparse without boilerplate


## simple example

```python
from argser import ArgsParser

class Args(ArgsParser):
    a = 'a'
    foo = 1
    bar: bool


args = Args().parse().print()
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

## complex example
```python
from argser import ArgsParser, Command, Argument, PosArgument

class Args(ArgsParser):
    a: bool  # default None, will generate 2 args - --a and --no-a
    b = []  # nargs==*, List[str]
    c = 5
    d = Argument(default=3, aliases=('dd', 'ddd'), help="foo", keep_default_help=False)  # for complex arguments
    # arguments after `Commands` will belong to separate subparser named after command
    another = Command()
    e = ['str']  # nargs==+
    f: int = None
    g: str = PosArgument()  # positional argument

    class SubCommand(ArgsParser):
        k = 1
        l = 2

    another2 = SubCommand()


args = Args().parse().print()
```

```
❯ python playground.py -h

usage: playground.py [-h] [-a] [--no-a] [-b [B [B ...]]] [-c [C]] [-d D]
                     {another2,another} ...

positional arguments:
  {another2,another}
    another

optional arguments:
  -h, --help            show this help message and exit
  -a                    bool, default: None.
  --no-a
  -b [B [B ...]]        List[str], default: [].
  -c [C]                int, default: 5.
  -d D, --dd D, --ddd D
                        foo
```

```
❯ python playground.py another -h

usage: playground.py another [-h] [-e [E]] [-f [F]] g

positional arguments:
  g             str, default: None.

optional arguments:
  -h, --help    show this help message and exit
  -e E [E ...]  List[str], default: ['str'].
  -f [F]        int, default: None.
```

```
❯ python playground.py another2 -h

usage: playground.py another2 [-h] [-k [K]] [-l [L]]

optional arguments:
  -h, --help  show this help message and exit
  -k [K]      int, default: 1.
  -l [L]      int, default: 2.
```


## more

for more usage examples check out [tests.py](tests.py) file


## notes

1. annotations are not static fields
```python
class Args(ArgsParse):
    com = Command()
    a: str

assert hasattr(Args, 'a') is False
```
Annotation "fields" don't appear in `cls.__dict__` at all.
That's why we can't track their order in class definition which means that we can't use them with `Command`. 
You need to explicitly specify default value to convert simple annotation into field with annotation.

If you don't have sub-commands and don't have default values for arguments then it's okay to use them.

```python
class Args(ArgsParse):
    com = Command()
    a: str = None  # now `a` is part of `com` subparser
```

2. explicitly specify type for arguments defined with `Argument` class to help your IDE

```python
class Args(ArgsParse):
    a: int = Argument(default=3)
```

`argser` will know about type of `a` without annotation (it can be determined by default value), 
but if you want your IDE to know that `args.a` is `int` and not `Argument` then you need explicit annotation.
