"""Modelling alphabets for the PTA.

.. seealso::
    This module mostly adapted from the `DFA package
    <https://github.com/mvcisback/dfa/blob/master/dfa/alphabet.py>`_ for
    deterministic finite automata.

LICENSE
-------

MIT License

Copyright (c) 2019 Marcell Vazquez-Chanlatte

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from __future__ import annotations

import abc
from functools import total_ordering
from itertools import product
from typing import FrozenSet, Hashable, Iterable

import attr

Letter = Hashable


# NOTE: Defined Alphabet as an Abstract Class as opposed to a Union as it helps mypy
# NOTE: Needed to make this an Iterable because set(Set[...]) is empty for some reason...
class Alphabet(abc.ABC, Iterable):
    @abc.abstractmethod
    def __iter__(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def __contains__(self, elem):
        raise NotImplementedError()

    @abc.abstractmethod
    def __len__(self):
        raise NotImplementedError()

    def __lt__(left, right):
        """Partial order on subsets"""
        if isinstance(left, ProductAlphabet) and isinstance(right, ProductAlphabet):
            return (left.left < right.left) and (left.right < right.right)
        if isinstance(left, ExponentialAlphabet) and isinstance(
            right, ExponentialAlphabet
        ):
            return left.dim == right.dim and left.base < right.base
        return set(left) < set(right)

    def __eq__(left, right):
        """Equality on alphabets"""
        if isinstance(left, ProductAlphabet) and isinstance(right, ProductAlphabet):
            return (left.left == right.left) and (left.right == right.right)
        if isinstance(left, ExponentialAlphabet) and isinstance(
            right, ExponentialAlphabet
        ):
            return left.dim == right.dim and left.base == right.base
        return set(left) == set(right)


@attr.s(frozen=True, auto_attribs=True, eq=False, repr=False)
@total_ordering
class ExplicitAlphabet(Alphabet):
    """An Alphabet defined by a finite set"""

    _chars: FrozenSet[Letter] = attr.ib(converter=frozenset)

    @property
    def chars(self) -> FrozenSet[Letter]:
        return self._chars

    def __hash__(self):
        return hash(self.chars)

    def __eq__(self, other):
        if isinstance(other, ExplicitAlphabet):
            return self.chars == other.chars
        return set(self) == set(other)

    def __iter__(self):
        return iter(self.chars)

    def __len__(self):
        return len(self.chars)

    def __contains__(self, elem):
        return elem in self.chars

    def __repr__(self):
        return repr(set(self.chars))


def _alphabet_converter(alphabet) -> Alphabet:
    if isinstance(alphabet, Alphabet):
        return alphabet
    return ExplicitAlphabet(alphabet)


@attr.s(frozen=True, auto_attribs=True, eq=False, repr=False)
@total_ordering
class ProductAlphabet(Alphabet):
    """Product alphabet helper.

    Implicitely encodes the produce alphabet of two other alphabets.
    """

    left: Alphabet = attr.ib(converter=_alphabet_converter)
    right: Alphabet = attr.ib(converter=_alphabet_converter)

    def __hash__(self):
        return hash((self.left, self.right))

    def __contains__(self, elem):
        assert len(elem) == 2
        return (elem[0] in self.left) and (elem[1] in self.right)

    def __iter__(self):
        return product(self.left, self.right)

    def __repr__(self):
        return "{} x {}".format(set(self.left), set(self.right))

    def __len__(self):
        return len(self.left) * len(self.right)


@attr.s(frozen=True, auto_attribs=True, eq=False, order=False, repr=False)
@total_ordering
class ExponentialAlphabet(Alphabet):
    """Product of base alphabet with itself dim times"""

    _base: Alphabet = attr.ib(converter=_alphabet_converter)
    _dim: int = attr.ib(default=1)

    @_dim.validator
    def _positive(self, _, value):
        if value <= 0:
            raise ValueError(
                "Dimension of exponential alphabet must be positive, got {}".format(
                    value
                )
            )

    @property
    def base(self) -> Alphabet:
        return self._base

    @property
    def dim(self) -> int:
        return self._dim

    def __hash__(self):
        return hash((self.base, self.dim))

    def __contains__(self, elem):
        # Assume that the elem is indeed iterable
        for i, e in enumerate(elem):
            if (i >= self.dim) or (e not in self.base):
                return False
        return i + 1 == self.dim

    def __repr__(self):
        return "{}^{}".format(self.base, self.dim)

    def __len__(self):
        return self.dim * len(self.base)

    def __iter__(self):
        return product(self.base, repeat=self.dim)


# TODO: Add support for Real valued Alphabet (delays and timed actions)

__all__ = [
    "ExplicitAlphabet",
    "ProductAlphabet",
    "ExponentialAlphabet",
]
