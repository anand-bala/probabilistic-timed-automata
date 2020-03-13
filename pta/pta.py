"""Probabilistic Timed Automaton"""

from typing import Set, Hashable, Callable, Tuple

import attr

from .clocks import Clock, ClockConstraint
from .distributions import DiscreteDistribution


Location = Hashable
Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]

EdgeFn = Callable[[Location], Set[Transition]]
InvariantFn = Callable[[Location], ClockConstraint]


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
class PTA:
    _locations: Set[Location] = attr.ib()
    _clocks: Set[Clock] = attr.ib()

    _init_location: Location = attr.ib()

    _transitions: EdgeFn = attr.ib()
    _invariants: InvariantFn = attr.ib()
