"""General MDP simulator for PTAs.

This simulator does not attempt to efficiently compute regions or any of that.
Rather, it is a naive implementation of an on-the-fly MDP translation of a PTA
for blackbox simulation.

This is useful in the context of reinforcement learning when you have a
controller (typically a neural network) that takes in a state (location,
valuation pair) and outputs a delay or an edge
"""

from typing import Callable, FrozenSet, Hashable, Set, Tuple

import attr
from attr.validators import instance_of

from pta import pta
from pta.clock import Clock, ClockConstraint, ClockValuation, Interval, delays
from pta.distributions import DiscreteDistribution

# Location in the PTA
Location = Hashable

# An is a transition that can be taken in the PTA
Edge = Hashable

State = Tuple[ClockValuation, Location]  # State is Valuation x Location
Action = Tuple[float, Edge]  # Action is Delay x Edge

Target = Tuple[Set[Clock], Location]
EdgeTransition = Tuple[ClockConstraint, DiscreteDistribution[Target]]


@attr.s(auto_attribs=True, slots=True)
class MDP:

    _pta: pta.PTA = attr.ib(validator=[instance_of(pta.PTA)])

    _current_clock_valuation: ClockValuation = attr.ib(init=False)
    _current_location: Location = attr.ib(init=False)

    @staticmethod
    def _default_delay_stochasticity(val: ClockValuation, cc: ClockConstraint) -> float:
        """Uniformly randomly pick a float withing the delay"""
        import portion as P
        import random

        # Get interval of allowable delays
        interval: Interval = delays(val, cc)
        assert (
            interval.atomic
        ), "Interval seems to be a disjunction of other intervals... Bug!"
        assert interval.lower != -P.inf, "Interval lower bound is unbounded... Bug!"
        left_offset = 0.1 if interval.left == P.OPEN else 0
        right_offset = 0.1 if interval.right == P.OPEN else 0
        if interval.upper == P.inf:
            # If upper is unbounded, it doesn't matter what value we pick, so pick the lower bound + some offset if open bound
            return interval.lower + left_offset
        # Otherwise pick uniformly from the range
        return random.uniform(
            interval.lower + left_offset, interval.upper - right_offset
        )

    # Given a ClockConstraint, pick an offset value
    _random_delay: Callable[[ClockValuation, ClockConstraint], float] = attr.ib(
        default=_default_delay_stochasticity, kw_only=True
    )

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

    def enabled_actions(self) -> Tuple[Interval, FrozenSet[Edge]]:
        """Get the interval of delays satisfying the invariant and the set of actions enabled at the current time"""
        return (
            self._pta.allowed_delays(
                self._current_location, self._current_clock_valuation
            ),
            self._pta.enabled_actions(
                self._current_location, self._current_clock_valuation
            ),
        )

    def __attrs_post_init__(self):
        self._current_clock_valuation = ClockValuation.zero_init(self.clocks)
        self._current_location = self.initial_location

    def _get_obs(self) -> State:
        return (self._current_clock_valuation, self._current_location)

    def _get_transition(self, edge: Edge) -> Transition:
        return self._pta._transitions[self._current_location][edge]

    def reset(self) -> State:
        """Reset the MDP to its initial state

        Returns
        -------
        State
            The reset state of the MDP
        """
        self.__attrs_post_init__()
        return self._get_obs()

    def step(self, action: Action, *, edge_first=True) -> State:
        """Take a timed action on the MDP

        Here, the semantics imply that the agent takes an edge, and then waits
        for the given delay. Due to the stochasticity in the environment, there
        is noise in the delay and the edge may be probabilistic.
        If you want the reverse to be true, set `edge_first` to `False`.

        Parameters
        ----------
        action : Action
                 A timed action
        Returns
        -------
        State
            The new state of the MDP
        """
        delay, edge = action
        allowed_delay, allowed_edges = self.enabled_actions()

        if edge_first:
            # TODO: Do I need this check?
            # NOTE: An RL algorithm should be able to generalize right?
            assert (
                edge in allowed_edges
            ), "Given action {} is not enables at state {}".format(
                edge, self._get_obs()
            )
            guard, prob_dist = self._get_transition(
                edge
            )  # Get the transition the agent wants to take
