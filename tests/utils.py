from collections import namedtuple


Params = namedtuple('Params', "args,kwargs")


def params(*args, **kwargs) -> Params:
    return Params(args, kwargs)
