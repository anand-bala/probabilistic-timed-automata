from pytest import approx

import pta
from pta.clock import ClockConstraint

test_singleton_constraints():
    x, y, z = pta.new_clocks(('x', 'y', 'z'))

    assert (x < y) == 
