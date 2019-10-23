Examples
=============

Sub-commands
************

.. code-block:: python

  from argser import parse_args, sub_command

  class Args:
      a: bool
      b = []
      c = 5

      class Sub1:
          d = 1
          e = '2'
          class Sub11:
              a = 5
          sub11 = sub_command(Sub11)
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

  args = parse_args(Args, '-a -c 10 sub1 -d 5 sub11 -a 6')
  assert args.sub1.d == 5
  assert args.sub1.sub11.a == 6
  assert args.sub2 is None

  args = parse_args(Args, '-a -c 10 sub2 -g "foo bar"')
  assert args.sub1 is None
  assert args.sub2.g == "foo bar"


Arguments
*********

str / int / float

.. code-block:: python

    class Args:
        a: str  # default is None
        b = 2  # default is 2
        c: float = Arg(default=3.0, help="a3")  # default is 3.0, with additional help text

    args = parse_args(Args, '-a "foo bar" -b 5 -c 4.2')
    assert args.a == 'foo bar'
    assert args.b == 5
    assert args.c == 4.2


booleans

.. code-block:: python

    class Args:
        a: bool  # default is None, to change use flags: -a or --no-a
        b = True  # default is True, to change to False: ./script.py --no-b
        c = False  # default is False, to change to True: ./script.py -c
        d: bool = Arg(bool_flag=False)  # to change - specify value after flag: `-d 1` or `-d false` or ...

    args = parse_args(Args, '-d 0')
    assert args.a is None
    assert args.b is True
    assert args.c is False
    assert args.d is False

    args = parse_args(Args, '-a --no-b -c -d 1')
    assert args.a is True
    assert args.b is False
    assert args.c is True
    assert args.d is True


lists

.. code-block:: python

    class Args:
        # list
        a = []  # default = [], type = str, nargs = *
        b: List[int] = []  # default = [], type = int, nargs = *
        c = [1.0]  # default = [], type = float, nargs = +
        d: List[int] = Arg(default=[], nargs='+')  # default = [], type = int, nargs = +

    args = parse_args(Args, '-a "foo bar" "baz"')
    assert args.a == ["foo bar", "baz"]
    args = parse_args(Args, '-b 1 2 3')
    assert args.b == [1, 2, 3]
    args = parse_args(Args, '-c 1.1 2.2')
    assert args.c == [1.1, 2.2]
    args = parse_args(Args, '-d')  # error, -d should have more then one element


positional arguments

.. code-block:: python

    class Args:
        a: float = PosArg()
        b: str = PosArg()

    args = parse_args(Args, '5 "foo bar"')
    assert args.a == 5
    assert args.b == 'foo bar'


one dash

.. code-block:: python

    class Args:
        aaa: int = Arg(one_dash=False)
        bbb: int = Arg(one_dash=True)

    args = parse_args(Args, '--aaa 42 -bbb 42')
    assert args.aaa == 42
    assert args.bbb == 42



argparse params

.. code-block:: python

    class Args:
        a = Arg(help="foo bar")  # with additional help message
        b = Arg(action='count')
        c: List[int] = Arg(action='append')

    args = parse_args(Args, '-a foo -bbb -c 1 -c 2')
    assert args.a == 'foo'
    assert args.b == 3
    assert args.c == [1, 2]


Actions
*******

.. code-block:: python

    class Args:
        a = Arg(action='store_const', default='42', const=42)

    args = parse_args(Args, '')
    assert args.a == '42'
    args = parse_args(Args, '-a')
    assert args.a == 42

.. code-block:: python

    class Args:
        a: List[int] = Arg(action='append', default=[])

    args = parse_args(Args, '-a 1')
    assert args.a == [1]

    args = parse_args(Args, '-a 1 -a 2')
    assert args.a == [1, 2]

.. code-block:: python

    class Args:
        verbose: int = Arg(action='count', default=0)

    args = parse_args(Args, '')
    assert args.verbose == 0

    args = parse_args(Args, '-vvv')
    assert args.verbose == 3


Reusability
***********

.. code-block:: python

    class CommonArgs:
        value: int
        verbose = Arg(action='count', default=0)
        model_path = 'foo.pkl'

    class Args1(CommonArgs):
        value: str  # redefine
        epoch = 10

    class Args2(CommonArgs):
        type = 'bert'

    args = parse_args(Args1, '--value "foo bar" --epoch 5')
    args = parse_args(Args2, '--value 10 --type albert')


Auto completion
***************

Check out argcomplete_ for setup guide.

.. _argcomplete: https://argcomplete.readthedocs.io/en/latest

Add autocompletes:

.. code-block:: bash

    # using argcomplete's script
    eval "$(register-python-argcomplete foo.py)"

    # using argser
    eval "$(argser auto)"  # for all scripts with PYTHON_ARGCOMPLETE_OK (in current dir)
    eval "$(argser auto foo.py)"  # specific file
    eval "$(argser auto /path/to/dir)"  # for all scripts (with PYTHON_ARGCOMPLETE_OK) in /path/to/dir
    eval "$(argser auto /path/to/dir foo.py)"  # combine
    eval "$(argser auto --no-mark)"  # add autocomplete to every script
