"""Lexer for Quack v0.1."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator, List, Optional

from .diagnostics import QuackError, SourceLocation


class TokenKind(Enum):
    IDENT = auto()
    INT = auto()
    FLOAT = auto()
    STRING = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    ASSIGN = auto()
    COLON = auto()
    COMMA = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACK = auto()
    RBRACK = auto()

    NEWLINE = auto()
    EOF = auto()


@dataclass
class Token:
    kind: TokenKind
    text: str
    line: int
    column: int
    value: object = None

    @property
    def location(self) -> SourceLocation:
        return SourceLocation(self.line, self.column)


KEYWORDS = {
    "field": "field",
    "broadcast": "broadcast",
    "print": "print",
    "duck_field": "duck_field",
}


class Lexer:
    def __init__(self, source: str, filename: Optional[str] = None) -> None:
        self.source = source
        self.filename = filename
        self.i = 0
        self.line = 1
        self.col = 1

    def _peek(self) -> str:
        if self.i >= len(self.source):
            return "\0"
        return self.source[self.i]

    def _advance(self) -> str:
        ch = self._peek()
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def tokens(self) -> List[Token]:
        out: List[Token] = []
        while True:
            tok = self._next()
            out.append(tok)
            if tok.kind is TokenKind.EOF:
                break
        return out

    def _next(self) -> Token:
        while True:
            ch = self._peek()
            if ch == "\0":
                return Token(TokenKind.EOF, "", self.line, self.col)
            if ch in " \t\r":
                self._advance()
                continue
            if ch == "#":
                while self._peek() not in ("\n", "\0"):
                    self._advance()
                continue
            break

        line, col = self.line, self.col
        ch = self._peek()

        if ch == "\n":
            self._advance()
            return Token(TokenKind.NEWLINE, "\n", line, col)

        if ch.isalpha() or ch == "_":
            return self._ident(line, col)

        if ch.isdigit() or (ch == "." and self.i + 1 < len(self.source) and self.source[self.i + 1].isdigit()):
            return self._number(line, col)

        if ch == ":" and self.i + 1 < len(self.source) and self.source[self.i + 1] == "=":
            self._advance()
            self._advance()
            return Token(TokenKind.ASSIGN, ":=", line, col)

        singles = {
            "+": TokenKind.PLUS,
            "-": TokenKind.MINUS,
            "*": TokenKind.STAR,
            "/": TokenKind.SLASH,
            ":": TokenKind.COLON,
            ",": TokenKind.COMMA,
            "(": TokenKind.LPAREN,
            ")": TokenKind.RPAREN,
            "[": TokenKind.LBRACK,
            "]": TokenKind.RBRACK,
        }
        if ch in singles:
            self._advance()
            return Token(singles[ch], ch, line, col)

        raise QuackError(f"unexpected character {ch!r}", SourceLocation(line, col, self.filename))

    def _ident(self, line: int, col: int) -> Token:
        start = self.i
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[start : self.i]
        return Token(TokenKind.IDENT, text, line, col, text)

    def _number(self, line: int, col: int) -> Token:
        start = self.i
        is_float = False
        while self._peek().isdigit():
            self._advance()
        if self._peek() == ".":
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[start : self.i]
        if is_float:
            return Token(TokenKind.FLOAT, text, line, col, float(text))
        return Token(TokenKind.INT, text, line, col, int(text))
