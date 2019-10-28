from typing import List

import argser
from argser.parse_func import SubCommands


def test_simple_case():
    def foo(a, b: int, c=1.2):
        return [a, b, c]

    assert argser.call(foo, '1 2') == ['1', 2, 1.2]
    assert argser.call(foo, '2 3 -c 4.4') == ['2', 3, 4.4]

    def foo(a, b: List[int]):
        return [a, b]

    assert argser.call(foo, '1 2 3') == ['1', [2, 3]]


def test_decorator():
    @argser.call('')
    def foo(a=1, b='2'):
        assert a == 1
        assert b == '2'

    @argser.call('-a 5 -b "foo bar"')
    def foo(a=1, b='2'):
        assert a == 5
        assert b == 'foo bar'


def test_group():
    subs = SubCommands()

    @subs.add(description="foo bar")
    def foo():
        return 'foo'

    @subs.add
    def bar(a, b: int):
        return [a, b]

    assert subs.parse('foo') == 'foo'
    assert subs.parse('bar 1 2') == ['1', 2]
