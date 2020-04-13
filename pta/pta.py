"""Probabilistic Timed Automaton"""

from typing import (
    Set,
    FrozenSet,
    Hashable,
    Mapping,
    Tuple,
    Optional,
)

import attr

from .clock import Clock, ClockConstraint, delays, Interval
from .distributions import DiscreteDistribution


# Action = Union[str, int]
Action = Hashable
Label = str
Location = Hashable


Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]

TransitionFn = Mapping[Location, Mapping[Action, Transition]]


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
class PTA:
    """
    A PTA is a tuple :math:`M = \\left\\langle Q, C, A, T, q_0, I, L \\right\\rangle` where

    - :math:`Q` is the set of locations in the PTA;
    - :math:`C` is the set of clocks in the PTA;
    - :math:`A` is the set of actions in the PTA;
    - :math:`T: Q \\times A \\to \\mathcal{CC} \\times \\textrm{Dist}(2^C
      \\times Q)` is the transition function that maps a location to a set of
      possible transitions that can be taken (and their associated guards),
      along with the probabilities associated with the set of clocks that are
      reset and the next location;
    - :math:`q_0` is the initial location in the PTA; and
    - :math:`I` is the invariant function that maps a location to a clock constraint
      such that as long as the clock constraint is satisfied, the clock can
      progress in the location.
    - :math:`L` is the labelling function, :math:`L : Q \\to 2^{\\textrm{AP}}`.

    Parameters
    ----------

    locations: Set[Location]
        The set of locations in the PTA
    clocks: Set[Clock]
        The set of clocks in the PTA
    actions: Set[Action]
        The set of actions in the PTA
    init_location: Location
        The entry point for the PTA
    transitions: TransitionFn
        Mapping from locations to set of (action, transition) pairs
    invariants: Mapping[Location, ClockConstraint]
        Mapping from locations to a clock constraint
    labels: Mapping[Location, Set[Label]]
        Mapping from locations to atomic predicate labels
    """

    _locations: FrozenSet[Location] = attr.ib(converter=frozenset)
    _clocks: FrozenSet[Clock] = attr.ib(converter=frozenset)
    _actions: FrozenSet[Action] = attr.ib(converter=frozenset)

    _init_location: Location = attr.ib()

    _transitions: TransitionFn = attr.ib()
    _invariants: Mapping[Location, ClockConstraint] = attr.ib()
    _labels: Mapping[Location, Set[Label]]

    @_init_location.validator
    def _init_location_validator(self, attribute: attr.Attribute, value: Location):
        if value not in self._locations:
            raise ValueError("Given initial location not in the set of locations")

    @_transitions.validator
    def _transitions_validator(self, attribute: attr.Attribute, value: TransitionFn):
        if not self._locations.issubset(set(value.keys())):
            raise ValueError(
                "Transition mapping does not contain a key for locations {} in the PTA",
                self._locations - set(value.keys()),
            )
        # TODO: check if the edges don't do anything stupid.

    @_invariants.validator
    def _invariants_validator(
        self, attribute: attr.Attribute, value: Mapping[Location, ClockConstraint]
    ):
        if not self._locations.issubset(set(value.keys())):
            raise ValueError(
                "Invariants mapping does not contain a key for locations {} in the PTA",
                self._locations - set(value.keys()),
            )
        # TODO: Check if clock constraints are only defined on known clocks...

    @property
    def clocks(self) -> FrozenSet[Clock]:
        """Get the set of clocks in the PTA"""
        return self._clocks

    @property
    def locations(self) -> FrozenSet[Location]:
        """Get the set of locations in the PTA"""
        return self._locations

    @property
    def actions(self) -> FrozenSet[Action]:
        """Get the set of actions in the PTA"""
        return self._actions

    @property
    def initial_location(self) -> Location:
        """Get the initial location of the PTA"""
        return self._init_location

    def labels(self, location: Location) -> Set[Label]:
        """Get the set of labels enabled at the given location"""
        return self._labels[location]

    def enabled_actions(
        self, loc: Location, values: Mapping[Clock, float]
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

        .. seealso::
            :py:func:`~pta.clocks.delays`
        """
        return delays(values, self._invariants[loc])
