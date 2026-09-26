"""Safe predicate evaluator for wiki event ``triggers``.

A tiny recursive-descent parser — ``eval()`` is never used. Supports:

* dotted state paths (e.g. ``population.unrest``, ``resources.food_stock``)
* comparison operators: ``> < >= <= == !=``
* arithmetic: ``+ - * /`` and parentheses, with unary minus
* boolean logic: ``and``, ``or``, ``not``

Anything unsafe or malformed (unknown paths, type mismatches, division by
zero, syntax errors) evaluates to ``False`` instead of raising.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Union

from api.models import Game

_TOKEN_RE = re.compile(
    r"""
    (?P<num>\d+(?:\.\d+)?)
    | (?P<ident>[A-Za-z_][A-Za-z0-9_.]*)
    | (?P<op>>=|<=|==|!=|>|<|\+|-|\*|/|\(|\))
    | (?P<ws>\s+)
    | (?P<bad>.)
    """,
    re.VERBOSE,
)

_KEYWORDS = {"and", "or", "not"}
_COMP_OPS = {">", "<", ">=", "<=", "==", "!="}


@dataclass
class _Token:
    kind: str  # "num" | "ident" | "op" | "kw"
    text: str


class _EvalError(Exception):
    """Internal: any evaluation problem collapses to False."""


def _tokenize(expr: str) -> list[_Token]:
    tokens: list[_Token] = []
    for m in _TOKEN_RE.finditer(expr):
        kind = m.lastgroup
        text = m.group()
        if kind == "ws":
            continue
        if kind == "bad":
            raise _EvalError(f"bad character: {text!r}")
        if kind == "ident" and text in _KEYWORDS:
            kind = "kw"
        tokens.append(_Token(kind, text))
    return tokens


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class _Parser:
    def __init__(self, tokens: list[_Token], context: Mapping[str, Any]):
        self.tokens = tokens
        self.context = context
        self.pos = 0

    # -- plumbing ---------------------------------------------------------
    def peek(self) -> Union[_Token, None]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def next(self) -> _Token:
        tok = self.peek()
        if tok is None:
            raise _EvalError("unexpected end of expression")
        self.pos += 1
        return tok

    def expect_op(self, text: str) -> None:
        tok = self.next()
        if tok.kind != "op" or tok.text != text:
            raise _EvalError(f"expected {text!r}")

    # -- grammar ----------------------------------------------------------
    def parse(self) -> Any:
        if not self.tokens:
            raise _EvalError("empty expression")
        value = self.parse_or()
        if self.peek() is not None:
            raise _EvalError("trailing tokens")
        return value

    def parse_or(self) -> Any:
        left = self.parse_and()
        while (tok := self.peek()) and tok.kind == "kw" and tok.text == "or":
            self.next()
            right = self.parse_and()
            left = self._as_bool(left) or self._as_bool(right)
        return left

    def parse_and(self) -> Any:
        left = self.parse_not()
        while (tok := self.peek()) and tok.kind == "kw" and tok.text == "and":
            self.next()
            right = self.parse_not()
            left = self._as_bool(left) and self._as_bool(right)
        return left

    def parse_not(self) -> Any:
        tok = self.peek()
        if tok and tok.kind == "kw" and tok.text == "not":
            self.next()
            return not self._as_bool(self.parse_not())
        return self.parse_comparison()

    def parse_comparison(self) -> Any:
        left = self.parse_add()
        tok = self.peek()
        if tok and tok.kind == "op" and tok.text in _COMP_OPS:
            self.next()
            right = self.parse_add()
            if self.peek() and self.peek().kind == "op" and self.peek().text in _COMP_OPS:
                raise _EvalError("chained comparisons not supported")
            return self._compare(tok.text, left, right)
        return left

    def parse_add(self) -> Any:
        left = self.parse_mul()
        while (tok := self.peek()) and tok.kind == "op" and tok.text in ("+", "-"):
            self.next()
            right = self.parse_mul()
            left = self._arith(tok.text, left, right)
        return left

    def parse_mul(self) -> Any:
        left = self.parse_unary()
        while (tok := self.peek()) and tok.kind == "op" and tok.text in ("*", "/"):
            self.next()
            right = self.parse_unary()
            left = self._arith(tok.text, left, right)
        return left

    def parse_unary(self) -> Any:
        tok = self.peek()
        if tok and tok.kind == "op" and tok.text == "-":
            self.next()
            value = self.parse_unary()
            if not _is_number(value):
                raise _EvalError("unary minus on non-number")
            return -value
        return self.parse_primary()

    def parse_primary(self) -> Any:
        tok = self.next()
        if tok.kind == "num":
            return float(tok.text) if "." in tok.text else int(tok.text)
        if tok.kind == "op" and tok.text == "(":
            value = self.parse_or()
            self.expect_op(")")
            return value
        if tok.kind == "ident":
            return self._resolve(tok.text)
        raise _EvalError(f"unexpected token: {tok.text!r}")

    # -- evaluation helpers ------------------------------------------------
    def _resolve(self, path: str) -> Any:
        if path.startswith(".") or path.endswith(".") or ".." in path:
            raise _EvalError(f"bad path: {path!r}")
        node: Any = self.context
        for part in path.split("."):
            if not isinstance(node, Mapping) or part not in node:
                raise _EvalError(f"unknown path: {path!r}")
            node = node[part]
        return node

    @staticmethod
    def _as_bool(v: Any) -> bool:
        if isinstance(v, bool):
            return v
        raise _EvalError("logical operator on non-boolean")

    @staticmethod
    def _arith(op: str, left: Any, right: Any) -> Union[int, float]:
        if not _is_number(left) or not _is_number(right):
            raise _EvalError("arithmetic on non-numbers")
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if right == 0:
            raise _EvalError("division by zero")
        return left / right

    @staticmethod
    def _compare(op: str, left: Any, right: Any) -> bool:
        if not _is_number(left) or not _is_number(right):
            raise _EvalError("comparison on non-numbers")
        if op == ">":
            return left > right
        if op == "<":
            return left < right
        if op == ">=":
            return left >= right
        if op == "<=":
            return left <= right
        if op == "==":
            return left == right
        return left != right  # "!="


def evaluate_expr(expr: str, context: Mapping[str, Any]) -> bool:
    """Evaluate a trigger expression against a nested mapping context.

    Never raises: any malformed input evaluates to False.
    """
    try:
        parser = _Parser(_tokenize(expr), context)
        return bool(parser.parse())
    except _EvalError:
        return False
    except Exception:
        return False


def evaluate_trigger(game: Game, trigger: str) -> bool:
    """Evaluate a trigger string against a Game's state."""
    context = game.model_dump(mode="json")
    return evaluate_expr(trigger, context)
