"""Collection of distributions for the PTA and the Region MDP"""

import random
from itertools import product

from typing import Generic, TypeVar, Hashable, Mapping, Sequence, Set

import attr
import funcy as fn


# TODO: Is it worth using numpy or torch distributions instead? No (I think)...

# DiscreteSpace = TypeVar('DiscreteSpace', Hashable)
T = TypeVar('T', bound=Hashable)


@attr.s(frozen=True, auto_attribs=True)
class DiscreteDistribution(Generic[T]):
    """A Discrete distribution over a finite, countable support"""
    _dist: Mapping[T, float] = attr.ib()

    def sample(self, *, k: int = 1) -> Sequence[T]:
        """Sample a value from the support

        :param k: Number of items to sample from the distribution.
        """
        support, distribution = zip(*self._dist.items())
        return random.choices(support, distribution, k=k)

    @fn.memoize
    def __call__(self, x: T) -> float:
        """Get the probability of ``x`` in the distribution"""
        return self._dist.get(x, 0)


def delta(center: T) -> DiscreteDistribution[T]:
    """Return the (Kronecker) delta distribution centered at ``center``

    Essentially, the distributon is the following:

    .. math::

        \\texttt{Unit}(\\omega)(x) = \\begin{cases}
            1, \\quad \\text{for } x = \\omega \\\\
            0, \\quad \\text{otherwise.}
        \\end{cases}

    :param center: Center of the delta distribution
    """
    return DiscreteDistribution(dict([(center, 1)]))


def uniform(support: Set[T]) -> DiscreteDistribution[T]:
    """Return the uniform distribution over the given support

    :param support: Any finite set of states.
    """
    prob = 1 / len(support)
    return DiscreteDistribution({s: prob for s in support})
