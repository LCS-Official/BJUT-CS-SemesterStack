/*==================================================================
 * 编译原理实验二：语法分析程序
 * part2_tree.y - Bison语法分析器（LALR(1)分析法）
 *
 * 文法产生式：
 *   P  → L | L P                          （程序）
 *   L  → S ;                              （语句列表）
 *   S  → id = E                           （赋值语句）
 *   S  → if C then S                      （条件语句）
 *   S  → if C then S else S               （条件-否则语句）
 *   S  → while C do S                     （循环语句）
 *   S  → { P }                            （复合语句块）
 *   C  → E > E  | E < E  | E = E           （比较条件）
 *   C  → E >= E | E <= E | E <> E         （比较条件扩展）
 *   E  → E + T | E - T | T               （表达式）
 *   T  → T * F | T / F | F               （项）
 *   F  → ( E )                            （括号表达式）
 *   F  → id | int10 | int8 | int16       （基本因子）
 *
 * 输出：语法分析树（缩进格式）
 *==================================================================*/
%{
#include <stdio.h>
#include <stdlib.h>
#include "part2.h"

/* 用于存储临时孩子节点指针的数组 */
struct node* nodeList[10];
%}

/* ---- 语义值类型定义 ---- */
%union {
    struct node *node;  /* 语法树节点指针 */
}

/* ---- Token 声明 ---- */
%token EOL                                    /* 语句结束符 ; */
%token <node> IDN DEC OCT HEX                 /* 标识符、十进制/八进制/十六进制数 */
%token <node> PLUS MINUS MULTIPLY DIVIDE      /* 算术运算符 */
%token <node> G L EQ GE LE NE LP RP LBP RBP   /* 比较运算符和括号 */
%token <node> IF THEN ELSE WHILE DO           /* 关键字 */

/* ---- 非终结符类型声明 ---- */
%type <node> para lexs stat cond elem term fina

/* ---- 运算符优先级和结合性 ---- */
/* 优先级从低到高排列，同级别左结合 */
%right IF ELSE THEN       /* if-then-else 移进/归约冲突用 %right 解决 */
%left G L EQ GE LE NE     /* 比较运算符 */
%left PLUS MINUS          /* 加减运算 */
%left MULTIPLY DIVIDE     /* 乘除运算 */
%right NEG                /* 负号（备用） */

/* ---- 起始符号 ---- */
%start allinall

%%
/*================================================================
 * 产生式规则（每条规则的动作构建对应的子树）
 *================================================================*/

/* allinall: 处理多个语句/程序段落 */
allinall:
    /* 空 */
  | allinall para EOL
      { traverse(0, $2);    /* 输出语法树 */
        treefree($2);       /* 释放语法树内存 */
        print2file("\n"); }  /* 语句之间加空行 */
  | allinall EOL
      { /* 允许空行 */ }
  | allinall error EOL
      { yyerrok; }          /* 错误恢复：跳过当前行继续 */
  ;

/* para: 程序（Program） = 语句列表 */
/* P → L | L P */
para: lexs
      { nodeList[0] = $1;
        $$ = newnode(1, "P", nodeList); }
  | lexs para
      { nodeList[0] = $1;
        nodeList[1] = $2;
        $$ = newnode(2, "P", nodeList); }
  ;

/* lexs: 语句列表 = 单条语句（加上分号在 stat 后面由调用方处理） */
/* L → S ; */
lexs: stat
      { nodeList[0] = $1;
        $$ = newnode(1, "L", nodeList); }
  ;

/* stat: 语句（Statement） */
/* S → id = E */
stat: IDN EQ elem
      { nodeList[0] = newleaf("ID");
        nodeList[1] = newleaf("EQ");
        nodeList[2] = $3;
        $$ = newnode(3, "S", nodeList); }

  /* S → if C then S else S */
  | IF cond LBP THEN stat RBP ELSE stat
      { nodeList[0] = newleaf("IF");
        nodeList[1] = $2;
        nodeList[2] = newleaf("THEN");
        nodeList[3] = $5;
        nodeList[4] = newleaf("ELSE");
        nodeList[5] = $8;
        $$ = newnode(6, "S", nodeList); }

  /* S → if C then S else S（无括号版本） */
  | IF cond THEN stat ELSE stat
      { nodeList[0] = newleaf("IF");
        nodeList[1] = $2;
        nodeList[2] = newleaf("THEN");
        nodeList[3] = $4;
        nodeList[4] = newleaf("ELSE");
        nodeList[5] = $6;
        $$ = newnode(6, "S", nodeList); }

  /* S → if C then S */
  | IF cond LBP THEN stat RBP
      { nodeList[0] = newleaf("IF");
        nodeList[1] = $2;
        nodeList[2] = newleaf("THEN");
        nodeList[3] = $5;
        $$ = newnode(4, "S", nodeList); }

  /* S → if C then S（无括号版本） */
  | IF cond THEN stat
      { nodeList[0] = newleaf("IF");
        nodeList[1] = $2;
        nodeList[2] = newleaf("THEN");
        nodeList[3] = $4;
        $$ = newnode(4, "S", nodeList); }

  /* S → while C do S */
  | WHILE cond DO stat
      { nodeList[0] = newleaf("WHILE");
        nodeList[1] = $2;
        nodeList[2] = newleaf("DO");
        nodeList[3] = $4;
        $$ = newnode(4, "S", nodeList); }

  /* S → { P } */
  | LBP para RBP
      { nodeList[0] = newleaf("{");
        nodeList[1] = $2;
        nodeList[2] = newleaf("}");
        $$ = newnode(3, "S", nodeList); }
  ;

/* cond: 条件（Condition） */
/* C → E > E | E < E | E = E | E >= E | E <= E | E <> E */
cond: elem G elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf(">");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  | elem L elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf("<");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  | elem EQ elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf("=");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  | elem GE elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf(">=");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  | elem LE elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf("<=");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  | elem NE elem
      { nodeList[0] = $1;
        nodeList[1] = newleaf("!=");
        nodeList[2] = $3;
        $$ = newnode(3, "C", nodeList); }
  ;

/* elem: 表达式（Expression） */
/* E → E + T | E - T | T */
elem: term
      { nodeList[0] = $1;
        $$ = newnode(1, "E", nodeList); }
  | elem PLUS term
      { nodeList[0] = $1;
        nodeList[1] = newleaf("+");
        nodeList[2] = $3;
        $$ = newnode(3, "E", nodeList); }
  | elem MINUS term
      { nodeList[0] = $1;
        nodeList[1] = newleaf("-");
        nodeList[2] = $3;
        $$ = newnode(3, "E", nodeList); }
  ;

/* term: 项（Term） */
/* T → T * F | T / F | F */
term: fina
      { nodeList[0] = $1;
        $$ = newnode(1, "T", nodeList); }
  | term MULTIPLY fina
      { nodeList[0] = $1;
        nodeList[1] = newleaf("*");
        nodeList[2] = $3;
        $$ = newnode(3, "T", nodeList); }
  | term DIVIDE fina
      { nodeList[0] = $1;
        nodeList[1] = newleaf("/");
        nodeList[2] = $3;
        $$ = newnode(3, "T", nodeList); }
  ;

/* fina: 因子（Factor） */
/* F → ( E ) | id | int10 | int8 | int16 */
fina: LP elem RP
      { nodeList[0] = newleaf("(");
        nodeList[1] = $2;
        nodeList[2] = newleaf(")");
        $$ = newnode(3, "F", nodeList); }
  | IDN
      { nodeList[0] = newleaf("ID");
        $$ = newnode(1, "F", nodeList); }
  | DEC
      { nodeList[0] = newleaf("DEC");
        $$ = newnode(1, "F", nodeList); }
  | OCT
      { nodeList[0] = newleaf("OCT");
        $$ = newnode(1, "F", nodeList); }
  | HEX
      { nodeList[0] = newleaf("HEX");
        $$ = newnode(1, "F", nodeList); }
  ;

%%
