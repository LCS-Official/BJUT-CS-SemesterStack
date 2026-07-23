#pragma once
#include "token.h"
#include <fstream>
#include <string>

class Lexer {
public:
    Lexer(const std::string& filename);
    Token scan();
private:
    std::ifstream file;
    int line, col;
    char ch;
    void nextChar();
};
