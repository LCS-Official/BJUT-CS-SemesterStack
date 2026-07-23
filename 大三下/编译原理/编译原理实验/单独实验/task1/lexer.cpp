#include "lexer.h"
#include <cctype>
#include <stdexcept>
#include <unordered_map>

static const std::unordered_map<std::string, TokenType> KEYWORDS = {
    {"if",TK_IF},{"then",TK_THEN},{"else",TK_ELSE},{"while",TK_WHILE},{"do",TK_DO}
};

Lexer::Lexer(const std::string& filename) : line(1), col(0), ch(0) {
    file.open(filename);
    if (!file) throw std::runtime_error("Cannot open " + filename);
    nextChar();
}

void Lexer::nextChar() {
    int c = file.get();
    if (c == EOF) { ch = '\0'; return; }
    ch = (char)c;
    if (ch == '\n') { line++; col = 0; }
    else col++;
}

Token Lexer::scan() {
    while (ch && isspace((unsigned char)ch)) nextChar();
    if (!ch) return {TK_EOF, "", "_", line, col};

    int sl = line, sc = col;

    // identifier / keyword
    if (isalpha((unsigned char)ch)) {
        std::string lex;
        while (ch && isalnum((unsigned char)ch)) { lex += ch; nextChar(); }
        auto it = KEYWORDS.find(lex);
        if (it != KEYWORDS.end()) return {it->second, lex, "_", sl, sc};
        return {TK_IDN, lex, lex, sl, sc};
    }

    // number
    if (isdigit((unsigned char)ch)) {
        std::string lex;
        if (ch == '0') {
            lex += ch; nextChar();
            if (ch == 'x' || ch == 'X') {
                lex += ch; nextChar();
                std::string hp;
                while (ch && isxdigit((unsigned char)ch)) { hp += ch; lex += ch; nextChar(); }
                if (hp.empty()) return {TK_ERROR, lex, "invalid hex", sl, sc};
                if (ch == '.') {
                    lex += ch; nextChar();
                    std::string fp;
                    while (ch && isxdigit((unsigned char)ch)) { fp += ch; lex += ch; nextChar(); }
                    long long iv = std::stoll(hp, nullptr, 16);
                    double fv = 0, base = 1.0/16;
                    for (char c : fp) { fv += (isdigit(c)?c-'0':tolower(c)-'a'+10)*base; base/=16; }
                    return {TK_REAL16, lex, std::to_string(iv+fv), sl, sc};
                }
                return {TK_INT16, lex, std::to_string(std::stoll(hp,nullptr,16)), sl, sc};
            }
            if (ch >= '0' && ch <= '7') {
                std::string op;
                while (ch >= '0' && ch <= '7') { op += ch; lex += ch; nextChar(); }
                if (ch && isdigit((unsigned char)ch)) {
                    while (ch && isdigit((unsigned char)ch)) { lex += ch; nextChar(); }
                    return {TK_ERROR, lex, "invalid octal", sl, sc};
                }
                return {TK_INT8, lex, std::to_string(std::stoll(op,nullptr,8)), sl, sc};
            }
            if (ch == '.') {
                lex += ch; nextChar();
                while (ch && isdigit((unsigned char)ch)) { lex += ch; nextChar(); }
                return {TK_REAL10, lex, lex, sl, sc};
            }
            return {TK_INT10, lex, "0", sl, sc};
        }
        while (ch && isdigit((unsigned char)ch)) { lex += ch; nextChar(); }
        if (ch == '.') {
            lex += ch; nextChar();
            while (ch && isdigit((unsigned char)ch)) { lex += ch; nextChar(); }
            return {TK_REAL10, lex, lex, sl, sc};
        }
        return {TK_INT10, lex, lex, sl, sc};
    }

    char c = ch; nextChar();
    switch (c) {
        case '+': return {TK_PLUS,   "+","_",sl,sc};
        case '-': return {TK_MINUS,  "-","_",sl,sc};
        case '*': return {TK_MUL,    "*","_",sl,sc};
        case '/': return {TK_DIV,    "/","_",sl,sc};
        case '>': return {TK_GT,     ">","_",sl,sc};
        case '<': return {TK_LT,     "<","_",sl,sc};
        case '=': return {TK_EQ,     "=","_",sl,sc};
        case '(': return {TK_LPAREN, "(","_",sl,sc};
        case ')': return {TK_RPAREN, ")","_",sl,sc};
        case ';': return {TK_SEMI,   ";","_",sl,sc};
        case '{': return {TK_LBRACE, "{","_",sl,sc};
        case '}': return {TK_RBRACE, "}","_",sl,sc};
        default:  return {TK_ERROR, std::string(1,c), "illegal char", sl, sc};
    }
}
