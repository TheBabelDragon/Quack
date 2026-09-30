"""Pretty-printer for Field IR."""

from __future__ import annotations

from .nodes import (
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


def print_ir(module: IRModule) -> str:
    lines: list[str] = ["module {"]
    for stmt in module.statements:
        lines.append("  " + _stmt(stmt))
    lines.append("}")
    return "\n".join(lines)


def _stmt(stmt) -> str:
    if isinstance(stmt, IRAssign):
        return f"{stmt.name} : {stmt.field_type} = {_expr(stmt.value)}"
    if isinstance(stmt, IRPrint):
        return f"print {_expr(stmt.value)}"
    return f"<? {type(stmt).__name__}>"


def _expr(e: IRExpr) -> str:
    if isinstance(e, IRConstant):
        return repr(e.value)
    if isinstance(e, IRRef):
        return e.name
    if isinstance(e, IRFieldConstruct):
        elems = ", ".join(_expr(x) for x in e.elements)
        shape = "x".join(str(d) for d in e.shape) if e.shape else "scalar"
        return f"field[{shape}]({elems})"
    if isinstance(e, IRBroadcast):
        return f"broadcast({_expr(e.value)}, {e.size})"
    if isinstance(e, IRBinary):
        return f"({_expr(e.left)} {e.op} {_expr(e.right)})"
    if isinstance(e, IRUnary):
        return f"({e.op}{_expr(e.operand)})"
    if isinstance(e, IRIndex):
        return f"{_expr(e.target)}[{_expr(e.index)}]"
    if isinstance(e, IRDuckConstruct):
        return f"duck_field({_expr(e.value)})"
    return f"<?{type(e).__name__}>"
