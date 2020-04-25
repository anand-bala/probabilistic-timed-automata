from typing import (
    Set,
    Hashable,
    Mapping,
    Tuple,
    Optional,
    Union,
    FrozenSet,
    Iterable,
    MutableMapping,
)

import attr

from pta.clock import Clock, ClockConstraint, Interval, ClockValuation
from pta.distributions import DiscreteDistribution
from pta.pta import PTA


# Action = Union[str, int]
Action = Hashable
Label = str
Location = Hashable


Target = Tuple[Set[Clock], Location]
Transition = Tuple[ClockConstraint, DiscreteDistribution[Target]]

TransitionFn = Mapping[Location, Mapping[Action, Transition]]


def _frozen_converter(x: Union[Set, FrozenSet, Iterable]) -> FrozenSet:
    return frozenset(x)


@attr.s(auto_attribs=True)
class Region:
    """Efficient data structure to model an Integral Region of the PTA [Hartmanns2017]_
    """

    _clocks: FrozenSet[Clock] = attr.ib(converter=_frozen_converter)
    _is_int: bool = attr.ib(init=False)

    _value_vector: MutableMapping[Clock, int] = attr.ib(init=False)
    _fractional_ord: MutableMapping[Clock, int] = attr.ib(init=False)
    _num_frac: int = attr.ib(init=False)

    @property
    def clocks(self) -> FrozenSet[Clock]:
        """The set of clocks in the region"""
        return self._clocks

    @property
    def n_clocks(self) -> int:
        """The number of clocks in the region."""
        return len(self._clocks)

    @property
    def is_int(self) -> bool:
        """``True`` if any of the clocks have integer valuation."""
        return self._is_int

    def __attrs_post_init__(self):
        self._is_int = True
        self._value_vector = {clock: 0 for clock in self.clocks}
        self._fractional_ord = {clock: 0 for clock in self.clocks}
        self._num_frac = 1

    def value(self) -> ClockValuation:
        """Get the representative values of the clocks in the current region

        The representative value of the region depends on the integer value and
        the *fractional order* of the individual valuations.
        """

        def val_comp(clock) -> float:
            return self._value_vector[clock] + (
                (2 * self._fractional_ord[clock] + int(not self.is_int))
                / (2.0 * self._num_frac)
            )

        return ClockValuation({clock: val_comp(clock) for clock in self._clocks})  # type: ignore

    def delay(self, steps: int = 1) -> "Region":
        """Delay each of the clocks and move by ``steps`` "representative" region.

        Parameters
        ----------
        steps: int
            An integer >= 1 such that the region takes that many representative steps.

        Returns
        -------
        :
            The updated region (a reference to self)
        """
        assert steps >= 1, "At lease 1 step must be taken when PTA is delayed."
        self._value_vector = {
            clock: val
            + (
                (2 * self._fractional_ord[clock] + int(not self.is_int) + steps)
                // (2 * self._num_frac)
            )
            for clock, val in self._value_vector.items()
        }

        self._fractional_ord = {
            clock: ((frac + (steps + int(not self.is_int)) // 2) % self._num_frac)
            for clock, frac in self._fractional_ord.items()
        }

        if steps % 2 == 1:
            self._is_int = not self._is_int
        return self

    def delay_float(self, time: float) -> "Region":
        """Delay the region by ``time``. Wrapper around `delay`.
        """
        steps = int(time * 2 * self._num_frac)
        return self.delay(steps)

    def reset(self, reset_clock: Clock) -> "Region":
        """Reset the given clock to 0"""
        assert 0 <= reset_clock < self.n_clocks, "Invalid clock id."

        if self.is_int and self._fractional_ord[reset_clock] == 0:
            self._value_vector[reset_clock] = 0
            return self

        same: bool = any(
            frac == self._fractional_ord[reset_clock]
            for clock, frac in self._fractional_ord.items()
            if clock != reset_clock
        )

        self._num_frac -= int(not same)
        self._num_frac += int(not self.is_int)
        for clk in self.clocks:
            if clk == reset_clock:
                continue
            if not same and (
                self._fractional_ord[clk] > self._fractional_ord[reset_clock]
            ):
                self._fractional_ord[clk] = (
                    self._fractional_ord[clk] - 1
                ) % self._num_frac
            if not self.is_int:
                self._fractional_ord[clk] = (
                    self._fractional_ord[clk] + 1
                ) % self._num_frac

        self._fractional_ord[reset_clock] = 0
        self._value_vector[reset_clock] = 0
        self._is_int = True
        return self


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
    def clock_valuation(self) -> ClockValuation:
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

    def reset(self) -> Tuple[Location, ClockValuation]:
        """Reset the PTA to an initial state
        """
        self.__attrs_post_init__()
        return self.location, self.clock_valuation

    def delay(self, time: float) -> Optional[Tuple[Location, ClockValuation]]:
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
