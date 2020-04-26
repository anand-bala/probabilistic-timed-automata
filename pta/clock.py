"""Symbolic Representation for Clock Constraints

Clock constraints are of the following form::

    cc ::=  true | false |
            cc & cc |
            c ~ n | c_1 - c_2 ~ n

Here, ``~`` is one of ``<,<=,>=,>``, ``c, c_i`` are any ``Clock`` names, and
``n`` is a natural number.

The `Clock` and `ClockConstraint` classes have syntactic sugar to easily write the above constraints. For example::

    x = Clock('x')
    y = Clock('y')

    assert x & y == And((Clock('x'), Clock('y')))
    assert (x - y >= 0) == DiagonalConstraint(DiagonalLHS(x, y), 0)

Moreover, the `Clock` and `ClockConstraint` are *frozen*, which emulates immutable data.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto, unique
from typing import Hashable, Mapping, Tuple, Callable, Dict, Iterator, Iterable
import operator


import attr
import attr.validators as VAL

# NOTE:
#   Currently using this library for intervals, but may use a custom Intervall
#   class in the future.
import portion as P
from portion import Interval


@attr.s(frozen=True, auto_attribs=True, order=False, eq=True, repr=False, hash=True)
class Clock:
    """A Clock symbol

    The Clock class is a simple wrapper around any Hashable. For example::

        x = Clock('x')
        y = Clock('y')

    In the above example, the variables ``x`` and ``y`` are clocks with the *name* (a hashable string).
    """

    name: Hashable = attr.ib(validator=VAL.instance_of(Hashable))

    def __lt__(self, other: int) -> "ClockConstraint":
        if not isinstance(other, int):
            raise TypeError(
                "Clock can only be compared to an int, got {}".format(type(other))
            )
        if other <= 0:
            # NOTE: Doesn't make sense for clock to be less than 0!
            return Boolean(False)
        return SingletonConstraint(self, other, ComparisonOp.LT)

    def __le__(self, other: int) -> "ClockConstraint":
        if not isinstance(other, int):
            raise TypeError(
                "Clock can only be compared to an int, got {}".format(type(other))
            )
        if other < 0:
            # NOTE: Doesn't make sense for clock to be less than 0!
            return Boolean(False)
        return SingletonConstraint(self, other, ComparisonOp.LE)

    def __gt__(self, other: int) -> "ClockConstraint":
        if not isinstance(other, int):
            raise TypeError(
                "Clock can only be compared to an int, got {}".format(type(other))
            )
        if other < 0:
            # NOTE: The clock value must always be >= 0
            return Boolean(True)
        return SingletonConstraint(self, other, ComparisonOp.GT)

    def __ge__(self, other: int) -> "ClockConstraint":
        if not isinstance(other, int):
            raise TypeError(
                "Clock can only be compared to an int, got {}".format(type(other))
            )
        if other <= 0:
            # NOTE: The clock value must always be >= 0
            return Boolean(True)
        return SingletonConstraint(self, other, ComparisonOp.GE)

    def __sub__(self, other: "Clock") -> "DiagonalLHS":
        return DiagonalLHS(self, other)

    def __repr__(self) -> str:
        return "Clock('{}')".format(self.name)


@attr.s(auto_attribs=True, slots=True, repr=False)
class ClockValuation(Mapping[Clock, float]):
    _values: Dict[Clock, float] = attr.ib(converter=dict)

    #  @_clocks.validator
    #  def _clocks_validator(self, _, value):
    #  if len(value) < 1:
    #  raise ValueError("Expected at least 1 clock... Are you looking for an MDP instead?")
    #  if not all([isinstance(c, Clock) for c in self._clocks]):
    #  raise TypeError("Expected a list of Clocks...")

    @_values.validator
    def _values_validator(self, _, value):
        if not all([isinstance(c, Clock) for c in self._values.keys()]):
            raise TypeError("Expected keys to be Clocks...")
        if not all([v >= 0 for v in self._values.values()]):
            raise ValueError("Clock values cannot be negative...")

    def __getitem__(self, clock: Clock) -> float:
        assert isinstance(clock, Clock)
        return self._values[clock]

    def __iter__(self) -> Iterator[Clock]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __repr__(self) -> str:
        return repr(self._values)

    @classmethod
    def zero_init(cls, clocks: Iterable[Clock]) -> "ClockValuation":
        """Zero initialize a `ClockValuation` for the given set of `Clock`

        Parameters
        ----------
        clocks : Iterable[Clock]
                 Set of clocks to track the valuation of

        Returns
        -------
        ClockValuation
                `ClockValuation` where each `Clock` has 0 valuation.
        """
        from itertools import repeat

        return ClockValuation(dict(zip(clocks, repeat(0))))  # type: ignore

    def __add__(self, other) -> "ClockValuation":
        if isinstance(other, float):
            new_vals = {clk: val + other for clk, val in self._values.items()}
            return ClockValuation(new_vals)  # type: ignore
        if isinstance(other, (ClockValuation, Mapping)):
            assert set(other.keys()) >= self._values.keys()
            new_vals = {clk: val + other[clk] for clk, val in self._values.items()}
            return ClockValuation(new_vals)  # type: ignore
        return NotImplemented


class ClockConstraint(ABC):
    """An abstract class for clock constraints"""

    def __and__(self, other: "ClockConstraint") -> "ClockConstraint":
        if isinstance(other, bool):
            other = Boolean(other)
        if isinstance(other, Boolean):
            if other.value:
                return self
            return other
        return And((self, other))

    @abstractmethod
    def contains(self, value: ClockValuation) -> bool:
        """Check if the clock constraints evaluate to true given clock valuations."""
        raise NotImplementedError(
            "Can't get the interval for the abstract ClockConstraint class"
        )

    def __contains__(self, value: ClockValuation) -> bool:
        return self.contains(value)


@attr.s(frozen=True, auto_attribs=True, order=False)
class Boolean(ClockConstraint):
    """An atomic boolean class to represent ``true`` and ``false`` clock constraints"""

    value: bool = attr.ib(validator=VAL.instance_of(bool))

    @value.validator
    def _value_validator(self, attribute, value):
        if not isinstance(value, bool):
            raise TypeError(
                "Boolean muse have a bool value, got {}".format(type(value))
            )

    def __and__(self, other: ClockConstraint) -> ClockConstraint:
        if isinstance(other, bool):
            other = Boolean(other)
        if self.value:
            return other
        return Boolean(False)

    def contains(self, value: ClockValuation) -> bool:
        return self.value


@attr.s(frozen=True, auto_attribs=True, order=False)
class And(ClockConstraint):
    """Class to represent conjunctions of clock constraints"""

    args: Tuple[ClockConstraint, ClockConstraint] = attr.ib()

    @args.validator
    def _args_validator(self, valuations, value):
        if not isinstance(value, tuple) or len(value) != 2:
            raise TypeError("Given args are not tuple of length 2: {}".format(value))
        if not isinstance(value[0], ClockConstraint) or not isinstance(
            value[1], ClockConstraint
        ):
            raise TypeError(
                "Value of both args must be ClockConstraint, got {}".format(
                    (type(value[0]), type(value[1]))
                )
            )

    def contains(self, value: ClockValuation) -> bool:
        return (value in self.args[0]) and (value in self.args[1])


@unique
class ComparisonOp(Enum):
    """Four comparison operations allowed in `SingletonConstraint` and `DiagonalConstraint` """

    GE = auto()
    GT = auto()
    LE = auto()
    LT = auto()

    def to_op(self) -> Callable[[float, float], bool]:
        """Output the operator function that corresponds to the enum"""
        if self == ComparisonOp.GE:
            return operator.ge
        if self == ComparisonOp.GT:
            return operator.gt
        if self == ComparisonOp.LE:
            return operator.le
        if self == ComparisonOp.LT:
            return operator.lt
        return operator.lt


@attr.s(frozen=True, auto_attribs=True, order=False)
class SingletonConstraint(ClockConstraint):
    """Constraints of the form \\(c \\sim n\\) for \\(n \\in \\mathbb{N}\\) and \\(\\sim \\in \\{<,\\le,\\ge,>\\}\\)"""

    clock: Clock = attr.ib(validator=VAL.instance_of(Clock))
    rhs: int = attr.ib()
    op: ComparisonOp = attr.ib(validator=VAL.instance_of(ComparisonOp))

    @clock.validator
    def _clock_validator(self, attribute, value):
        if not isinstance(value, Clock):
            raise TypeError(
                "SingletonConstraint can only contain Clock, got {}".format(type(value))
            )

    @rhs.validator
    def _rhs_validator(self, attribute, value):
        if value < 0:
            raise ValueError("Clock constraint can't be negative")

    def contains(self, value: ClockValuation) -> bool:
        return self.op.to_op()(value[self.clock], self.rhs)


@attr.s(frozen=True, auto_attribs=True, order=False)
class DiagonalLHS:
    """Intermediate result for \\(c_1 - c_2\\)"""

    clock1: Clock = attr.ib()
    clock2: Clock = attr.ib()

    @clock1.validator
    def _clock1_validator(self, attribute, value):
        if not isinstance(value, Clock):
            raise TypeError(
                "DiagonalConstraint can only contain Clock, got {}".format(type(value))
            )

    @clock2.validator
    def _clock2_validator(self, attribute, value):
        if not isinstance(value, Clock):
            raise TypeError(
                "DiagonalConstraint can only contain Clock, got {}".format(type(value))
            )

    def __call__(self, value: ClockValuation) -> float:
        return value[self.clock1] - value[self.clock2]

    def __lt__(self, other: int) -> ClockConstraint:
        return DiagonalConstraint(self, other, ComparisonOp.LT)

    def __le__(self, other: int) -> ClockConstraint:
        return DiagonalConstraint(self, other, ComparisonOp.LE)

    def __gt__(self, other: int) -> ClockConstraint:
        return DiagonalConstraint(self, other, ComparisonOp.GT)

    def __ge__(self, other: int) -> ClockConstraint:
        return DiagonalConstraint(self, other, ComparisonOp.GE)


# TODO(anand): Can there only be two clocks in a diagonal constraint?
@attr.s(frozen=True, auto_attribs=True, order=False)
class DiagonalConstraint(ClockConstraint):
    """Diagonal constraints of the form: \\(c_1 - c_2 \\sim n\\)"""

    lhs: DiagonalLHS = attr.ib()
    rhs: int = attr.ib()
    op: ComparisonOp = attr.ib()

    @rhs.validator
    def _rhs_validator(self, attribute, value):
        if not isinstance(value, int):
            raise TypeError(
                "DiagonalConstraint cannot be compared with type other than int, got {}".format(
                    type(value)
                )
            )
        if value < 0:
            raise ValueError("Clock constraint can't be negative")

    def contains(self, value: ClockValuation) -> bool:
        return self.op.to_op()(self.lhs(value), self.rhs)


def delays(values: ClockValuation, constraint: ClockConstraint) -> Interval:
    """Compute the allowable delay with the given clock valuations and constraints

    .. todo::
        Write the LaTeX version of the function.

    Parameters
    ----------
    values :
        A mapping from `Clock` to the valuation of the clock.
    constraint :
        A clock constrain.

    Returns
    -------
    :
        An interval that represents the set of possible delays that satisfy the
        given clock constraint.

    """
    if isinstance(constraint, Boolean):
        if constraint.value:
            return P.closed(0, P.inf)
        return P.empty()
    if isinstance(constraint, SingletonConstraint):
        v_c = values[constraint.clock]
        n: int = constraint.rhs
        if constraint.op == ComparisonOp.GE:
            return P.closed(n - v_c, P.inf)
        if constraint.op == ComparisonOp.GT:
            return P.open(n - v_c, P.inf)
        if constraint.op == ComparisonOp.LE:
            return P.closed(0, n - v_c)
        if constraint.op == ComparisonOp.LT:
            return P.closedopen(0, n - v_c)
    if isinstance(constraint, And):
        return delays(values, constraint.args[0]) & delays(values, constraint.args[1])
    if isinstance(constraint, DiagonalConstraint):
        v_c1 = values[constraint.lhs.clock1]
        v_c2 = values[constraint.lhs.clock2]
        op_fn = constraint.op.to_op()
        if op_fn(v_c1 - v_c2, n):
            return P.closed(0, P.inf)
        return P.empty()
    raise TypeError("Unsupported ClockConstraint type: {}".format(type(constraint)))
