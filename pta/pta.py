"""Probabilistic Timed Automaton"""

from typing import Set, Hashable, Mapping, Tuple, Union

import attr

from .clocks import Clock, ClockConstraint, delays, Interval
from .distributions import DiscreteDistribution


Label = Union[str, int]

Location = Hashable
Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
class PTA:
    """
    A PTA is a 6-tuple \\(M = \\left\\langle Q, C, T, q_0, I \\right\\rangle\\) where

    - \\(Q\\) is the set of locations in the PTA;
    - \\(C\\) is the set of clocks in the PTA;
    - \\(T \\) is the transition function that maps a location to a set of possible
      transitions that can be taken (and their associated guards), along with the
      probabilities associated with the set of clocks that are reset and the next
      location;
    - \\(q_0\\) is the initial location in the PTA; and
    - \\(I\\) is the invariant function that maps a location to a clock constraint
      such that as long as the clock constraint is satisfied, the clock can
      progress in the location.
    """

    _locations: Set[Location] = attr.ib(converter=frozenset)
    _clocks: Set[Clock] = attr.ib(converter=frozenset)

    _init_location: Location = attr.ib()

    _transitions: Mapping[Location, Mapping[Label, Transition]] = attr.ib()
    _invariants: Mapping[Location, ClockConstraint] = attr.ib()

    def enabled_actions(
        self, loc: Location, values: Mapping[Clock, float]
    ) -> Mapping[Label, DiscreteDistribution[Target]]:
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
        output:
            Set of distributions corresponding to edges enabled in the location.
        """
        assert loc in self._locations, "Given location is not present in the PTA"
        assert (
            self._clocks <= values.keys()
        ), "Valuations do not contain keys for all clocks in PTA"

        return {
            label: dist
            for label, (guard, dist) in self._transitions[loc].items()
            if values in guard
        }

    def allowed_delays(self, loc: Location, values: Mapping[Clock, float]) -> Interval:
        return delays(values, self._invariants[loc])
