"""
Deterministic Field IR simulator (rank-N).

Uses plain Python lists — no NumPy required — so the semantic model stays obvious.
Layout is contiguous row-major; multi-index access follows the formal shape contract.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..diagnostics import QuackError
from ..fields import Field
from ..ir.nodes import (
    IRAssign,
    IRBinary,
    IRBroadcast,
    IRConstant,
    IRDuckConstruct,
    IRExpr,
    IRFieldConstruct,
    IRIndex,
    IRModule,
    IRPrint,
    IRRef,
    IRUnary,
)
from ..shape import is_scalar, offset
from ..types import ElementType, FieldType
from ..units import Dimensionless


class Simulator:
    def __init__(self) -> None:
        self.env: Dict[str, Field] = {}
        self.outputs: List[str] = []

    def run(self, module: IRModule) -> Dict[str, Field]:
        self.env.clear()
        self.outputs.clear()
        for stmt in module.statements:
            self._stmt(stmt)
        return dict(self.env)

    def _stmt(self, stmt) -> None:
        if isinstance(stmt, IRAssign):
            value = self._eval(stmt.value)
            value.field_type = stmt.field_type
            self.env[stmt.name] = value
        elif isinstance(stmt, IRPrint):
            value = self._eval(stmt.value)
            self.outputs.append(str(value))
        else:
            raise QuackError(f"unsupported IR statement {type(stmt).__name__}")

    def _eval(self, expr: IRExpr) -> Field:
        if isinstance(expr, IRConstant):
            return Field.scalar(
                expr.value,
                element=expr.field_type.element,
                unit=expr.field_type.unit,
            )
        if isinstance(expr, IRRef):
            if expr.name not in self.env:
                raise QuackError(f"undefined name '{expr.name}' at runtime")
            return self.env[expr.name]
        if isinstance(expr, IRFieldConstruct):
            flat: List[Any] = []
            for e in expr.elements:
                f = self._eval(e)
                if is_scalar(f.shape):
                    flat.append(f.data[0])
                else:
                    flat.extend(f.data)
            if len(flat) != expr.field_type.size:
                raise QuackError(
                    f"runtime construct size mismatch: got {len(flat)}, "
                    f"expected {expr.field_type.size} for shape {expr.shape}"
                )
            return Field.from_values(
                flat,
                expr.shape,
                element=expr.field_type.element,
                unit=expr.field_type.unit,
            )
        if isinstance(expr, IRBroadcast):
            src = self._eval(expr.value)
            if not is_scalar(src.shape):
                raise QuackError(
                    f"runtime broadcast requires scalar, got shape {src.shape}"
                )
            v = src.data[0]
            return Field.from_values(
                [v] * expr.size,
                (expr.size,),
                element=expr.field_type.element,
                unit=expr.field_type.unit,
            )
        if isinstance(expr, IRBinary):
            left = self._eval(expr.left)
            right = self._eval(expr.right)
            return self._bin_op(expr.op, left, right, expr.field_type)
        if isinstance(expr, IRUnary):
            operand = self._eval(expr.operand)
            if expr.op == "-":
                data = [-x for x in operand.data]
                return Field(data, expr.field_type, operand.topology)
            raise QuackError(f"unsupported unary op {expr.op}")
        if isinstance(expr, IRIndex):
            return self._index(expr)
        if isinstance(expr, IRDuckConstruct):
            inner = self._eval(expr.value)
            return Field.scalar(
                inner.data[0], element=ElementType.DUCK, unit=Dimensionless
            )
        raise QuackError(f"unsupported IR expr {type(expr).__name__}")

    def _index(self, expr: IRIndex) -> Field:
        target = self._eval(expr.target)
        coords: List[int] = []
        for ix_expr in expr.indices:
            ix_f = self._eval(ix_expr)
            if not is_scalar(ix_f.shape):
                raise QuackError("runtime index coordinate must be scalar")
            coords.append(int(ix_f.data[0]))

        if len(coords) == 1:
            val = target.get(coords[0])
        else:
            if len(coords) != target.rank:
                raise QuackError(
                    f"runtime index rank {len(coords)} != field rank {target.rank}"
                )
            val = target.get_at(*coords)
        return Field.scalar(
            val, element=expr.field_type.element, unit=expr.field_type.unit
        )

    def _bin_op(
        self, op: str, left: Field, right: Field, result_type: FieldType
    ) -> Field:
        if left.shape != right.shape:
            raise QuackError(
                f"runtime shape mismatch: {left.shape} vs {right.shape}"
            )
        if len(left.data) != len(right.data):
            raise QuackError(
                f"runtime storage length mismatch: {len(left.data)} vs {len(right.data)}"
            )
        out: List[Any] = []
        for a, b in zip(left.data, right.data):
            if op == "+":
                out.append(a + b)
            elif op == "-":
                out.append(a - b)
            elif op == "*":
                out.append(a * b)
            elif op == "/":
                out.append(a / b)
            else:
                raise QuackError(f"unsupported op {op}")
        return Field(out, result_type)
