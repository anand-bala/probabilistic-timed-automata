"""Probabilistic Timed Automaton"""

from typing import Set, Hashable, Mapping, Tuple, Union

import attr

from .clocks import Clock, ClockConstraint, delays, Interval
from .distributions import DiscreteDistribution
from .region import Region


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

    @property
    def clocks(self) -> Set[Clock]:
        """Get the set of clocks in the PTA"""
        return self._clocks

    @property
    def locations(self) -> Set[Location]:
        """Get the set of locations in the PTA"""
        return self._locations

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
        """Return the allowed interval of delays at the given location and clock valuation.

        See Also
        --------
        `pta.clocks.delays`
        """
        return delays(values, self._invariants[loc])

    def to_region_mdp(self) -> "RegionMDP":
        """Get the integral region graph MDP of the PTA"""
        return RegionMDP(self)


@attr.s(auto_attribs=True, eq=False, order=False)
class RegionMDP:
    """An integral region graph MDP simulation of a PTA with generator API.

    The region MDP shouldn't be directly constructed as it requires access to
    private information of the PTA. Instead, use the `PTA.to_region_mdp()`
    method.
    """

    _pta: PTA = attr.ib()
    _current_region: Region = attr.ib(init=False)

    def __attrs_post_init__(self):
        self._current_region = Region(self._pta.clocks)
