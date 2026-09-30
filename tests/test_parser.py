"""Parser tests."""

from quack.ast import Assign, BinaryOp, Broadcast, FieldConstruct, IntLiteral, Program
from quack.parser import Parser


def test_assign_scalar():
    prog = Parser.parse_source("x := 4")
    assert isinstance(prog, Program)
    assert len(prog.statements) == 1
    stmt = prog.statements[0]
    assert isinstance(stmt, Assign)
    assert stmt.name == "x"
    assert isinstance(stmt.expr, IntLiteral)
    assert stmt.expr.value == 4


def test_field_construct():
    prog = Parser.parse_source("y := field[4](1, 2, 3, 4)")
    stmt = prog.statements[0]
    assert isinstance(stmt.expr, FieldConstruct)
    assert stmt.expr.dims == [4]
    assert len(stmt.expr.elements) == 4


def test_broadcast():
    prog = Parser.parse_source("z := broadcast(x, 4)")
    stmt = prog.statements[0]
    assert isinstance(stmt.expr, Broadcast)
    assert stmt.expr.size == 4


def test_arithmetic():
    prog = Parser.parse_source("r := y + z")
    stmt = prog.statements[0]
    assert isinstance(stmt.expr, BinaryOp)
    assert stmt.expr.op == "+"


def test_unit_annotation():
    prog = Parser.parse_source("v : Voltage := 12")
    stmt = prog.statements[0]
    assert stmt.unit_annotation == "Voltage"
