"""Recursive-descent parser for Quack v0.1."""

from __future__ import annotations

from typing import List, Optional

from .ast import (
    Assign,
    BinaryOp,
    Broadcast,
    DuckField,
    Expr,
    FieldConstruct,
    FloatLiteral,
    Index,
    IntLiteral,
    Name,
    PrintStmt,
    Program,
    Stmt,
    UnaryMinus,
)
from .diagnostics import QuackError, SourceLocation
from .lexer import Lexer, Token, TokenKind


class Parser:
    def __init__(self, tokens: List[Token], filename: Optional[str] = None) -> None:
        self.tokens = tokens
        self.filename = filename
        self.i = 0

    @classmethod
    def parse_source(cls, source: str, filename: Optional[str] = None) -> Program:
        tokens = Lexer(source, filename).tokens()
        return cls(tokens, filename).parse_program()

    def _cur(self) -> Token:
        return self.tokens[self.i]

    def _at(self, kind: TokenKind) -> bool:
        return self._cur().kind is kind

    def _eat(self, kind: TokenKind) -> Token:
        tok = self._cur()
        if tok.kind is not kind:
            raise QuackError(
                f"expected {kind.name}, got {tok.kind.name} ({tok.text!r})",
                SourceLocation(tok.line, tok.column, self.filename),
            )
        self.i += 1
        return tok

    def _match(self, kind: TokenKind) -> bool:
        if self._at(kind):
            self.i += 1
            return True
        return False

    def _skip_newlines(self) -> None:
        while self._match(TokenKind.NEWLINE):
            pass

    def parse_program(self) -> Program:
        stmts: List[Stmt] = []
        self._skip_newlines()
        while not self._at(TokenKind.EOF):
            stmts.append(self.parse_statement())
            self._skip_newlines()
        return Program(stmts)

    def parse_statement(self) -> Stmt:
        tok = self._cur()
        if tok.kind is TokenKind.IDENT and tok.text == "print":
            return self._parse_print()
        if tok.kind is TokenKind.IDENT:
            name_tok = self._eat(TokenKind.IDENT)
            unit_ann: Optional[str] = None
            if self._match(TokenKind.COLON):
                unit_tok = self._eat(TokenKind.IDENT)
                unit_ann = unit_tok.text
            self._eat(TokenKind.ASSIGN)
            expr = self.parse_expr()
            return Assign(
                name_tok.text,
                expr,
                unit_ann,
                location=SourceLocation(name_tok.line, name_tok.column, self.filename),
            )
        raise QuackError(
            f"expected statement, got {tok.kind.name}",
            SourceLocation(tok.line, tok.column, self.filename),
        )

    def _parse_print(self) -> PrintStmt:
        tok = self._eat(TokenKind.IDENT)
        self._eat(TokenKind.LPAREN)
        expr = self.parse_expr()
        self._eat(TokenKind.RPAREN)
        return PrintStmt(expr, location=SourceLocation(tok.line, tok.column, self.filename))

    def parse_expr(self) -> Expr:
        return self._parse_add()

    def _parse_add(self) -> Expr:
        left = self._parse_mul()
        while self._at(TokenKind.PLUS) or self._at(TokenKind.MINUS):
            op_tok = self._cur()
            self.i += 1
            right = self._parse_mul()
            left = BinaryOp(
                op_tok.text,
                left,
                right,
                location=SourceLocation(op_tok.line, op_tok.column, self.filename),
            )
        return left

    def _parse_mul(self) -> Expr:
        left = self._parse_unary()
        while self._at(TokenKind.STAR) or self._at(TokenKind.SLASH):
            op_tok = self._cur()
            self.i += 1
            right = self._parse_unary()
            left = BinaryOp(
                op_tok.text,
                left,
                right,
                location=SourceLocation(op_tok.line, op_tok.column, self.filename),
            )
        return left

    def _parse_unary(self) -> Expr:
        if self._at(TokenKind.MINUS):
            tok = self._eat(TokenKind.MINUS)
            operand = self._parse_unary()
            return UnaryMinus(
                operand,
                location=SourceLocation(tok.line, tok.column, self.filename),
            )
        return self._parse_postfix()

    def _parse_postfix(self) -> Expr:
        expr = self._parse_primary()
        while self._at(TokenKind.LBRACK):
            tok = self._eat(TokenKind.LBRACK)
            index = self.parse_expr()
            self._eat(TokenKind.RBRACK)
            expr = Index(
                expr,
                index,
                location=SourceLocation(tok.line, tok.column, self.filename),
            )
        return expr

    def _parse_primary(self) -> Expr:
        tok = self._cur()
        if tok.kind is TokenKind.INT:
            self.i += 1
            return IntLiteral(tok.value, location=SourceLocation(tok.line, tok.column, self.filename))  # type: ignore[arg-type]
        if tok.kind is TokenKind.FLOAT:
            self.i += 1
            return FloatLiteral(tok.value, location=SourceLocation(tok.line, tok.column, self.filename))  # type: ignore[arg-type]
        if tok.kind is TokenKind.IDENT:
            name = tok.text
            if name == "field":
                return self._parse_field_construct()
            if name == "broadcast":
                return self._parse_broadcast()
            if name == "duck_field":
                return self._parse_duck_field()
            self.i += 1
            return Name(name, location=SourceLocation(tok.line, tok.column, self.filename))
        if tok.kind is TokenKind.LPAREN:
            self.i += 1
            expr = self.parse_expr()
            self._eat(TokenKind.RPAREN)
            return expr
        raise QuackError(
            f"unexpected token {tok.kind.name} ({tok.text!r})",
            SourceLocation(tok.line, tok.column, self.filename),
        )

    def _parse_field_construct(self) -> FieldConstruct:
        tok = self._eat(TokenKind.IDENT)
        self._eat(TokenKind.LBRACK)
        dims: List[int] = []
        dim_tok = self._eat(TokenKind.INT)
        dims.append(int(dim_tok.value))  # type: ignore[arg-type]
        while self._match(TokenKind.COMMA):
            dim_tok = self._eat(TokenKind.INT)
            dims.append(int(dim_tok.value))  # type: ignore[arg-type]
        self._eat(TokenKind.RBRACK)
        self._eat(TokenKind.LPAREN)
        elements: List[Expr] = []
        if not self._at(TokenKind.RPAREN):
            elements.append(self.parse_expr())
            while self._match(TokenKind.COMMA):
                elements.append(self.parse_expr())
        self._eat(TokenKind.RPAREN)
        return FieldConstruct(
            dims,
            elements,
            location=SourceLocation(tok.line, tok.column, self.filename),
        )

    def _parse_broadcast(self) -> Broadcast:
        tok = self._eat(TokenKind.IDENT)
        self._eat(TokenKind.LPAREN)
        value = self.parse_expr()
        self._eat(TokenKind.COMMA)
        size_tok = self._eat(TokenKind.INT)
        self._eat(TokenKind.RPAREN)
        return Broadcast(
            value,
            int(size_tok.value),  # type: ignore[arg-type]
            location=SourceLocation(tok.line, tok.column, self.filename),
        )

    def _parse_duck_field(self) -> DuckField:
        tok = self._eat(TokenKind.IDENT)
        self._eat(TokenKind.LPAREN)
        value = self.parse_expr()
        self._eat(TokenKind.RPAREN)
        return DuckField(
            value,
            location=SourceLocation(tok.line, tok.column, self.filename),
        )
