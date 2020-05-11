"""Bunch of utility functions for the package and it's users"""

from collections import deque
from typing import Iterable, Iterator, Tuple, Union


def flatten(t) -> Iterator:
    if not isinstance(t, Iterable):
        yield t
    else:
        for ti in t:
            if isinstance(ti, Iterable):
                yield from flatten(ti)
            else:
                yield ti
