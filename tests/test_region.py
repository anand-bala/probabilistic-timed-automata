from pytest import approx
from pta import Region, clocks


def test_region_value():
    """Check if the region outputs the correct values given a series of delays"""
    x, y, z = clocks(("x", "y", "z"))

    reg = Region((x, y, z))
    assert reg.value() == {x: 0, y: 0, z: 0}

    reg.delay(1)
    assert reg.value() == {x: 0.5, y: 0.5, z: 0.5}

    reg.reset(x)
    assert reg.value() == {x: 0.0, y: 0.5, z: 0.5}

    reg.delay(1)
    assert reg.value() == {x: 0.25, y: 0.75, z: 0.75}

    reg.delay(4)
    assert reg.value() == {x: 1.25, y: 1.75, z: 1.75}

    reg.reset(y)
    assert reg.value() == {x: approx(4 / 3), y: 0.0, z: approx(5 / 3)}

    reg.delay(1)
    assert reg.value() == {
        x: approx(4 / 3 + 1 / 6),
        y: approx(1 / 6),
        z: approx(5 / 3 + 1 / 6),
    }


# TODO: rest of testing
