/*==================================================================
 * 编译原理实验二：语法分析程序
 * part2_tree.l - Flex词法分析器
 *
 * 词法规则：
 *   标识符:    letter (letter|digit)*
 *   十进制整数: 0 | [1-9][0-9]*
 *   八进制整数: 0[1-7][0-7]* | 00
 *   十六进制整数:0[xX][0-9a-fA-F]+
 *   运算符/分隔符: + - * / > < = >= <= <> ( ) { } ;
 *   关键字:    if then else while do
 *==================================================================*/
%option noyywrap nodefault yylineno

%{
#include "part2.h"
#include "part2_tree.tab.h"
%}

digit       [0-9]
letter      [a-zA-Z]
nonzero     [1-9]
octdigit    [0-7]
hexdigit    [0-9a-fA-F]
identifier  {letter}({letter}|{digit})*
decimal     0|{nonzero}{digit}*
octal       00|0{octdigit}+
hexa        0[xX]{hexdigit}+

%%

[ \n\t\r]+  { }

if          { return IF; }
then        { return THEN; }
else        { return ELSE; }
while       { return WHILE; }
do          { return DO; }

";"         { return EOL; }
"+"         { return PLUS; }
"-"         { return MINUS; }
"*"         { return MULTIPLY; }
"/"         { return DIVIDE; }
">"         { return G; }
"<"         { return L; }
"="         { return EQ; }
">="        { return GE; }
"<="        { return LE; }
"<>"        { return NE; }
"("         { return LP; }
")"         { return RP; }
"{"         { return LBP; }
"}"         { return RBP; }

{identifier} { return IDN; }
{decimal}   { return DEC; }
{octal}     { return OCT; }
{hexa}      { return HEX; }

<<EOF>>     { yyterminate(); }

.           { fprintf(stderr, "Warning: unknown char '%c' at line %d\n", yytext[0], yylineno); }

%%
