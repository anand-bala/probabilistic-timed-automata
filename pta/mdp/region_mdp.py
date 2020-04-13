from typing import (
    Set,
    FrozenSet,
    Hashable,
    Mapping,
    Tuple,
    Optional,
)

import attr

from pta.clock import Clock, ClockConstraint, Interval
from pta.distributions import DiscreteDistribution
from pta.region import Region
from pta.pta import PTA


# Action = Union[str, int]
Action = Hashable
Label = str
Location = Hashable


Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]

TransitionFn = Mapping[Location, Mapping[Action, Transition]]


@attr.s(auto_attribs=True, eq=False, order=False)
class RegionMDP:
    """An integral region graph MDP simulation of a PTA with generator API.

    The region MDP shouldn't be directly constructed as it requires access to
    private information of the PTA. Instead, use the `PTA.to_region_mdp()`
    method.
    """

    _pta: PTA = attr.ib()
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
