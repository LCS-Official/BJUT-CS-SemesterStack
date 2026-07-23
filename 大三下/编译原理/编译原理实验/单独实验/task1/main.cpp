#include "lexer.h"
#include <iostream>
#include <fstream>

int main(int argc, char* argv[]) {
    std::string infile = (argc > 1) ? argv[1] : "input.txt";
    Lexer lexer(infile);
    std::ofstream tokOut("tokens.txt");
    std::ofstream errOut("errors.txt");

    Token tok;
    while ((tok = lexer.scan()).type != TK_EOF) {
        if (tok.type == TK_ERROR) {
            errOut << "LexError at line " << tok.line << ", col " << tok.column
                   << ": " << tok.attr << " ('" << tok.lexeme << "')\n";
        } else {
            tokOut << tokenTypeName(tok.type) << " " << tok.attr << "\n";
        }
    }
    return 0;
}
