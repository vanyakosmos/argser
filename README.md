# args_parse

```python
from args_parse import ArgsParser, Command, Argument, PosArgument

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
❯ python args_parse.py -h

usage: args_parse.py [-h] [-a] [--no-a] [-b [B]] [-c [C]] [-d D] {another} ...

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
❯ python args_parse.py another -h

usage: args_parse.py another [-h] [-e [E]] [-f [F]] g

positional arguments:
  g               str, default: None.

optional arguments:
  -h, --help      show this help message and exit
  -e [E], -e [E]  list, default: ['str'].
  -f [F], -f [F]  int, default: None.
```
