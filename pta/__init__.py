"""Probabilistic Timed Automata"""

from typing import Iterable, Hashable, Tuple

from pta.clock import Clock, ClockConstraint
from pta.region import Region
from pta.pta import PTA, RegionMDP

__version__ = "0.1.0"


def new_clocks(clock_vars: Iterable[Hashable]) -> Tuple[Clock, ...]:
    """Create multiple `Clock` variables in one go

    Example
    -------

    >>> clocks(('x','y','z'))
    {Clock(name='x'), Clock(name='y'), Clock(name='z')}

    Parameters
    ----------
    clock_vars: Iterable[Hashable]
        List of clock "names"
    Returns
    -------
    :
        Set of clocks
    """
    return tuple(map(lambda x: Clock(x), clock_vars))
