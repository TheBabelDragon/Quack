"""Rank-N fields: construction, indexing, arithmetic, topology, IR, simulation."""

import pytest

from quack.backends.simulator import Simulator
from quack.fields import Field
from quack.parser import Parser
from quack.semantic import analyze
from quack.topology import Grid2D, Grid3D, Linear, Point, topology_for_shape, validate_topology
from quack.types import ElementType, FieldType
from quack.units import Dimensionless, Voltage


def _run(src: str):
    prog = Parser.parse_source(src)
    mod, diags = analyze(prog)
    assert not diags.has_errors(), [str(e) for e in diags.items]
    sim = Simulator()
    env = sim.run(mod)
    return env, sim.outputs, mod


def test_matrix_construction():
    env, outs, _ = _run("""
m := field[2,3](10, 20, 30, 40, 50, 60)
print(m)
""")
    m = env["m"]
    assert m.shape == (2, 3)
    assert m.size == 6
    assert m.data == [10, 20, 30, 40, 50, 60]
    assert m.strides == (3, 1)
    assert m.topology.name == "grid2d"


def test_matrix_multi_index():
    env, outs, _ = _run("""
m := field[2,3](1, 2, 3, 4, 5, 6)
a := m[0, 0]
b := m[0, 2]
c := m[1, 1]
d := m[1, 2]
print(a)
print(b)
print(c)
print(d)
""")
    assert env["a"].data[0] == 1
    assert env["b"].data[0] == 3
    assert env["c"].data[0] == 5
    assert env["d"].data[0] == 6


def test_matrix_linear_index():
    env, outs, _ = _run("""
m := field[2,3](1, 2, 3, 4, 5, 6)
print(m[0])
print(m[5])
print(m[3])
""")
    assert outs[0].startswith("Field(1")
    assert outs[1].startswith("Field(6")
    assert outs[2].startswith("Field(4")


def test_rank3_construction_and_index():
    env, outs, _ = _run("""
t := field[2,2,2](1,2,3,4,5,6,7,8)
print(t[1,1,1])
print(t[0,1,0])
print(t[7])
""")
    assert env["t"].shape == (2, 2, 2)
    assert env["t"].size == 8
    assert env["t"].strides == (4, 2, 1)
    assert outs[0].startswith("Field(8")
    assert outs[1].startswith("Field(3")
    assert outs[2].startswith("Field(8")


def test_matrix_arithmetic_same_shape():
    env, outs, _ = _run("""
a := field[2,2](1, 2, 3, 4)
b := field[2,2](10, 20, 30, 40)
c := a + b
print(c)
""")
    assert env["c"].shape == (2, 2)
    assert env["c"].data == [11, 22, 33, 44]


def test_shape_mismatch_rejected():
    prog = Parser.parse_source("""
a := field[2,2](1, 2, 3, 4)
b := field[3](1, 2, 3)
c := a + b
""")
    mod, diags = analyze(prog)
    assert diags.has_errors()
    msgs = " ".join(str(e) for e in diags.items)
    assert "shape mismatch" in msgs


def test_element_count_mismatch():
    prog = Parser.parse_source("m := field[2,3](1, 2, 3)")
    mod, diags = analyze(prog)
    assert diags.has_errors()
    msgs = " ".join(str(e) for e in diags.items)
    assert "expects 6" in msgs


def test_invalid_dimension():
    prog = Parser.parse_source("m := field[0]()")
    mod, diags = analyze(prog)
    assert diags.has_errors()
    msgs = " ".join(str(e) for e in diags.items)
    assert "invalid dimension" in msgs


def test_static_multi_index_oob():
    prog = Parser.parse_source("""
m := field[2,3](1,2,3,4,5,6)
x := m[2, 0]
""")
    mod, diags = analyze(prog)
    assert diags.has_errors()


def test_static_linear_oob():
    prog = Parser.parse_source("""
m := field[2,3](1,2,3,4,5,6)
x := m[6]
""")
    mod, diags = analyze(prog)
    assert diags.has_errors()


def test_index_rank_mismatch():
    prog = Parser.parse_source("""
m := field[2,3](1,2,3,4,5,6)
x := m[0, 1, 2]
""")
    mod, diags = analyze(prog)
    assert diags.has_errors()
    msgs = " ".join(str(e) for e in diags.items)
    assert "rank" in msgs.lower()


def test_scalar_vs_one_element_vector():
    ft_s = FieldType(ElementType.INT, ())
    ft_v = FieldType(ElementType.INT, (1,))
    assert ft_s.is_scalar
    assert not ft_v.is_scalar
    assert ft_s.size == 1
    assert ft_v.size == 1
    assert ft_s.rank == 0
    assert ft_v.rank == 1


def test_field_runtime_get_at():
    f = Field.from_values(list(range(6)), (2, 3))
    assert f.get_at(0, 0) == 0
    assert f.get_at(1, 2) == 5
    assert f.coords_of(5) == (1, 2)
    with pytest.raises(IndexError):
        f.get_at(2, 0)


def test_topology_inference():
    assert topology_for_shape(()).name == "point"
    assert topology_for_shape((5,)).name == "linear"
    assert topology_for_shape((2, 3)).name == "grid2d"
    assert topology_for_shape((2, 2, 2)).name == "grid3d"
    assert topology_for_shape((2, 2, 2, 2)).name == "grid4d"


def test_topology_validation():
    validate_topology(Point, ())
    validate_topology(Linear, (4,))
    validate_topology(Grid2D, (2, 3))
    with pytest.raises(ValueError):
        validate_topology(Grid2D, (4,))
    with pytest.raises(ValueError):
        validate_topology(Point, (1,))


def test_ir_preserves_shape():
    _, _, mod = _run("m := field[2,3](1,2,3,4,5,6)")
    assign = mod.statements[0]
    assert assign.field_type.shape == (2, 3)
    assert assign.field_type.size == 6


def test_unit_on_matrix():
    env, _, _ = _run("""
m : Voltage := field[2,2](1.0, 2.0, 3.0, 4.0)
print(m)
""")
    assert env["m"].unit.name == "Voltage"
    assert env["m"].shape == (2, 2)


def test_broadcast_still_scalar_only():
    prog = Parser.parse_source("""
v := field[1](7)
b := broadcast(v, 3)
""")
    mod, diags = analyze(prog)
    assert diags.has_errors()
    msgs = " ".join(str(e) for e in diags.items)
    assert "scalar" in msgs.lower()


def test_deterministic_rank_n_sim():
    src = """
m := field[2,2](1, 2, 3, 4)
n := field[2,2](1, 1, 1, 1)
r := m * n
print(r[1, 1])
"""
    env1, outs1, _ = _run(src)
    env2, outs2, _ = _run(src)
    assert outs1 == outs2
    assert env1["r"].data == env2["r"].data == [1, 2, 3, 4]


def test_existing_vector_compat():
    env, outs, _ = _run("""
y := field[4](1, 2, 3, 4)
z := broadcast(4, 4)
r := y + z
print(r)
print(y[2])
""")
    assert env["r"].data == [5, 6, 7, 8]
    assert outs[1].startswith("Field(3")
