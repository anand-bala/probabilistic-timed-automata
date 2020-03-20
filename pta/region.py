"""The Region data structure for simulating PTA."""

from typing import FrozenSet, Iterable, Mapping, MutableMapping, Set, Union

import attr

from .clock import Clock


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

    def value(self) -> Mapping[Clock, float]:
        """Get the representative values of the clocks in the current region

        The representative value of the region depends on the integer value and
        the *fractional order* of the individual valuations.
        """
        return {
            clock: self._value_vector[clock]
            + (
                (2 * self._fractional_ord[clock] + int(not self.is_int))
                / (2.0 * self._num_frac)
            )
            for clock in self.clocks
        }

    def delay(self, steps: int = 1):
        """Delay each of the clocks and move by ``steps`` "representative" region.
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

    def delay_float(self, time: float):
        """Delay the region by ``time``"""
        steps = int(time * 2 * self._num_frac)
        self.delay(steps)

    def reset(self, reset_clock: Clock):
        """Reset the given clock to 0"""
        assert 0 <= reset_clock < self.n_clocks, "Invalid clock id."

        if self.is_int and self._fractional_ord[reset_clock] == 0:
            self._value_vector[reset_clock] = 0
            return

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
