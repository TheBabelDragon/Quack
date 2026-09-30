"""Lexer tests."""

from quack.lexer import Lexer, TokenKind


def test_identifiers_and_numbers():
    tokens = Lexer("x := 4\ny := 3.5").tokens()
    kinds = [t.kind for t in tokens if t.kind is not TokenKind.NEWLINE]
    assert TokenKind.IDENT in kinds
    assert TokenKind.ASSIGN in kinds
    assert TokenKind.INT in kinds
    assert TokenKind.FLOAT in kinds
    assert kinds[-1] is TokenKind.EOF


def test_operators():
    tokens = Lexer("a + b * c - d / e").tokens()
    texts = [t.text for t in tokens if t.kind is not TokenKind.EOF and t.kind is not TokenKind.NEWLINE]
    assert texts == ["a", "+", "b", "*", "c", "-", "d", "/", "e"]


def test_field_syntax_tokens():
    tokens = Lexer("field[4](1, 2, 3, 4)").tokens()
    texts = [t.text for t in tokens if t.kind is not TokenKind.EOF]
    assert "field" in texts
    assert "[" in texts
    assert "]" in texts


def test_comments_skipped():
    tokens = Lexer("# comment\nx := 1").tokens()
    assert any(t.text == "x" for t in tokens)
    assert not any("#" in t.text for t in tokens)
