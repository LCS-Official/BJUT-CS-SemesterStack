#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验三：语法制导的三地址代码生成器

支持的微型语言来自实验指导书：
  P -> L | L P
  L -> S ;
  S -> id = E | if C then S | if C then S else S | while C do S | { P }
  C -> E > E | E < E | E = E | E >= E | E <= E | E <> E
  E -> E + T | E - T | T
  T -> T * F | T / F | F
  F -> ( E ) | id | int8 | int10 | int16
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import argparse
import sys


KEYWORDS = {
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "while": "WHILE",
    "do": "DO",
}

SINGLE_CHAR_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    ">": "GT",
    "<": "LT",
    "=": "EQ",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ";": "SEMI",
}


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    value: str
    line: int
    col: int


class CompileError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while not self._eof():
            ch = self._peek()
            if ch in " \t\r\n":
                self._consume_whitespace()
            elif ch.isalpha():
                tokens.append(self._identifier_or_keyword())
            elif ch.isdigit():
                tokens.append(self._number())
            elif ch == "/" and self._peek(1) == "/":
                self._line_comment()
            elif ch == "/" and self._peek(1) == "*":
                self._block_comment()
            else:
                tokens.append(self._operator_or_delimiter())
        tokens.append(Token("EOF", "", "", self.line, self.col))
        return tokens

    def _identifier_or_keyword(self) -> Token:
        line, col = self.line, self.col
        start = self.pos
        self._advance()
        while not self._eof() and (self._peek().isalpha() or self._peek().isdigit()):
            self._advance()
        text = self.source[start:self.pos]
        kind = KEYWORDS.get(text, "ID")
        return Token(kind, text, text, line, col)

    def _number(self) -> Token:
        line, col = self.line, self.col
        start = self.pos
        if self._peek() == "0" and self._peek(1) in "xX":
            self._advance()
            self._advance()
            if self._eof() or not self._peek().lower() in "0123456789abcdef":
                raise CompileError(f"{line}:{col}: 十六进制整数缺少数字")
            while not self._eof() and self._peek().lower() in "0123456789abcdef":
                self._advance()
            text = self.source[start:self.pos]
            return Token("INT16", text, str(int(text, 16)), line, col)

        if self._peek() == "0":
            self._advance()
            while not self._eof() and self._peek().isdigit():
                if self._peek() not in "01234567":
                    raise CompileError(f"{self.line}:{self.col}: 八进制整数中出现非法数字 '{self._peek()}'")
                self._advance()
            text = self.source[start:self.pos]
            kind = "INT8" if len(text) > 1 else "INT10"
            return Token(kind, text, str(int(text, 8 if kind == "INT8" else 10)), line, col)

        while not self._eof() and self._peek().isdigit():
            self._advance()
        text = self.source[start:self.pos]
        return Token("INT10", text, text, line, col)

    def _operator_or_delimiter(self) -> Token:
        line, col = self.line, self.col
        ch = self._peek()
        pair = ch + self._peek(1)
        if pair in {">=", "<=", "<>"}:
            self._advance()
            self._advance()
            return Token({"<>": "NE", ">=": "GE", "<=": "LE"}[pair], pair, pair, line, col)
        if ch in SINGLE_CHAR_TOKENS:
            self._advance()
            return Token(SINGLE_CHAR_TOKENS[ch], ch, ch, line, col)
        raise CompileError(f"{line}:{col}: 无法识别的字符 '{ch}'")

    def _consume_whitespace(self) -> None:
        while not self._eof() and self._peek() in " \t\r\n":
            self._advance()

    def _line_comment(self) -> None:
        while not self._eof() and self._peek() != "\n":
            self._advance()

    def _block_comment(self) -> None:
        self._advance()
        self._advance()
        while not self._eof():
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        raise CompileError("块注释没有闭合")

    def _peek(self, offset: int = 0) -> str:
        index = self.pos + offset
        return "" if index >= len(self.source) else self.source[index]

    def _advance(self) -> None:
        if self._peek() == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1

    def _eof(self) -> bool:
        return self.pos >= len(self.source)


@dataclass
class Program:
    statements: list["Statement"]


class Statement:
    pass


@dataclass
class Assign(Statement):
    name: str
    expr: "Expr"


@dataclass
class If(Statement):
    cond: "Condition"
    then_stmt: Statement
    else_stmt: Statement | None


@dataclass
class While(Statement):
    cond: "Condition"
    body: Statement


@dataclass
class Block(Statement):
    statements: list[Statement]


class Expr:
    pass


@dataclass
class Var(Expr):
    name: str


@dataclass
class Const(Expr):
    value: str


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr


@dataclass
class Condition:
    op: str
    left: Expr
    right: Expr


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        statements = self._statement_list({"EOF"})
        self._expect("EOF")
        return Program(statements)

    def _statement_list(self, stops: set[str]) -> list[Statement]:
        statements: list[Statement] = []
        while self._current().kind not in stops:
            statements.append(self._statement())
            self._expect("SEMI")
        return statements

    def _statement(self) -> Statement:
        token = self._current()
        if token.kind == "ID":
            name = self._advance().value
            self._expect("EQ")
            return Assign(name, self._expr())
        if token.kind == "IF":
            self._advance()
            cond = self._condition()
            self._expect("THEN")
            then_stmt = self._statement()
            else_stmt = None
            if self._match("ELSE"):
                else_stmt = self._statement()
            return If(cond, then_stmt, else_stmt)
        if token.kind == "WHILE":
            self._advance()
            cond = self._condition()
            self._expect("DO")
            return While(cond, self._statement())
        if token.kind == "LBRACE":
            self._advance()
            statements = self._statement_list({"RBRACE"})
            self._expect("RBRACE")
            return Block(statements)
        raise self._error(f"期望语句，实际为 '{token.text or token.kind}'")

    def _condition(self) -> Condition:
        left = self._expr()
        token = self._current()
        ops = {
            "GT": ">",
            "LT": "<",
            "EQ": "=",
            "GE": ">=",
            "LE": "<=",
            "NE": "<>",
        }
        if token.kind not in ops:
            raise self._error("条件表达式缺少比较运算符")
        self._advance()
        return Condition(ops[token.kind], left, self._expr())

    def _expr(self) -> Expr:
        expr = self._term()
        while self._current().kind in {"PLUS", "MINUS"}:
            op = "+" if self._advance().kind == "PLUS" else "-"
            expr = BinOp(op, expr, self._term())
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._current().kind in {"MULTIPLY", "DIVIDE"}:
            op = "*" if self._advance().kind == "MULTIPLY" else "/"
            expr = BinOp(op, expr, self._factor())
        return expr

    def _factor(self) -> Expr:
        token = self._current()
        if token.kind == "LPAREN":
            self._advance()
            expr = self._expr()
            self._expect("RPAREN")
            return expr
        if token.kind == "ID":
            return Var(self._advance().value)
        if token.kind in {"INT8", "INT10", "INT16"}:
            return Const(self._advance().value)
        raise self._error(f"表达式因子非法：'{token.text or token.kind}'")

    def _match(self, kind: str) -> bool:
        if self._current().kind == kind:
            self._advance()
            return True
        return False

    def _expect(self, kind: str) -> Token:
        token = self._current()
        if token.kind != kind:
            raise self._error(f"期望 {kind}，实际为 '{token.text or token.kind}'")
        return self._advance()

    def _advance(self) -> Token:
        token = self._current()
        self.pos += 1
        return token

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _error(self, message: str) -> CompileError:
        token = self._current()
        return CompileError(f"{token.line}:{token.col}: {message}")


class CodeGenerator:
    def __init__(self):
        self.lines: list[str] = []
        self.temp_no = 1
        self.label_no = 0

    def generate(self, program: Program) -> list[str]:
        if not program.statements:
            return []
        self._sequence(program.statements, None)
        return self.lines

    def _sequence(self, statements: list[Statement], next_label: str | None) -> None:
        for index, statement in enumerate(statements):
            stmt_next = next_label if index == len(statements) - 1 else self._new_label()
            self._statement(statement, stmt_next)
            if index != len(statements) - 1:
                self._label(stmt_next)

    def _statement(self, statement: Statement, next_label: str | None, entry_label: str | None = None) -> None:
        if isinstance(statement, Assign):
            if entry_label is not None:
                self._label(entry_label)
            place = self._expr(statement.expr)
            self._emit(f"{statement.name} := {place}")
        elif isinstance(statement, While):
            begin_label = entry_label if entry_label is not None else self._new_label()
            true_label = self._new_label()
            false_label = next_label if next_label is not None else self._new_label()
            self._label(begin_label)
            self._condition(statement.cond, true_label, false_label)
            self._statement(statement.body, begin_label, true_label)
            self._emit(f"goto {begin_label}")
            if next_label is None:
                self._label(false_label)
        elif isinstance(statement, If):
            if entry_label is not None:
                self._label(entry_label)
            true_label = self._new_label()
            false_label = next_label if statement.else_stmt is None else self._new_label()
            if false_label is None:
                false_label = self._new_label()
            self._condition(statement.cond, true_label, false_label)
            self._statement(statement.then_stmt, next_label, true_label)
            if statement.else_stmt is not None:
                if next_label is not None:
                    self._emit(f"goto {next_label}")
                self._label(false_label)
                self._statement(statement.else_stmt, next_label)
            elif next_label is None:
                self._label(false_label)
        elif isinstance(statement, Block):
            if entry_label is not None:
                self._label(entry_label)
            self._sequence(statement.statements, next_label)
        else:
            raise TypeError(f"unsupported statement: {statement!r}")

    def _condition(self, condition: Condition, true_label: str, false_label: str) -> None:
        left = self._expr(condition.left)
        right = self._expr(condition.right)
        self._emit(f"if {left} {condition.op} {right} goto {true_label}")
        self._emit(f"goto {false_label}")

    def _expr(self, expr: Expr) -> str:
        if isinstance(expr, Var):
            return expr.name
        if isinstance(expr, Const):
            return expr.value
        if isinstance(expr, BinOp):
            left = self._expr(expr.left)
            right = self._expr(expr.right)
            temp = self._new_temp()
            self._emit(f"{temp} := {left} {expr.op} {right}")
            return temp
        raise TypeError(f"unsupported expression: {expr!r}")

    def _new_temp(self) -> str:
        temp = f"t{self.temp_no}"
        self.temp_no += 1
        return temp

    def _new_label(self) -> str:
        label = f"L{self.label_no}"
        self.label_no += 1
        return label

    def _label(self, label: str | None) -> None:
        if label is not None:
            self.lines.append(f"{label}:")

    def _emit(self, text: str) -> None:
        self.lines.append(f"    {text}")


def compile_source(source: str) -> list[str]:
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()
    return CodeGenerator().generate(program)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="实验三：语法制导三地址代码生成器")
    parser.add_argument("input", nargs="?", default="input.txt", help="源程序输入文件")
    parser.add_argument("output", nargs="?", default="output.txt", help="三地址码输出文件")
    parser.add_argument("--tokens", action="store_true", help="同时输出词法符号序列，便于调试")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    try:
        source = input_path.read_text(encoding="utf-8")
        code = compile_source(source)
        output_path.write_text("\n".join(code) + ("\n" if code else ""), encoding="utf-8")
        print("实验三：语法制导三地址代码生成器")
        print(f"输入文件: {input_path}")
        print(f"输出文件: {output_path}")
        print()
        if args.tokens:
            for token in Lexer(source).tokenize():
                if token.kind != "EOF":
                    print(f"{token.kind:<8} {token.value or '_'}")
            print()
        print("--- 三地址代码 ---")
        for line in code:
            print(line)
        print("--- 生成完成 ---")
        return 0
    except (OSError, CompileError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
