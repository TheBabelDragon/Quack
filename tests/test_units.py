"""Unit / dimension tests."""

from quack.units import Current, Mass, Resistance, Voltage, lookup_unit


def test_lookup():
    assert lookup_unit("Voltage") is Voltage


def test_compatible():
    assert Voltage.compatible(Voltage)
    assert not Voltage.compatible(Mass)


def test_div_ohm_law():
    # V / R → I
    result = Voltage.div(Resistance)
    assert result.compatible(Current)
