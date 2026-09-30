"""
Field IR — independent of parser AST.

Shapes, units, and operations are explicit. Suitable for simulation
and future tensor/dataflow/FPGA lowering without redesigning the language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

from ..diagnostics import SourceLocation
from ..types import ElementType, FieldType
from ..units import Unit, Dimensionless


@dataclass
class IRNode:
    location: Optional[SourceLocation] = field(default=None, kw_only=True)


@dataclass
class IRModule(IRNode):
    statements: List["IRStmt"]


@dataclass
class IRStmt(IRNode):
    pass


@dataclass
class IRAssign(IRStmt):
    name: str
    value: "IRExpr"
    field_type: FieldType


@dataclass
class IRPrint(IRStmt):
    value: "IRExpr"


@dataclass
class IRExpr(IRNode):
    field_type: FieldType = field(kw_only=True)


@dataclass
class IRConstant(IRExpr):
    value: Any


@dataclass
class IRFieldConstruct(IRExpr):
    elements: List[IRExpr]
    shape: Tuple[int, ...]


@dataclass
class IRRef(IRExpr):
    name: str


@dataclass
class IRBinary(IRExpr):
    op: str
    left: IRExpr
    right: IRExpr


@dataclass
class IRBroadcast(IRExpr):
    value: IRExpr
    size: int


@dataclass
class IRIndex(IRExpr):
    target: IRExpr
    index: IRExpr


@dataclass
class IRUnary(IRExpr):
    op: str
    operand: IRExpr


@dataclass
class IRDuckConstruct(IRExpr):
    value: IRExpr
