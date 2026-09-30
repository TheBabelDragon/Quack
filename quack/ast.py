"""Parser AST for Quack — separate from Field IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union

from .diagnostics import SourceLocation


@dataclass
class Node:
    location: Optional[SourceLocation] = field(default=None, kw_only=True)


@dataclass
class Program(Node):
    statements: List["Stmt"]


@dataclass
class Stmt(Node):
    pass


@dataclass
class Assign(Stmt):
    name: str
    expr: "Expr"
    unit_annotation: Optional[str] = None


@dataclass
class PrintStmt(Stmt):
    expr: "Expr"


@dataclass
class Expr(Node):
    pass


@dataclass
class IntLiteral(Expr):
    value: int


@dataclass
class FloatLiteral(Expr):
    value: float


@dataclass
class Name(Expr):
    name: str


@dataclass
class BinaryOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class FieldConstruct(Expr):
    dims: List[int]
    elements: List[Expr]


@dataclass
class Broadcast(Expr):
    value: Expr
    size: int


@dataclass
class DuckField(Expr):
    value: Expr


@dataclass
class Index(Expr):
    target: Expr
    index: Expr


@dataclass
class UnaryMinus(Expr):
    operand: Expr
