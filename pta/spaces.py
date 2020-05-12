from abc import abstractmethod
from functools import reduce
from typing import Protocol, Sequence, Tuple, runtime_checkable


@runtime_checkable
class Space(Protocol):
    """Defines the observation and action spaces, so you can write generic
    code that applies to any Env. For example, you can choose a random
    action.
    """

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def sample(self):
        """Randomly sample an element of this space. Can be
        uniform or non-uniform sampling based on boundedness of space."""
        raise NotImplementedError

    @abstractmethod
    def __contains__(self, x) -> bool:
        """
        Return boolean specifying if x is a valid
        member of this space
        """
        raise NotImplementedError


class ProductSpace(Space):
    spaces: Tuple[Space, ...]

    def __init__(self, *spaces: Space):
        self.spaces = tuple(spaces)

    def __len__(self) -> int:
        return reduce(lambda s1, s2: s1 * s2, [len(s) for s in self.spaces])

    def __contains__(self, x):
        assert isinstance(x, Sequence) and len(x) == len(
            self.spaces
        ), f"Product needs to be a tuple-like of size {len(self.spaces)}..."
        return all([s.__contains__(x[i]) for i, s in enumerate(self.spaces)])

    def sample(self):
        return tuple(s.sample() for s in self.spaces)
