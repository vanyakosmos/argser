# arse

argparse without boilerplate


## mini example

```python
from arse import ArgsParser

class Args(ArgsParser):
    a = 'a'
    foo = 1
    bar = True


args = Args().parse()
print(repr(args.a), args.foo, args.bar)
```

```
python playground.py -a "aaa bbb" -f 100500 --no-b
>> 'aaa bbb' 100500 False
```

```
❯ python playground.py -h
usage: playground.py [-h] [-a [A]] [--foo [FOO]] [--no-bar]

optional arguments:
  -h, --help            show this help message and exit
  -a [A]                str, default: 'a'.
  --foo [FOO], -f [FOO]
                        int, default: 1.
  --no-bar, --no-b      bool, default: True.
```

## complex example
```python
from arse import ArgsParser, Command, Argument, PosArgument

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


args = Args().parse().print()
```

```
❯ python playground.py -h

usage: playground.py [-h] [-a] [--no-a] [-b [B]] [-c [C]] [-d D] {another} ...

positional arguments:
  {another}
    another

optional arguments:
  -h, --help            show this help message and exit
  -a, -a                bool, default: None.
  --no-a, --no-a
  -b [B], -b [B]        list, default: [].
  -c [C], -c [C]        int, default: 5.
  -d D, --dd D, --ddd D
                        foo
```

```
❯ python playground.py another -h

usage: playground.py another [-h] [-e [E]] [-f [F]] g

positional arguments:
  g               str, default: None.

optional arguments:
  -h, --help      show this help message and exit
  -e [E], -e [E]  list, default: ['str'].
  -f [F], -f [F]  int, default: None.
```

## more

for more usage examples check out [tests.py](tests.py) file
