"""Probabilistic Timed Automaton"""

from typing import (
    Set,
    FrozenSet,
    Hashable,
    Mapping,
    Tuple,
    TypeVar,
    Generic,
    Optional,
)

import attr

from .clock import Clock, ClockConstraint, delays, Interval
from .distributions import DiscreteDistribution
from .region import Region


# Action = Union[str, int]
Action = TypeVar("Action", bound=Hashable)
Label = str
Location = TypeVar("Location", bound=Hashable)


Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]

TransitionFn = Mapping[Location, Mapping[Action, Transition]]


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
class PTA(Generic[Location, Action]):
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

    def to_region_mdp(self) -> "RegionMDP":
        """Get the integral region graph MDP of the PTA"""
        return RegionMDP(self)


@attr.s(auto_attribs=True, eq=False, order=False)
class RegionMDP(Generic[Location, Action]):
    """An integral region graph MDP simulation of a PTA with generator API.

    The region MDP shouldn't be directly constructed as it requires access to
    private information of the PTA. Instead, use the `PTA.to_region_mdp()`
    method.
    """

    _pta: PTA[Location, Action] = attr.ib()
    _current_region: Region = attr.ib(init=False)
    _current_location: Location = attr.ib(init=False)

    # MDPState = Tuple[Location, float] # (PTA state, representative valuation)
    # MDPAction = Union[float, Action] # Delay time or pick an edge

    def __attrs_post_init__(self):
        self._current_region = Region(self._pta.clocks)
        self._current_location = self._pta.initial_location

    @property
    def _current_transitions(self) -> Mapping[Action, Transition]:
        return self._pta._transitions[self.location]

    @property
    def location(self) -> Location:
        """The current location of the MDP"""
        return self._current_location

    @property
    def clock_valuation(self) -> Mapping[Clock, float]:
        """The current clock valuation"""
        return self._current_region.value()

    def enabled_actions(self) -> Mapping[Action, DiscreteDistribution[Target]]:
        """Return the set of enabled edges available given the current state of the MDP

        Returns
        -------
        :
            Set of distributions corresponding to edges enabled in the location
            with respect to their guards and the clock valuations.
        """
        return self._pta.enabled_actions(self.location, self.clock_valuation)

    def invariant_interval(self) -> Interval:
        """Return the allowed interval of delays before the invariant associated with the location turns false."""
        return self._pta.allowed_delays(self.location, self.clock_valuation)

    def reset(self) -> Tuple[Location, Mapping[Clock, float]]:
        """Reset the PTA to an initial state
        """
        self.__attrs_post_init__()
        return self.location, self.clock_valuation

    def delay(self, time: float) -> Optional[Tuple[Location, Mapping[Clock, float]]]:
        """Stay in the current location and delay by ``time`` amount.

        Parameters
        ----------
        time:
            The duration to delay taking an action

        Returns
        -------
        :
            If delaying by ``time`` amount leads to the current location's
            invariant being violated, the returned value is ``None`` as this
            implies the scheduler is bad and has driven the system into
            a non-recoverable state.

            Otherwise, the Region MDP moves to a successor region like so:

            .. math::

                \\langle q, R \\rangle \\to \\langle q, R' \\rangle

            where, :math:`q` is the current location, :math:`R` is the current
            region and :math:`R'` is the successor region.

            For more details, read the paper [Hartmanns2017]_.
        """
        # First check if the delay time exceeds the allowed time
        if not self.invariant_interval().contains(time):
            return None

        # We know time is allowable, thus, we need to update the current region with time.
        self._current_region.delay_float(time)
        return self.location, self.clock_valuation
