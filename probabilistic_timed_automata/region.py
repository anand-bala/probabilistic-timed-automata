"""The Region data structure for simulating PTA."""

from typing import List

import attr
import funcy as fn
import operator import add


@attr.s(auto_attribs=True)
class Region(object):
    """Data structure to model an Integral Region of the PTA.

    This data structure is based on the paper [Hartmanns2017]_ for efficient,
    region-based simulations of PTA.

    Instance Variables
    ------------------

    - ``n_clocks``: The number of clocks the region structure needs to keep track of.
    - ``is_int``:   ``True`` if any of the clocks have integer valuation.

    ..  [Hartmanns2017] A. Hartmanns, S. Sedwards, and P. R. D’Argenio,
        "Efficient simulation-based verification of probabilistic timed automata,"
        in Proceedings of the 2017 Winter Simulation Conference, Las Vegas, Nevada,
        2017, pp. 1–12.
    """

    _n_clocks: int = attr.ib()
    _is_int: bool = attr.ib(default=True, kw_only=True)

    _value_vector: List[int] = attr.ib(kw_only=True)
    _fractional_ord: List[int] = attr.ib(kw_only=True)
    _num_frac: int = attr.ib(default=0, kw_only=True)

    @property
    def n_clocks(self):
        """The number of clocks in the region."""
        return self._n_clocks

    @property
    def is_int(self):
        """``True`` if any of the clocks have integer valuation."""
        return self._is_int

    @_n_clocks.validator
    def _check_n_clocks(self, attribute: attr.Attribute, value: int):
        if value < 0:
            raise ValueError("n_clocks must be a non-negative integer")

    @_value_vector.default
    def _value_vector_default(self) -> List[int]:
        return [0]*self.n_clocks

    @_fractional_ord.default
    def _fractional_ord_default(self) -> List[int]:
        return [0]*self.n_clocks

    def value(self) -> List[float]:
        """Get the representative values of the clocks in the current region

        The representative value of the region depends on the integer value and
        the *fractional order* of the individual valuations.
        """
        def value_fn(clock: int) -> float:
            return(self._value_vector[clock] + ((2 * self._fractional_ord[clock] + int(self._is_int)) / (2.0 * self._num_frac)))
        return [value_fn(c) for c in range(self.n_clocks)]

    def delay(self, steps: int = 1):
        """Delay each of the clocks and move ``steps`` "representative" region.

        If ``steps`` is 1, the region is updated to the next region. Otherwise,
        for ``steps`` > 1, the number of regions moved is dependent on the
        fractional order, etc.
        """
        assert steps >= 1, "At lease 1 step must be taken when PTA is delayed."

        if steps == 1:
            if not self.is_int:
                self._fractional_ord = fn.lmap(lambda x: (
                    x + 1) % self._num_frac, self._fractional_ord)
                self._value_vector = fn.lmap(
                    lambda val, frac: val + int(frac == 0), self._value_vector, self._fractional_ord)
            self._is_int = not self._is_int
        else:
            self._value_vector = fn.lmap(lambda val, frac: val + (2 * frac + int(
                self.is_int) + steps)//(2 * self._num_frac), self._value_vector, self._fractional_ord)
            self._fractional_ord = fn.lmap(lambda frac: (
                frac + (steps + int(self.is_int)) // 2) % self._num_frac, self._fractional_ord)

            if steps % 2 == 1:
                self._is_int = not self._is_int

    def reset(self, reset_clock: int):
        """Reset the given clock to 0"""
        assert 0 <= reset_clock < self.n_clocks, "Invalid clock id."

        if self.is_int and self._fractional_ord[reset_clock] == 0:
            self._value_vector[reset_clock] = 0
            return

        same: bool = fn.any(
            lambda i, frac: (i != reset_clock and frac ==
                             self._fractional_ord[reset_clock]),
            enumerate(self._fractional_ord)
        )

        self._num_frac += int(not same) - int(self.is_int)
        for c in range(self.n_clocks):
            if c == reset_clock:
                continue
            if not same and (self._fractional_ord[c]
                             > self._fractional_ord[reset_clock]):
                self._fractional_ord[c] = (self._fractional_ord[c] - 1) % self._num_frac
            if not self.is_int:
                self._fractional_ord[c] = (self._fractional_ord[c] + 1) % self._num
        
        self._fractional_ord[reset_clock] = 0
        self._value_vector[reset_clock] = 0
        self._is_int = True

