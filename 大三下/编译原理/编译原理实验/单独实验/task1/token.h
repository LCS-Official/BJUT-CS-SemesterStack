#pragma once
#include <string>

enum TokenType {
    TK_EOF = 0, TK_ERROR = 1,
    TK_IDN = 10,
    TK_INT10 = 20, TK_INT8 = 21, TK_INT16 = 22,
    TK_REAL10 = 23, TK_REAL8 = 24, TK_REAL16 = 25,
    TK_IF = 30, TK_THEN = 31, TK_ELSE = 32, TK_WHILE = 33, TK_DO = 34,
    TK_PLUS = 40, TK_MINUS = 41, TK_MUL = 42, TK_DIV = 43,
    TK_GT = 44, TK_LT = 45, TK_EQ = 46,
    TK_LPAREN = 47, TK_RPAREN = 48, TK_SEMI = 49,
    TK_LBRACE = 50, TK_RBRACE = 51
};

struct Token {
    TokenType type;
    std::string lexeme;
    std::string attr;
    int line, column;
};

inline std::string tokenTypeName(TokenType t) {
    switch (t) {
        case TK_EOF: return "EOF"; case TK_ERROR: return "ERROR";
        case TK_IDN: return "IDN";
        case TK_INT10: return "INT10"; case TK_INT8: return "INT8"; case TK_INT16: return "INT16";
        case TK_REAL10: return "REAL10"; case TK_REAL8: return "REAL8"; case TK_REAL16: return "REAL16";
        case TK_IF: return "IF"; case TK_THEN: return "THEN"; case TK_ELSE: return "ELSE";
        case TK_WHILE: return "WHILE"; case TK_DO: return "DO";
        case TK_PLUS: return "+"; case TK_MINUS: return "-";
        case TK_MUL: return "*"; case TK_DIV: return "/";
        case TK_GT: return ">"; case TK_LT: return "<"; case TK_EQ: return "=";
        case TK_LPAREN: return "("; case TK_RPAREN: return ")";
        case TK_SEMI: return ";"; case TK_LBRACE: return "{"; case TK_RBRACE: return "}";
        default: return "UNKNOWN";
    }
}
