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

.. code-block:: python

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


Auto completion
**************

Check out argcomplete_.

.. _argcomplete: https://argcomplete.readthedocs.io/en/latest

.. code-block::

    eval "$(register-python-argcomplete foo.py)"
    eval "$(argser auto foo.py)"  # specific file
    eval "$(argser auto /path/to/dir)"  # all .py files in dir
    eval "$(argser auto /path/to/dir foo.py)"  # combine
