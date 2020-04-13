import pytest

import pta


def test_singleton_constraints():
    x, y, z = pta.new_clocks(("x", "y", "z"))

    with pytest.raises(TypeError):
        x < y
