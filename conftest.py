from typing import List

import pytest

from argser import parse_args


@pytest.fixture(autouse=True)
def no_color(mocker):
    mocker.patch.dict('os.environ', {'ANSI_COLORS_DISABLED': '1'})


@pytest.fixture()
def list_args():
    class Args:
        a: list
        b: List
        c: List[int]
        d: List[bool] = []
        e = [1.1, 2.2]

    def parse(args=''):
        return parse_args(Args, args)

    return parse
