"""The Region data structure for simulating PTA."""

from typing import MutableMapping, Set, Mapping

import attr

from .clocks import Clock


@attr.s(auto_attribs=True)
class Region:
    """Efficient data structure to model an Integral Region of the PTA.[^1]

    References
    ----------
    [^1]: A. Hartmanns, S. Sedwards, and P. R. D’Argenio,
        "Efficient simulation-based verification of probabilistic timed automata,"
        in Proceedings of the 2017 Winter Simulation Conference, Las Vegas, Nevada,
        2017, pp. 1–12.
    """

    _clocks: Set[Clock] = attr.ib()
    _is_int: bool = attr.ib(init=False)

    _value_vector: MutableMapping[Clock, int] = attr.ib(init=False)
    _fractional_ord: MutableMapping[Clock, int] = attr.ib(init=False)
    _num_frac: int = attr.ib(init=False)

    @property
    def clocks(self) -> Set[Clock]:
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

        def value_fn(clock: Clock) -> float:
            return self._value_vector[clock] + (
                (2 * self._fractional_ord[clock] + int(self._is_int))
                / (2.0 * self._num_frac)
            )

        return {c: value_fn(c) for c in self.clocks}

    def delay(self, steps: int = 1):
        """Delay each of the clocks and move by ``steps`` "representative" region.

        If ``steps`` is 1, the region is updated to the next region. Otherwise,
        for ``steps`` > 1, the number of regions moved is dependent on the
        fractional order, etc.
        """
        assert steps >= 1, "At lease 1 step must be taken when PTA is delayed."

        if steps == 1:
            if not self.is_int:
                self._fractional_ord = {
                    clock: (val + 1) % self._num_frac
                    for clock, val in self._fractional_ord.items()
                }
                self._value_vector = {
                    clock: val + int(self._fractional_ord[clock] == 0)
                    for clock, val in self._value_vector.items()
                }
            self._is_int = not self._is_int
        else:
            self._value_vector = {
                clock: val
                + (
                    (2 * self._fractional_ord[clock] + int(self.is_int) + steps)
                    // (2 * self._num_frac)
                )
                for clock, val in self._value_vector.items()
            }

            self._fractional_ord = {
                clock: ((frac + (steps + int(self.is_int)) // 2) % self._num_frac)
                for clock, frac in self._fractional_ord.items()
            }

            if steps % 2 == 1:
                self._is_int = not self._is_int

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

        self._num_frac += int(not same) - int(self.is_int)
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
