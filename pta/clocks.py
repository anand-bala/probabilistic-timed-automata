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
from typing import Hashable

import attr


@attr.s(frozen=True, auto_attribs=True, order=False)
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
        return And(self, other)


@attr.s(frozen=True, auto_attribs=True, order=False)
class Boolean(ClockConstraint):
    value: bool = attr.ib()

    def __and__(self, other: ClockConstraint) -> ClockConstraint:
        if self.value:
            return other
        return Boolean(False)


@attr.s(frozen=True, auto_attribs=True, order=False)
class And(ClockConstraint):
    lhs: ClockConstraint = attr.ib()
    rhs: ClockConstraint = attr.ib()


@unique
class ComparisonOp(Enum):
    GE = auto()
    GT = auto()
    LE = auto()
    LT = auto()


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
