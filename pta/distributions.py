"""Collection of useful distributions"""
from __future__ import annotations
from abc import ABC, abstractmethod
import random

# from itertools import product
import functools

from typing import Generic, TypeVar, Hashable, Mapping, Sequence, Set

import attr

# TODO: Is it worth using numpy or torch distributions instead? No (I think)...

# DiscreteSpace = TypeVar('DiscreteSpace', Hashable)
T = TypeVar("T", bound=Hashable)


@attr.s(frozen=True, auto_attribs=True)
class Distribution(ABC):
    @abstractmethod
    def sample(self, *, k: int = 1) -> Sequence:
        """Sample `k` values from the support

        Parameters
        ----------
        k : int
            Number of items to sample from the distribution.

        """

    @abstractmethod
    def validate_support(self, arg1):
        """TODO: Docstring for validate_support.

        :arg1: TODO
        :returns: TODO

        """


@attr.s(frozen=True, auto_attribs=True)
class DiscreteDistribution(Generic[T]):
    """A Discrete distribution over a finite, countable support

    You can call the instantiated distribution to get the probability of an input::

        p = uniform(range(10))
        assert p(5) == 1/10

    """

    _dist: Mapping[T, float] = attr.ib()

    def sample(self, *, k: int = 1) -> Sequence[T]:
        """Sample a value from the support

        Parameters
        ----------
        k : int
            Number of items to sample from the distribution.
        """
        support, distribution = zip(*self._dist.items())
        return random.choices(support, distribution, k=k)

    @functools.lru_cache(128)
    def __call__(self, x: T) -> float:
        """Get the probability of ``x`` in the distribution"""
        return self._dist.get(x, 0)

    def validate_support(self, check_set: Set[T]) -> bool:
        return not (set(self._dist.keys()) <= check_set)

    @classmethod
    def delta(cls, center: T) -> DiscreteDistribution[T]:
        """Return the (Kronecker) delta distribution centered at ``center``

        Essentially, the distributon is the following:

        .. math::

            \\texttt{Unit}(\\omega)(x) = \\begin{cases}
                1, \\quad \\text{for } x = \\omega \\\\
                0, \\quad \\text{otherwise.}
            \\end{cases}

        Parameters
        ----------
        center : Hashable
            Center of the delta distribution
        """
        return DiscreteDistribution(dict([(center, 1)]))

    @classmethod
    def uniform(cls, support: Set[T]) -> DiscreteDistribution[T]:
        """Return the uniform distribution over the given support

        Parameters
        ----------
        support : Hashable
            Any finite set of states.

        Returns
        -------
        output : DiscreteDistribution
            A uniform distribution over the finite set of states.
        """
        prob = 1 / len(support)
        return DiscreteDistribution({s: prob for s in support})
