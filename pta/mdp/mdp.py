"""General MDP simulator for PTAs.

This simulator does not attempt to efficiently compute regions or any of that.
Rather, it is a naive implementation of an on-the-fly MDP translation of a PTA
for blackbox simulation.

This is useful in the context of reinforcement learning when you have a
controller (typically a neural network) that takes in a state (location,
valuation pair) and outputs a delay or an edge
"""

import attr
from attr.validators import instance_of

from pta.clock import Clock, ClockValuation
from pta.distributions import DiscreteDistribution
from pta import pta

from typing import (
    FrozenSet,
    Hashable,
    Mapping,
    Tuple,
)

# Location in the PTA
Location = Hashable

# An is a transition that can be taken in the PTA
Edge = Hashable

State = Tuple[float, Location]  # State is Valuation x Location
Action = Tuple[float, Edge]     # Action is Delay x Edge

# TransitionFn :: State x Action -> Dist(State)


@attr.s(auto_attribs=True)
class MDP:

    _pta: pta.PTA = attr.ib(validator=[instance_of(pta.PTA)])

    _current_clock_valuation: ClockValuation = attr.ib(converter=ClockValuation)

    @property
    def locations(self) -> FrozenSet[Location]:
        return self._pta.locations

    @property
    def clocks(self) -> FrozenSet[Clock]:
        return self._pta.clocks

    @property
    def edges(self) -> FrozenSet[Edge]:
        return self._pta.actions

    @property
    def initial_location(self) -> Location:
        return self._pta.initial_location

    def __attrs_post_init__(self):
        # We have our PTA. Now I need to populate what?
        # 1. A generator for 
