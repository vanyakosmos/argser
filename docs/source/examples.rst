Examples
=============

Sub-commands
************

.. doctest::

    >>> from argser import parse_args, sub_command

    >>> class Args:
    ...     a: bool
    ...     b = []
    ...     c = 5
    ...     class Sub1:
    ...         d = 1
    ...         e = '2'
    ...         class Sub11:
    ...             a = 5
    ...         sub11 = sub_command(Sub11)
    ...     sub1 = sub_command(Sub1)
    ...     class Sub2:
    ...         f = 1
    ...         g = '2'
    ...     sub2 = sub_command(Sub2)

    >>> args = parse_args(Args, '-a -c 10')
    >>> assert args.a is True
    >>> assert args.c == 10
    >>> assert args.sub1 is None
    >>> assert args.sub2 is None

    >>> args = parse_args(Args, '-a -c 10 sub1 -d 5 sub11 -a 6')
    >>> assert args.sub1.d == 5
    >>> assert args.sub1.sub11.a == 6
    >>> assert args.sub2 is None

    >>> args = parse_args(Args, '-a -c 10 sub2 -g "foo bar"')
    >>> assert args.sub1 is None
    >>> assert args.sub2.g == "foo bar"


Arguments
*********

str / int / float
-----------------

.. doctest::

    >>> from argser import Opt

    >>> class Args:
    ...     a: str  # default is None
    ...     b = 2  # default is 2
    ...     c: float = Opt(default=3.0, help="a3")  # default is 3.0, with additional help text

    >>> args = parse_args(Args, '-a "foo bar" -b 5 -c 4.2')
    >>> assert args.a == 'foo bar'
    >>> assert args.b == 5
    >>> assert args.c == 4.2


booleans
--------

.. doctest::

    >>> class Args:
    ...     a: bool  # default is None, to change use flags: -a or --no-a
    ...     b = True  # default is True, to change to False: ./script.py --no-b
    ...     c = False  # default is False, to change to True: ./script.py -c
    ...     d: bool = Opt(bool_flag=False)  # to change - specify value after flag: `-d 1` or `-d false` or ...

    >>> args = parse_args(Args, '-d 0')
    >>> assert args.a is None
    >>> assert args.b is True
    >>> assert args.c is False
    >>> assert args.d is False

    >>> args = parse_args(Args, '-a --no-b -c -d 1')
    >>> assert args.a is True
    >>> assert args.b is False
    >>> assert args.c is True
    >>> assert args.d is True


lists
-----

.. doctest::

    >>> from typing import List

    >>> class Args:
    ...     a = []  # default = [], type = str, nargs = *
    ...     b: List[int] = []  # default = [], type = int, nargs = *
    ...     c = [1.0]  # default = [], type = float, nargs = +
    ...     d: List[int] = Opt(default=[], nargs='+')  # default = [], type = int, nargs = +

    >>> args = parse_args(Args, '-a "foo bar" "baz"')
    >>> assert args.a == ["foo bar", "baz"]
    >>> args = parse_args(Args, '-b 1 2 3')
    >>> assert args.b == [1, 2, 3]
    >>> args = parse_args(Args, '-c 1.1 2.2')
    >>> assert args.c == [1.1, 2.2]
    >>> try:
    ...     args = parse_args(Args, '-d')  # error, -d should have more then one element
    ...     assert 0
    ... except SystemExit:
    ...     assert 1


positional arguments
--------------------

.. doctest::

    >>> from argser import Arg

    >>> class Args:
    ...     a: float = Arg()
    ...     b: str = Arg()

    >>> args = parse_args(Args, '5 "foo bar"')
    >>> assert args.a == 5
    >>> assert args.b == 'foo bar'


different prefixes
------------------

.. doctest::

    >>> from argser import Opt

    >>> class Args:
    ...     aaa: int = Opt(prefix='-')
    ...     bbb: int = Opt(prefix='++')

    >>> args = parse_args(Args, '-aaa 42 ++bbb 42')
    >>> assert args.aaa == 42
    >>> assert args.bbb == 42


argparse params
---------------

.. doctest::

    >>> from typing import List
    >>> from argser import Opt

    >>> class Args:
    ...     a = Opt(help="foo bar")  # with additional help message
    ...     b = Opt(action='count')
    ...     c: List[int] = Opt(action='append')

    >>> args = parse_args(Args, '-a foo -bbb -c 1 -c 2')
    >>> assert args.a == 'foo'
    >>> assert args.b == 3
    >>> assert args.c == [1, 2]


Actions
*******

.. doctest::

    >>> from argser import Opt

    >>> class Args:
    ...     a = Opt(action='store_const', default='42', const=42)

    >>> args = parse_args(Args, '')
    >>> assert args.a == '42'
    >>> args = parse_args(Args, '-a')
    >>> assert args.a == 42

.. doctest::

    >>> from typing import List
    >>> from argser import Opt

    >>> class Args:
    ...     a: List[int] = Opt(action='append', default=[])

    >>> args = parse_args(Args, '-a 1')
    >>> assert args.a == [1]

    >>> args = parse_args(Args, '-a 1 -a 2')
    >>> assert args.a == [1, 2]

.. doctest::

    >>> from argser import Opt
    >>> class Args:
    ...     verbose: int = Opt(action='count', default=0)

    >>> args = parse_args(Args, '')
    >>> assert args.verbose == 0

    >>> args = parse_args(Args, '-vvv')
    >>> assert args.verbose == 3


Reusability
***********

.. doctest::

    >>> class CommonArgs:
    ...     value: int
    ...     verbose = Opt(action='count', default=0)
    ...     model_path = 'foo.pkl'

    >>> class Args1(CommonArgs):
    ...     value: str  # redefine
    ...     epoch = 10

    >>> class Args2(CommonArgs):
    ...     type = 'bert'

    >>> args = parse_args(Args1, '--value "foo bar" --epoch 5')
    >>> assert args.epoch == 5
    >>> args = parse_args(Args2, '--value 10 --type albert')
    >>> assert args.type == 'albert'


Call function with parsed arguments
***********************************

.. doctest::

    >>> import argser

    >>> def main(a, b: int, c=1.2, d: List[bool]=None):
    ...     return [a, b, c, d]

    >>> assert argser.call(main, '1 2 -c 3.3 -d 1 0 1 1') == [
    ...     '1',
    ...     2,
    ...     3.3,
    ...     [True, False, True, True],
    ... ]

Or as decorator:
----------------

.. doctest::

    >>> import argser

    >>> @argser.call('1 2')
    ... def foo(a, b: int):
    ...     assert a == '1' and b == 2

In examples above ``a`` (implicit string) and ``b`` (int) are positional argument because they don't have default values.


Multiple sub-commands:
----------------------

.. doctest::

    >>> from argser import SubCommands
    >>> subs = SubCommands()

    >>> @subs.add(description="foo bar")
    ... def foo(): return 'foo'

    >>> @subs.add
    ... def bar(a, b: int): return [a, b]

    >>> subs.parse('foo')
    'foo'
    >>> subs.parse('bar 1 2')
    ['1', 2]


Override options globally
*************************

.. doctest::

    >>> import argser
    >>> class Args:
    ...     a = 1
    ...     b = True
    ...     ccc_ddd = 'foo'

    >>> args = argser.parse_args(
    ...     Args,
    ...     '+a 42 +b false +ccc+ddd "foo bar"',  # read from command if None
    ...     make_shortcuts=False,  # +ccc+ddd will not generate cd now
    ...     bool_flag=False,  # bool arg will require bool value near flag
    ...     prefix='+',  # change default prefix
    ...     repl=('_', '+'),  # change auto-replacer options (from, to)
    ...     override=True,  # only required if you need to override args defined with Opt/Arg
    ... )

    >>> assert args.a == 42
    >>> assert args.b is False
    >>> assert args.ccc_ddd == 'foo bar'


Display arguments
*****************

.. doctest::

    >>> from argser import sub_command, parse_args
    >>> class Args:
    ...     a = 1
    ...     b = 'foo'
    ...     class Sub:
    ...         a = 'foo bar'
    ...     sub = sub_command(Sub)
    >>> args = parse_args(
    ...     Args,
    ...     '-a 42 sub -a "fooooooooo baaaaaaaaaaaaaaar baaaaaaaaaaaaaaar"',
    ...     show='table',
    ... )
    arg    value     arg     value
    -----  -------   ------  -----------------------------
    a      42        sub__a  'fooooooooo baaaaaaaaaaaaaaar
    b      'foo'             baaaaaaaaaaaaaaar'


Or as tree:

.. doctest::

    >>> args = parse_args(
    ...     Args,
    ...     '-a 42 sub -a "fooooooooo baaaaaaaaaaaaaaar baaaaaaaaaaaaaaaz"',
    ...     show='tree',
    ... )
    Args
    ├ a = 42
    ├ b = 'foo'
    └ sub = Sub
      ├ a = 'fooooooooo baaaaaaaaaaaaaaar
      └     baaaaaaaaaaaaaaaz'

Or in one line:

.. doctest::

    >>> args = parse_args(
    ...     Args,
    ...     '-a 42 sub -a "fooooooooo baaaaaaaaaaaaaaar baaaaaaaaaaaaaaar"',
    ...     show=True,
    ... )
    Args(a=42, b='foo', sub=Sub(a='fooooooooo baaaaaaaaaaaaaaar baaaaaaaaaaaaaaar'))

Or after parsing:

.. doctest::

    >>> from argser import print_args
    >>> print_args(args, 'table')
    arg    value     arg     value
    -----  -------   ------  -----------------------------
    a      42        sub__a  'fooooooooo baaaaaaaaaaaaaaar
    b      'foo'             baaaaaaaaaaaaaaar'


Using existing parser
*********************

.. doctest::

    >>> from argparse import ArgumentParser, Namespace
    >>> parser = ArgumentParser(prog='prog')
    >>> action = parser.add_argument('--foo', default=42, type=int)

    >>> class Args:
    ...     __namespace__: Namespace  # just for hints in IDE
    ...     a = 1
    ...     b = True

    >>> args = parse_args(Args, '--foo 100 -a 5 --no-b', parser=parser, parser_prog='WILL NOT BE USED')
    >>> args.a, args.b
    (5, False)
    >>> args.__namespace__.foo
    100


Inspection
**********

After parsing each attribute of parsed class will be replaced with populated instance of :class:`argser.fields.Opt`.

.. doctest::

    >>> class Args:
    ...     a: bool
    ...     b = 1, "help for a"

    >>> args = parse_args(Args, '--no-a -b 2')

    >>> assert isinstance(Args.a, Opt)
    >>> assert Args.a.type is bool
    >>> assert args.a is False

    >>> assert isinstance(Args.b, Opt)
    >>> assert Args.b.type is int
    >>> assert Args.b.help == "help for a"
    >>> assert args.b == 2


Arguments factory
*****************

From callable:

.. doctest::

  >>> def read_a(value: str):
  ...     return int(value) + 1

  >>> class Args:
  ...     a = Opt(default=1, factory=read_a)

  >>> parse_args(Args, '-a 2').a
  3


From method:

.. doctest::

  >>> class Args:
  ...     a = 1
  ...     def read_a(self, value: str):
  ...         return int(value) + 1

  >>> parse_args(Args, '-a 2').a
  3

From method with different name:

  >>> class Args:
  ...     a = Opt(default=1, factory='get_a')
  ...     def get_a(self, value: str):
  ...         return int(value) + 1

  >>> parse_args(Args, '-a 2').a
  3


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
