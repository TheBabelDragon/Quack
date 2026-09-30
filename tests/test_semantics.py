"""Semantic analysis, IR, and simulation tests."""

import pytest

from quack.backends.simulator import Simulator
from quack.ir.printer import print_ir
from quack.parser import Parser
from quack.semantic import analyze
from quack.types import ElementType


def _pipeline(source: str):
    program = Parser.parse_source(source)
    module, diags = analyze(program)
    return module, diags


def test_scalar_as_field():
    module, diags = _pipeline("x := 4")
    assert not diags.has_errors()
    assert module.statements[0].field_type.shape == ()
    assert module.statements[0].field_type.element is ElementType.INT


def test_field_construction_shape():
    module, diags = _pipeline("y := field[4](1, 2, 3, 4)")
    assert not diags.has_errors()
    assert module.statements[0].field_type.shape == (4,)


def test_field_element_count_mismatch():
    module, diags = _pipeline("y := field[4](1, 2)")
    assert diags.has_errors()
    assert any("expects 4" in d.message for d in diags)


def test_explicit_broadcast():
    module, diags = _pipeline("x := 4\nz := broadcast(x, 4)")
    assert not diags.has_errors()
    z = module.statements[1]
    assert z.field_type.shape == (4,)


def test_silent_broadcast_rejected():
    module, diags = _pipeline(
        "y := field[4](1, 2, 3, 4)\nx := 4\nr := y + x"
    )
    assert diags.has_errors()
    assert any("broadcast" in d.message.lower() for d in diags)


def test_unit_compatible():
    module, diags = _pipeline(
        "v : Voltage := 12\nr : Resistance := 4\ni := v / r"
    )
    assert not diags.has_errors()
    i = module.statements[2]
    assert i.field_type.unit.name == "Current"


def test_unit_incompatible():
    module, diags = _pipeline(
        "v : Voltage := 12\nm : Mass := 1\nbad := v + m"
    )
    assert diags.has_errors()
    assert any("incompatible units" in d.message for d in diags)


def test_index_bounds_static():
    module, diags = _pipeline("y := field[2](1, 2)\ne := y[5]")
    assert diags.has_errors()
    assert any("out of range" in d.message for d in diags)


def test_ir_generation():
    module, diags = _pipeline("x := 4\ny := field[2](1, 2)\nz := broadcast(x, 2)\nr := y + z")
    assert not diags.has_errors()
    text = print_ir(module)
    assert "broadcast" in text
    assert "field" in text


def test_deterministic_simulation():
    module, diags = _pipeline(
        "x := 4\ny := field[4](1, 2, 3, 4)\nz := broadcast(x, 4)\nresult := y + z"
    )
    assert not diags.has_errors()
    sim = Simulator()
    env = sim.run(module)
    assert env["result"].data == [5, 6, 7, 8]


def test_duck_field_execution():
    module, diags = _pipeline("duck := duck_field(1)")
    assert not diags.has_errors()
    sim = Simulator()
    env = sim.run(module)
    assert env["duck"].element is ElementType.DUCK
    assert env["duck"].data == [1]


def test_integration_pipeline():
    source = """
    x := 4
    y := field[4](1, 2, 3, 4)
    z := broadcast(x, 4)
    result := y + z
    print(result)
    """
    program = Parser.parse_source(source)
    module, diags = analyze(program)
    assert not diags.has_errors()
    sim = Simulator()
    sim.run(module)
    assert len(sim.outputs) == 1
    assert "5" in sim.outputs[0]
