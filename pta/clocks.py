"""Symbolic Representation for Clock Constraints

Clock constraints are of the following form::

    cc ::=  true | false |
            cc & cc |
            c ~ n | c_1 - c_2 ~ n

Here, ``~`` is one of ``<,<=,>=,>``, ``c, c_i`` are any ``Clock`` names, and
``n`` is a natural number.
"""

from abc import ABC
from enum import Enum, auto, unique
from typing import Hashable, Mapping, Tuple, Callable
import operator

import attr

# NOTE:
#   Currently using this library for intervals, but may use a custom Intervall
#   class in the future.
import portion as P
from portion import Interval


@attr.s(frozen=True, auto_attribs=True, order=False, eq=True)
class Clock:
    name: Hashable = attr.ib()

    def __lt__(self, other: int) -> 'ClockConstraint':
        if other <= 0:
            # NOTE: Doesn't make sense for clock to be less than 0!
            return Boolean(False)
        return SingletonConstraint(self, other, ComparisonOp.LT)

    def __le__(self, other: int) -> 'ClockConstraint':
        if other < 0:
            # NOTE: Doesn't make sense for clock to be less than 0!
            return Boolean(False)
        return SingletonConstraint(self, other, ComparisonOp.LE)

    def __gt__(self, other: int) -> 'ClockConstraint':
        if other < 0:
            # NOTE: The clock value must always be >= 0
            return Boolean(True)
        return SingletonConstraint(self, other, ComparisonOp.GT)

    def __ge__(self, other: int) -> 'ClockConstraint':
        if other <= 0:
            # NOTE: The clock value must always be >= 0
            return Boolean(True)
        return SingletonConstraint(self, other, ComparisonOp.GE)

    def __sub__(self, other: 'Clock') -> 'DiagonalLHS':
        return DiagonalLHS(self, other)


class ClockConstraint(ABC):

    def __and__(self, other: 'ClockConstraint') -> 'ClockConstraint':
        if isinstance(other, Boolean):
            if other.value:
                return self
            return other
        return And((self, other))


@attr.s(frozen=True, auto_attribs=True, order=False)
class Boolean(ClockConstraint):
    value: bool = attr.ib()

    def __and__(self, other: ClockConstraint) -> ClockConstraint:
        if self.value:
            return other
        return Boolean(False)


@attr.s(frozen=True, auto_attribs=True, order=False)
class And(ClockConstraint):
    args: Tuple[ClockConstraint, ClockConstraint] = attr.ib()


@unique
class ComparisonOp(Enum):
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
    clock: Clock = attr.ib()
    rhs: int = attr.ib()
    op: ComparisonOp = attr.ib()

    @rhs.validator
    def _rhs_validator(self, attribute, value):
        if value < 0:
            raise ValueError("Clock constraint can't be negative")


@attr.s(frozen=True, auto_attribs=True, order=False)
class DiagonalLHS:
    clock1: Clock = attr.ib()
    clock2: Clock = attr.ib()

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
    """Diagonal constraints of the form: ``clock1 - clock2 ~ n```"""
    lhs: DiagonalLHS = attr.ib()
    rhs: int = attr.ib()
    op: ComparisonOp = attr.ib()

    @rhs.validator
    def _rhs_validator(self, attribute, value):
        if value < 0:
            raise ValueError("Clock constraint can't be negative")


def delays(values: Mapping[Clock, float], constraint: ClockConstraint) -> Interval:
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
    raise TypeError("Unsupported ClockConstraint type: {}"
                    .format(type(constraint)))
