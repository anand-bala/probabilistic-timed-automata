"""General MDP simulator for PTAs.

This simulator does not attempt to efficiently compute regions or any of that.
Rather, it is a naive implementation of an on-the-fly MDP translation of a PTA
for blackbox simulation.

This is useful in the context of reinforcement learning when you have a
controller (typically a neural network) that takes in a state (location,
valuation pair) and outputs a delay or an edge
"""

import enum
import random
from typing import (Callable, FrozenSet, Hashable, Mapping, NamedTuple, Set,
                    Tuple)

import attr
from attr.validators import instance_of

from pta import pta
from pta.clock import Clock, ClockConstraint, ClockValuation, Interval, delays
from pta.pta import Target
from pta.pta import Transition as EdgeTransition
from pta.spaces import Space

# Location in the PTA
Location = Hashable

# An is a transition that can be taken in the PTA
Edge = Hashable


class State(NamedTuple):
    value: ClockValuation
    location: Location


class Action(NamedTuple):
    delay: float
    edge: Edge


@enum.unique
class _Turn(enum.Enum):
    PLAYER = enum.auto()
    ENV = enum.auto()


@attr.s(auto_attribs=True, slots=True)
class MDP:

    _pta: pta.PTA = attr.ib(validator=[instance_of(pta.PTA)])

    _current_clock_valuation: ClockValuation = attr.ib(init=False)
    _current_location: Location = attr.ib(init=False)
    _progress_steps: int = attr.ib(init=False, default=0)
    _turn: _Turn = attr.ib(init=False, default=_Turn.PLAYER)

    def __attrs_post_init__(self):
        self._current_clock_valuation = ClockValuation.zero_init(self.clocks)
        self._current_location = self.initial_location
        self._progress_steps = 0
        self._turn = _Turn.PLAYER

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
    def location_space(self) -> Space:
        return self._pta.location_space

    @property
    def clocks(self) -> FrozenSet[Clock]:
        return self._pta.clocks

    @property
    def edges(self) -> FrozenSet[Edge]:
        return self._pta.actions

    @property
    def initial_location(self) -> Location:
        return self._pta.initial_location

    @property
    def valuation(self) -> ClockValuation:
        return self._current_clock_valuation

    @property
    def location(self) -> Location:
        return self._current_location

    def _get_obs(self) -> State:
        return State(self._current_clock_valuation, self._current_location)

    def transition(self, edge: Edge) -> EdgeTransition:
        return self._pta._transitions(self._current_location)[edge]

    def enabled_actions(self) -> Tuple[Interval, FrozenSet[Edge]]:
        """Get the interval of delays satisfying the invariant and the set of actions enabled at the current time"""
        return (
            self._pta.allowed_delays(
                self._current_location, self._current_clock_valuation
            ),
            frozenset(
                self._pta.enabled_actions(
                    self._current_location, self._current_clock_valuation
                ).keys()
            ).intersection(self.edges),
        )

    def available_edges(self) -> Mapping[Edge, EdgeTransition]:
        return {
            action: transition
            for action, transition in self._pta.transitions(
                self._current_location
            ).items()
            if action in self.edges
        }

    def reset(self) -> State:
        """Reset the MDP to its initial state

        Returns
        -------
        State
            The reset state of the MDP
        """
        self.__attrs_post_init__()
        return self._get_obs()

    def step(self, action: Action, *, edge_first=False) -> State:
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

        delay, edge = Action._make(action)

        if not edge_first:
            # First let's take the delay.

            # (Assume that a preprocessing step makes sure delay satisfies invariant)
            # And update current clock valuation
            self._current_clock_valuation = self._current_clock_valuation + delay

            _, allowed_edges = self.enabled_actions()

            # If edge is in allowed_edges, we can take the transition
            if edge in allowed_edges:
                transition = self.transition(edge)
                target: Target = Target._make(transition.target_dist.sample()[0])
                self._current_location = target.location
                self._current_clock_valuation.reset(target.reset)

        else:  # if edge taken first, then delay
            # First get the set of allowed edges
            _, allowed_edges = self.enabled_actions()
            # If edge is in allowed_edges, we can take the transition
            if edge in allowed_edges:
                transition = self.transition(edge)
                next_loc = transition.target_dist.sample()
                self._current_location = next_loc
            # Now, we take the delay
            self._current_clock_valuation = self._current_clock_valuation + delay

        # Now the environment can take actions...
        # Get the current allowed delays and actions
        allowed_delay, allowed_edges = self.enabled_actions()
        # Check if there is any edges available that are not part of self.edges
        env_actions = list(allowed_edges - self.edges)
        if len(env_actions) > 0:
            # Take it?
            env_edge: Edge = random.choices(env_actions, k=1)[0]
            env_transition: EdgeTransition = self.transition(env_edge)
            env_delay: float = self._random_delay(
                self._current_clock_valuation, env_transition.guard
            )
            env_reset, env_step = env_transition.target_dist.sample(k=1)[
                0
            ]  # type: Set[Clock], Location
            self._current_clock_valuation = self._current_clock_valuation + env_delay
            self._current_clock_valuation.reset(env_reset)
            self._current_location = env_step

        return self._get_obs()
