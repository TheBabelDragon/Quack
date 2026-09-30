"""
Semantic analysis: AST → Field IR.

- Scalars become one-element fields (shape ())
- Explicit broadcasting only
- Unit compatibility checking
- Shape validation where static
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from . import ast as A
from .diagnostics import DiagnosticCollector, QuackError, SourceLocation
from .ir.nodes import (
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
from .types import ElementType, FieldType
from .units import Dimensionless, Unit, lookup_unit


class SemanticAnalyzer:
    def __init__(self, filename: Optional[str] = None) -> None:
        self.filename = filename
        self.diagnostics = DiagnosticCollector()
        self.env: Dict[str, FieldType] = {}

    def analyze(self, program: A.Program) -> IRModule:
        stmts = []
        for stmt in program.statements:
            ir_stmt = self._stmt(stmt)
            if ir_stmt is not None:
                stmts.append(ir_stmt)
        return IRModule(stmts)

    def _stmt(self, stmt: A.Stmt):
        if isinstance(stmt, A.Assign):
            return self._assign(stmt)
        if isinstance(stmt, A.PrintStmt):
            value = self._expr(stmt.expr)
            return IRPrint(value, location=stmt.location)
        self.diagnostics.error(f"unsupported statement {type(stmt).__name__}", stmt.location)
        return None

    def _assign(self, stmt: A.Assign) -> IRAssign:
        value = self._expr(stmt.expr)
        ft = value.field_type
        if stmt.unit_annotation:
            try:
                unit = lookup_unit(stmt.unit_annotation)
            except KeyError:
                self.diagnostics.error(
                    f"unknown unit '{stmt.unit_annotation}'",
                    stmt.location,
                )
                unit = Dimensionless
            if ft.unit is Dimensionless or ft.unit.compatible(unit):
                ft = ft.with_unit(unit)
                value = self._retag(value, ft)
            else:
                self.diagnostics.error(
                    f"cannot annotate expression of unit {ft.unit.name} as {unit.name}",
                    stmt.location,
                )
        self.env[stmt.name] = ft
        return IRAssign(stmt.name, value, ft, location=stmt.location)

    def _retag(self, expr: IRExpr, ft: FieldType) -> IRExpr:
        expr.field_type = ft
        return expr

    def _expr(self, expr: A.Expr) -> IRExpr:
        if isinstance(expr, A.IntLiteral):
            ft = FieldType(ElementType.INT, (), Dimensionless)
            return IRConstant(expr.value, field_type=ft, location=expr.location)
        if isinstance(expr, A.FloatLiteral):
            ft = FieldType(ElementType.FLOAT, (), Dimensionless)
            return IRConstant(expr.value, field_type=ft, location=expr.location)
        if isinstance(expr, A.Name):
            if expr.name not in self.env:
                self.diagnostics.error(f"undefined name '{expr.name}'", expr.location)
                ft = FieldType(ElementType.INT, (), Dimensionless)
            else:
                ft = self.env[expr.name]
            return IRRef(expr.name, field_type=ft, location=expr.location)
        if isinstance(expr, A.UnaryMinus):
            operand = self._expr(expr.operand)
            return IRUnary("-", operand, field_type=operand.field_type, location=expr.location)
        if isinstance(expr, A.BinaryOp):
            return self._binary(expr)
        if isinstance(expr, A.FieldConstruct):
            return self._field_construct(expr)
        if isinstance(expr, A.Broadcast):
            return self._broadcast(expr)
        if isinstance(expr, A.DuckField):
            return self._duck(expr)
        if isinstance(expr, A.Index):
            return self._index(expr)
        self.diagnostics.error(f"unsupported expression {type(expr).__name__}", expr.location)
        ft = FieldType(ElementType.INT, (), Dimensionless)
        return IRConstant(0, field_type=ft, location=expr.location)

    def _binary(self, expr: A.BinaryOp) -> IRBinary:
        left = self._expr(expr.left)
        right = self._expr(expr.right)
        lt, rt = left.field_type, right.field_type

        if lt.shape != rt.shape:
            self.diagnostics.error(
                f"shape mismatch in '{expr.op}': {lt.shape} vs {rt.shape}; "
                f"use explicit broadcast(...)",
                expr.location,
            )

        result_unit = Dimensionless
        if expr.op in ("+", "-"):
            if not lt.unit.compatible(rt.unit):
                self.diagnostics.error(
                    f"incompatible units in '{expr.op}': {lt.unit.name} vs {rt.unit.name}",
                    expr.location,
                )
            else:
                result_unit = lt.unit
        elif expr.op == "*":
            result_unit = lt.unit.mul(rt.unit)
        elif expr.op == "/":
            result_unit = lt.unit.div(rt.unit)

        element = lt.element
        if ElementType.FLOAT in (lt.element, rt.element):
            element = ElementType.FLOAT
        if ElementType.DUCK in (lt.element, rt.element) and expr.op in ("+", "-", "*", "/"):
            if lt.element is ElementType.DUCK or rt.element is ElementType.DUCK:
                if lt.element is not rt.element:
                    self.diagnostics.error(
                        f"cannot apply '{expr.op}' between {lt.element.value} and {rt.element.value}",
                        expr.location,
                    )

        result_type = FieldType(element, lt.shape, result_unit)
        return IRBinary(expr.op, left, right, field_type=result_type, location=expr.location)

    def _field_construct(self, expr: A.FieldConstruct) -> IRFieldConstruct:
        shape = tuple(expr.dims)
        expected = 1
        for d in shape:
            if d < 1:
                self.diagnostics.error(f"invalid dimension {d}", expr.location)
            expected *= d
        elements = [self._expr(e) for e in expr.elements]
        if len(elements) != expected:
            self.diagnostics.error(
                f"field[{','.join(map(str, shape))}] expects {expected} elements, got {len(elements)}",
                expr.location,
            )
        element = ElementType.INT
        unit = Dimensionless
        if elements:
            if any(e.field_type.element is ElementType.FLOAT for e in elements):
                element = ElementType.FLOAT
            unit = elements[0].field_type.unit
            for e in elements[1:]:
                if not e.field_type.unit.compatible(unit):
                    self.diagnostics.error(
                        f"mixed units in field constructor: {unit.name} vs {e.field_type.unit.name}",
                        expr.location,
                    )
        ft = FieldType(element, shape, unit)
        return IRFieldConstruct(elements, shape, field_type=ft, location=expr.location)

    def _broadcast(self, expr: A.Broadcast) -> IRBroadcast:
        value = self._expr(expr.value)
        if expr.size < 1:
            self.diagnostics.error(f"broadcast size must be >= 1, got {expr.size}", expr.location)
        src_shape = value.field_type.shape
        if src_shape not in ((), (1,)):
            self.diagnostics.error(
                f"broadcast requires a scalar field, got shape {src_shape}",
                expr.location,
            )
        new_shape = (expr.size,)
        ft = value.field_type.with_shape(new_shape)
        return IRBroadcast(value, expr.size, field_type=ft, location=expr.location)

    def _duck(self, expr: A.DuckField) -> IRDuckConstruct:
        value = self._expr(expr.value)
        ft = FieldType(ElementType.DUCK, (), Dimensionless)
        return IRDuckConstruct(value, field_type=ft, location=expr.location)

    def _index(self, expr: A.Index) -> IRIndex:
        target = self._expr(expr.target)
        index = self._expr(expr.index)
        if index.field_type.shape not in ((), (1,)):
            self.diagnostics.error("index must be a scalar", expr.location)
        if isinstance(index, IRConstant) and isinstance(index.value, int):
            size = target.field_type.size if target.field_type.shape != () else 1
            if index.value < 0 or index.value >= size:
                self.diagnostics.error(
                    f"index {index.value} out of range for shape {target.field_type.shape}",
                    expr.location,
                )
        ft = FieldType(target.field_type.element, (), target.field_type.unit)
        return IRIndex(target, index, field_type=ft, location=expr.location)


def analyze(program: A.Program, filename: Optional[str] = None) -> Tuple[IRModule, DiagnosticCollector]:
    analyzer = SemanticAnalyzer(filename)
    module = analyzer.analyze(program)
    return module, analyzer.diagnostics
