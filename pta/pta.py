"""Probabilistic Timed Automaton"""

from typing import (Callable, FrozenSet, Hashable, Mapping, NamedTuple, Set,
                    Text, Tuple)

import attr

from pta.clock import Clock, ClockConstraint, ClockValuation, Interval, delays
from pta.distributions import DiscreteDistribution

Action = Hashable
Label = Text
Location = Hashable


class Target(NamedTuple):
    reset: Set[Clock]
    location: Location


class Transition(NamedTuple):
    guard: ClockConstraint
    target_dist: DiscreteDistribution[Target]


TransitionFn = Callable[[Location], Mapping[Action, Transition]]


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
class PTA:

    # NOTE: We never explicitly need to know the locations...
    _n_locations: int = attr.ib()
    _clocks: FrozenSet[Clock] = attr.ib(converter=frozenset)
    _actions: FrozenSet[Action] = attr.ib(converter=frozenset)

    _init_location: Location = attr.ib()

    _transitions: TransitionFn = attr.ib()
    _invariants: Callable[[Location], ClockConstraint] = attr.ib()

    @property
    def n_locations(self) -> int:
        return self._n_locations

    @property
    def clocks(self) -> FrozenSet[Clock]:
        """Get the set of clocks in the PTA"""
        return self._clocks

    @property
    def actions(self) -> FrozenSet[Action]:
        """Get the set of actions in the PTA"""
        return self._actions

    @property
    def initial_location(self) -> Location:
        """Get the initial location of the PTA"""
        return self._init_location

    def transitions(self, loc) -> Mapping[Action, Transition]:
        return self._transitions(loc)

    def invariants(self, loc) -> ClockConstraint:
        return self._invariants(loc)

    def enabled_actions(
        self, loc: Location, values: ClockValuation
    ) -> Mapping[Action, DiscreteDistribution[Target]]:
        """Return the set of enabled edges available at a location with given clock valuation.

        The edges are enabled with respect to their guards and the given valuation.

        Parameters
        ----------
        loc:
            Location in the PTA (raises error if ``loc`` not in PTA.
        values:
            Valuations for clocks in PTA (raises error if ``values`` does not
            contain keys for all clocks in the PTA.

        Returns
        -------
        :
            Set of distributions corresponding to edges enabled in the location.
        """
        assert (
            self._clocks <= values.keys()
        ), "Valuations do not contain keys for all clocks in PTA"

        return {
            label: dist
            for label, (guard, dist) in self._transitions(loc).items()
            if values in guard
        }

    def allowed_delays(self, loc: Location, values: ClockValuation) -> Interval:
        """Return the allowed interval of delays at the given location and clock valuation.

        .. seealso::
            :py:func:`~pta.clocks.delays`
        """
        return delays(values, self._invariants(loc))
