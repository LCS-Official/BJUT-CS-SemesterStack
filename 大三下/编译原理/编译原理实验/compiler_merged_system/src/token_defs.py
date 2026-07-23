# -*- coding: utf-8 -*-
"""统一 Token 定义。"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class TokenType(IntEnum):
    TK_EOF = 0
    TK_ERROR = 1

    TK_IDN = 10

    TK_INT10 = 20
    TK_INT8 = 21
    TK_INT16 = 22
    TK_REAL10 = 23
    TK_REAL8 = 24
    TK_REAL16 = 25

    TK_IF = 30
    TK_THEN = 31
    TK_ELSE = 32
    TK_WHILE = 33
    TK_DO = 34

    TK_PLUS = 40      # +
    TK_MINUS = 41     # -
    TK_MUL = 42       # *
    TK_DIV = 43       # /
    TK_GT = 44        # >
    TK_LT = 45        # <
    TK_EQ = 46        # =
    TK_LPAREN = 47    # (
    TK_RPAREN = 48    # )
    TK_SEMI = 49      # ;
    TK_LBRACE = 50    # {
    TK_RBRACE = 51    # }


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    attr: str
    line: int
    column: int


KEYWORDS = {
    "if": TokenType.TK_IF,
    "then": TokenType.TK_THEN,
    "else": TokenType.TK_ELSE,
    "while": TokenType.TK_WHILE,
    "do": TokenType.TK_DO,
}

OPERATORS = {
    "+": TokenType.TK_PLUS,
    "-": TokenType.TK_MINUS,
    "*": TokenType.TK_MUL,
    "/": TokenType.TK_DIV,
    ">": TokenType.TK_GT,
    "<": TokenType.TK_LT,
    "=": TokenType.TK_EQ,
    "(": TokenType.TK_LPAREN,
    ")": TokenType.TK_RPAREN,
    ";": TokenType.TK_SEMI,
    "{": TokenType.TK_LBRACE,
    "}": TokenType.TK_RBRACE,
}

DISPLAY_NAMES = {
    TokenType.TK_EOF: "EOF",
    TokenType.TK_ERROR: "ERROR",
    TokenType.TK_IDN: "IDN",
    TokenType.TK_INT10: "INT10",
    TokenType.TK_INT8: "INT8",
    TokenType.TK_INT16: "INT16",
    TokenType.TK_REAL10: "REAL10",
    TokenType.TK_REAL8: "REAL8",
    TokenType.TK_REAL16: "REAL16",
    TokenType.TK_IF: "IF",
    TokenType.TK_THEN: "THEN",
    TokenType.TK_ELSE: "ELSE",
    TokenType.TK_WHILE: "WHILE",
    TokenType.TK_DO: "DO",
    TokenType.TK_PLUS: "+",
    TokenType.TK_MINUS: "-",
    TokenType.TK_MUL: "*",
    TokenType.TK_DIV: "/",
    TokenType.TK_GT: ">",
    TokenType.TK_LT: "<",
    TokenType.TK_EQ: "=",
    TokenType.TK_LPAREN: "(",
    TokenType.TK_RPAREN: ")",
    TokenType.TK_SEMI: ";",
    TokenType.TK_LBRACE: "{",
    TokenType.TK_RBRACE: "}",
}

NUMERIC_TYPES = {
    TokenType.TK_INT10,
    TokenType.TK_INT8,
    TokenType.TK_INT16,
    TokenType.TK_REAL10,
    TokenType.TK_REAL8,
    TokenType.TK_REAL16,
}

REL_OP_TYPES = {TokenType.TK_GT, TokenType.TK_LT, TokenType.TK_EQ}


def token_name(token_type: TokenType) -> str:
    return DISPLAY_NAMES.get(token_type, token_type.name)


def token_output_line(token: Token) -> str:
    """按指导书样例输出：TOKEN 属性。EOF 不输出。"""
    return f"{token_name(token.type)} {token.attr}"
