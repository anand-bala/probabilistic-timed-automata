from itertools import product

from pta.alphabet import *


class TestExplicitAlph:
    def test_init(self):
        set_alph = {0, 1, 2, 3, 4, 5}
        alph = ExplicitAlphabet(range(6))

        assert set_alph == set(alph)

    def test_repr(self):
        assert repr(ExplicitAlphabet({0, 1})) == "{0, 1}"


class TestExponentialAlph:
    def test_init(self):
        alph = ExponentialAlphabet(range(4), 3)
        assert (0, 0, 0) in alph
        assert set(alph) == set(product(range(4), repeat=3))

        assert set(product(range(3), repeat=3)) < alph
