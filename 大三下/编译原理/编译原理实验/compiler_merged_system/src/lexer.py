# -*- coding: utf-8 -*-
"""实验一：词法分析器。

拓展版功能：
1. 文件输入 + scan() 每次返回一个 Token；
2. 支持 IDN、关键字、INT10/INT8/INT16、REAL10/REAL8/REAL16；
3. 支持拓展标识符：my_var、a.b 这类形式；
4. 维护标识符表和常量表；
5. 记录行号、列号，非法字符写入 errors.txt。
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .token_defs import KEYWORDS, NUMERIC_TYPES, OPERATORS, Token, TokenType, token_name


class Lexer:
    """面向对象封装的词法分析器，只通过 scan() 对外提供 Token。"""

    def __init__(self, source: str | Path, *, from_text: bool = False) -> None:
        if from_text:
            self.text = str(source)
        else:
            self.text = Path(source).read_text(encoding="utf-8")
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[str] = []
        self.identifier_table: dict[str, dict[str, int | str]] = {}
        self.constant_table: dict[str, dict[str, int | str]] = {}

    def scan(self) -> Token:
        self._skip_whitespace()
        start_line, start_col = self.line, self.column

        if self._eof():
            token = Token(TokenType.TK_EOF, "", "_", start_line, start_col)
            self.tokens.append(token)
            return token

        ch = self._peek()

        if ch.isalpha():
            token = self._scan_identifier_or_keyword(start_line, start_col)
        elif ch.isdigit():
            token = self._scan_number(start_line, start_col)
        elif ch in OPERATORS:
            self._advance()
            token = Token(OPERATORS[ch], ch, "_", start_line, start_col)
        else:
            self._advance()
            message = f"LexicalError at line {start_line}, column {start_col}: illegal character {ch!r}"
            token = Token(TokenType.TK_ERROR, ch, message, start_line, start_col)
            self.errors.append(message)

        self._remember_token(token)
        self.tokens.append(token)
        return token

    def _scan_identifier_or_keyword(self, line: int, col: int) -> Token:
        # 基本形式：字母开头，后接字母或数字。
        chars: list[str] = []
        chars.append(self._advance())
        while not self._eof() and (self._peek().isalpha() or self._peek().isdigit()):
            chars.append(self._advance())

        # 拓展形式：允许出现 _ 或 . 后面跟至少一个字母/数字。
        # 例如 my_var、obj.field。若 _/. 后面不是字母/数字，则不吞掉，交给后续扫描报错或处理。
        while not self._eof() and self._peek() in {"_", "."} and (self._peek(1).isalpha() or self._peek(1).isdigit()):
            chars.append(self._advance())
            while not self._eof() and (self._peek().isalpha() or self._peek().isdigit()):
                chars.append(self._advance())

        lexeme = "".join(chars)
        token_type = KEYWORDS.get(lexeme, TokenType.TK_IDN)
        attr = "_" if token_type != TokenType.TK_IDN else lexeme
        return Token(token_type, lexeme, attr, line, col)

    def _scan_number(self, line: int, col: int) -> Token:
        # 十六进制整数 / 十六进制实数：0x3f / 0X88.80
        if self._peek() == "0" and self._peek(1) in {"x", "X"}:
            return self._scan_hex_number(line, col)

        lexeme = self._consume_while(lambda c: c.isdigit())

        # 实数拓展：先根据整数部分判断 REAL10 / REAL8。
        if self._peek() == ".":
            lexeme += self._advance()
            fraction = self._consume_while(lambda c: c.isdigit())
            lexeme += fraction
            if not fraction:
                return self._error_token(lexeme, line, col, "real number needs digits after '.'")
            if lexeme.startswith("0") and len(lexeme.split(".")[0]) > 1:
                int_part, frac_part = lexeme.split(".", 1)
                if all(c in "01234567" for c in int_part) and all(c in "01234567" for c in frac_part):
                    value = int(int_part, 8)
                    for index, digit in enumerate(frac_part, start=1):
                        value += int(digit, 8) / (8 ** index)
                    return Token(TokenType.TK_REAL8, lexeme, self._format_float(value), line, col)
                return self._error_token(lexeme, line, col, "invalid octal real number")
            return Token(TokenType.TK_REAL10, lexeme, self._format_float(float(lexeme)), line, col)

        if len(lexeme) == 1 and lexeme == "0":
            return Token(TokenType.TK_INT10, lexeme, "0", line, col)

        if lexeme.startswith("0"):
            if all(c in "01234567" for c in lexeme):
                return Token(TokenType.TK_INT8, lexeme, str(int(lexeme, 8)), line, col)
            return self._error_token(lexeme, line, col, "invalid octal integer")

        return Token(TokenType.TK_INT10, lexeme, str(int(lexeme, 10)), line, col)

    def _scan_hex_number(self, line: int, col: int) -> Token:
        lexeme = self._advance() + self._advance()  # 0x / 0X
        int_part = self._consume_while(self._is_hex_digit)
        lexeme += int_part
        if not int_part:
            return self._error_token(lexeme, line, col, "hex integer needs at least one hex digit")

        if self._peek() != ".":
            return Token(TokenType.TK_INT16, lexeme, str(int(int_part, 16)), line, col)

        lexeme += self._advance()
        frac_part = self._consume_while(self._is_hex_digit)
        lexeme += frac_part
        if not frac_part:
            return self._error_token(lexeme, line, col, "hex real number needs digits after '.'")

        value = int(int_part, 16)
        for index, digit in enumerate(frac_part, start=1):
            value += int(digit, 16) / (16 ** index)
        return Token(TokenType.TK_REAL16, lexeme, self._format_float(value), line, col)

    def _remember_token(self, token: Token) -> None:
        if token.type == TokenType.TK_IDN:
            if token.attr not in self.identifier_table:
                self.identifier_table[token.attr] = {
                    "name": token.attr,
                    "first_line": token.line,
                    "first_column": token.column,
                    "count": 0,
                }
            self.identifier_table[token.attr]["count"] = int(self.identifier_table[token.attr]["count"]) + 1
        elif token.type in NUMERIC_TYPES:
            key = f"{token_name(token.type)}:{token.lexeme}"
            if key not in self.constant_table:
                self.constant_table[key] = {
                    "type": token_name(token.type),
                    "lexeme": token.lexeme,
                    "value": token.attr,
                    "first_line": token.line,
                    "first_column": token.column,
                    "count": 0,
                }
            self.constant_table[key]["count"] = int(self.constant_table[key]["count"]) + 1

    def format_identifier_table(self) -> str:
        if not self.identifier_table:
            return "<empty>\n"
        lines = ["name\tfirst_line\tfirst_column\tcount"]
        for name, info in sorted(self.identifier_table.items()):
            lines.append(f"{name}\t{info['first_line']}\t{info['first_column']}\t{info['count']}")
        return "\n".join(lines) + "\n"

    def format_constant_table(self) -> str:
        if not self.constant_table:
            return "<empty>\n"
        lines = ["type\tlexeme\tvalue\tfirst_line\tfirst_column\tcount"]
        for _, info in sorted(self.constant_table.items(), key=lambda item: (str(item[1]['type']), str(item[1]['lexeme']))):
            lines.append(
                f"{info['type']}\t{info['lexeme']}\t{info['value']}\t"
                f"{info['first_line']}\t{info['first_column']}\t{info['count']}"
            )
        return "\n".join(lines) + "\n"

    def _error_token(self, lexeme: str, line: int, col: int, reason: str) -> Token:
        message = f"LexicalError at line {line}, column {col}: {reason}: {lexeme!r}"
        self.errors.append(message)
        return Token(TokenType.TK_ERROR, lexeme, message, line, col)

    def _skip_whitespace(self) -> None:
        while not self._eof() and self._peek() in {" ", "\t", "\r", "\n"}:
            self._advance()

    def _consume_while(self, predicate) -> str:
        chars: list[str] = []
        while not self._eof() and predicate(self._peek()):
            chars.append(self._advance())
        return "".join(chars)

    @staticmethod
    def _is_hex_digit(ch: str) -> bool:
        return ch.isdigit() or ch.lower() in "abcdef"

    @staticmethod
    def _format_float(value: float) -> str:
        return f"{value:.12g}"

    def _peek(self, offset: int = 0) -> str:
        index = self.pos + offset
        if index >= len(self.text):
            return ""
        return self.text[index]

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def _eof(self) -> bool:
        return self.pos >= len(self.text)
