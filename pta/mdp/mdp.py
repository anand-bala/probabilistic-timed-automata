"""General MDP simulator for PTAs.

This simulator does not attempt to efficiently compute regions or any of that.
Rather, it is a naive implementation of an on-the-fly MDP translation of a PTA
for blackbox simulation.

This is useful in the context of reinforcement learning when you have a
controller (typically a neural network) that takes in a state (location,
valuation pair) and outputs a delay or an edge
"""

import attr

from pta.clock import Clock, ClockConstraint
from pta.distributions import DiscreteDistribution

from typing import (
    Set,
    FrozenSet,
    Hashable,
    Mapping,
    Tuple,
    Optional,
)

# Location in the PTA
Location = Hashable

# An is a transition that can be taken in the PTA
Edge = Hashable

Action = Tuple

# TransitionFn :: Location -> 
TransitionFn = Mapping[Location, DiscreteDistribution]


@attr.s(auto_attribs=True, init=False)
class MDP:

    _initial_location: Location = attr.ib()
    _locations: FrozenSet[Location] = attr.ib()
    _clocks: FrozenSet[Clock] = attr.ib()

    _discrete_actions: FrozenSet[Edge] = attr.ib()

    _probability_transition_fn: TransitionFn = attr.ib()
