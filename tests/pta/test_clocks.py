from pytest import approx
import pytest

import pta
import pta.clock as clk

def test_singleton_constraints():
    x, y, z = pta.new_clocks(('x', 'y', 'z'))

    with pytest.raises(TypeError):
        x < y
