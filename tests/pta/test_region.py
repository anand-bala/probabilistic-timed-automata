from pytest import approx
from pta import Region, new_clocks


def test_region_value():
    """Check if the region outputs the correct values given a series of delays"""
    x, y, z = new_clocks(("x", "y", "z"))

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

    reg.delay(1)
    assert reg.value() == {x: approx(5 / 3), y: approx(1 / 3), z: 2.0}

    reg.reset(z)
    assert reg.value() == {x: approx(5 / 3), y: approx(1 / 3), z: 0}


def test_delay_float():
    """Check if delaying by a floating point returns same values"""
    x, y, z = new_clocks(("x", "y", "z"))
    reg1 = Region((x, y, z))
    reg2 = Region((x, y, z))

    assert reg1.delay(1).value() == reg2.delay_float(0.5).value()
    assert reg1.reset(x).value() == reg2.reset(x).value()
    assert reg1.delay(1).value() == reg2.delay_float(0.25).value()
    assert reg1.delay(4).value() == reg2.delay_float(1.0).value()
    assert reg1.reset(y).value() == reg2.reset(y).value()
    assert reg1.delay(1).value() == reg2.delay_float(1 / 6).value()
    assert reg1.delay(1).value() == reg2.delay_float(1 / 6).value()
