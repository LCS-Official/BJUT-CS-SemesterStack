# -*- coding: utf-8 -*-
"""实验二 + 实验三：递归下降语法分析，并在分析过程中生成三地址代码。

本版对 parse.txt 做了增强：左栏显示使用的产生式，右栏显示该产生式在当前
源程序中对应的真实片段/属性值，便于验收展示。
同时新增 parse_tree.txt：用缩进 ASCII 树展示程序结构，更直观。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .codegen import CodeGenerator
from .lexer import Lexer
from .token_defs import NUMERIC_TYPES, REL_OP_TYPES, Token, TokenType, token_name


@dataclass
class TreeNode:
    label: str
    children: list["TreeNode"] = field(default_factory=list)

    def add(self, *nodes: "TreeNode") -> "TreeNode":
        for node in nodes:
            if node is not None:
                self.children.append(node)
        return self


@dataclass
class ExprResult:
    """表达式属性。

    place: 三地址代码中使用的位置，可能是变量名、常量值或临时变量 t1。
    text:  给 parse.txt 展示用的真实表达式文本，尽量保留人能看懂的形式。
    tree:  给 parse_tree.txt 展示用的表达式树节点。
    """

    place: str
    text: str
    tree: TreeNode


class Parser:
    def __init__(self, lexer: Lexer, codegen: CodeGenerator | None = None) -> None:
        self.lexer = lexer
        self.codegen = codegen or CodeGenerator()
        self.current: Token = self.lexer.scan()
        self.errors: list[str] = []
        # trace_rows 中每行是 [产生式, 当前真实含义]
        self.trace_rows: list[list[str]] = []
        self.tree_root: TreeNode | None = None

    @property
    def trace(self) -> list[str]:
        return self.format_trace().splitlines()

    def format_trace(self) -> str:
        if not self.trace_rows:
            return ""
        left_width = max(26, max(len(row[0]) for row in self.trace_rows))
        lines = []
        for rule, meaning in self.trace_rows:
            if meaning:
                lines.append(f"{rule:<{left_width}} | {meaning}")
            else:
                lines.append(rule)
        return "\n".join(lines) + "\n"

    def format_tree(self) -> str:
        if self.tree_root is None:
            return ""
        lines: list[str] = []

        def walk(node: TreeNode, prefix: str = "", is_last: bool = True, root: bool = False) -> None:
            if root:
                lines.append(node.label)
                for idx, child in enumerate(node.children):
                    walk(child, "", idx == len(node.children) - 1, False)
                return
            connector = "└── " if is_last else "├── "
            lines.append(prefix + connector + node.label)
            child_prefix = prefix + ("    " if is_last else "│   ")
            for idx, child in enumerate(node.children):
                walk(child, child_prefix, idx == len(node.children) - 1, False)

        walk(self.tree_root, root=True)
        return "\n".join(lines) + "\n"

    def _trace(self, rule: str, meaning: str = "") -> int:
        self.trace_rows.append([rule, meaning])
        return len(self.trace_rows) - 1

    def _set_trace_meaning(self, index: int, meaning: str) -> None:
        if 0 <= index < len(self.trace_rows):
            self.trace_rows[index][1] = meaning

    def parseProgram(self) -> bool:
        self._trace("Start: P", "从程序入口开始分析")
        self.tree_root = self._parse_sequence(stop_at=TokenType.TK_EOF, root_label="P")
        if self.current.type != TokenType.TK_EOF:
            self._match(TokenType.TK_EOF)
        ok = not self.errors and not self.lexer.errors
        self._trace("Result: ACCEPT" if ok else "Result: REJECT WITH ERRORS")
        return ok

    def parseStmt(self) -> TreeNode | None:
        t = self.current.type
        if t == TokenType.TK_IDN:
            target = self.current.attr
            row = self._trace("S -> id = E", f"当前识别赋值语句，左值 id = {target}")
            self._advance()
            self._match(TokenType.TK_EQ)
            value = self.parseExpr()
            self._set_trace_meaning(row, f"S => {target} = {value.text}")
            self.codegen.emit(f"{target} := {value.place}")
            return TreeNode("S: id = E", [TreeNode(f"id: {target}"), TreeNode(f"E: {value.text}")])
        elif t == TokenType.TK_IF:
            return self._parse_if()
        elif t == TokenType.TK_WHILE:
            return self._parse_while()
        elif t == TokenType.TK_LBRACE:
            row = self._trace("S -> { P }", "当前识别复合语句块")
            self._advance()
            inner = self._parse_sequence(stop_at=TokenType.TK_RBRACE, root_label="P")
            self._match(TokenType.TK_RBRACE)
            self._set_trace_meaning(row, "S => { 多条语句 }")
            return TreeNode("S: { P }", [inner])
        else:
            self._syntax_error("statement", self.current)
            self._advance()
            self._synchronize()
            return TreeNode("S: <error>")

    def parseCond(self, true_label: str, false_label: str) -> tuple[None, TreeNode]:
        row = self._trace("C -> E relop E", "开始识别条件：左表达式 关系运算符 右表达式")
        left = self.parseExpr()
        if self.current.type in REL_OP_TYPES:
            op = self.current.lexeme
            self._advance()
        else:
            self._syntax_error("relational operator >, < or =", self.current)
            op = "?"
        right = self.parseExpr()
        self._set_trace_meaning(row, f"C => {left.text} {op} {right.text}; 真->{true_label}, 假->{false_label}")
        self.codegen.emit(f"if {left.place} {op} {right.place} goto {true_label}")
        self.codegen.emit(f"goto {false_label}")
        cond_tree = TreeNode(f"C: E {op} E", [TreeNode(f"E: {left.text}"), TreeNode(f"E: {right.text}")])
        return None, cond_tree

    def parseExpr(self) -> ExprResult:
        row = self._trace("E -> T E'", "开始识别表达式 E，加减层")
        left = self.parseTerm()
        while self.current.type in {TokenType.TK_PLUS, TokenType.TK_MINUS}:
            op = self.current.lexeme
            op_row = self._trace(f"E' -> {op} T E'", f"E 后续发现 {op}，继续接一个 T")
            self._advance()
            right = self.parseTerm()
            temp = self.codegen.newtemp()
            self.codegen.emit(f"{temp} := {left.place} {op} {right.place}")
            combined_text = f"{left.text} {op} {right.text}"
            self._set_trace_meaning(op_row, f"E => {combined_text}; place = {temp}")
            left = ExprResult(
                place=temp,
                text=combined_text,
                tree=TreeNode(f"E: {combined_text}", [left.tree, right.tree]),
            )
        self._set_trace_meaning(row, f"E => {left.text}; place = {left.place}")
        return left

    def parseTerm(self) -> ExprResult:
        row = self._trace("T -> F T'", "开始识别项 T，乘除层")
        left = self.parseFactor()
        while self.current.type in {TokenType.TK_MUL, TokenType.TK_DIV}:
            op = self.current.lexeme
            op_row = self._trace(f"T' -> {op} F T'", f"T 后续发现 {op}，继续接一个 F")
            self._advance()
            right = self.parseFactor()
            if op == "/" and self._is_zero_constant(right.place):
                self.errors.append(
                    f"SemanticError: division by zero in expression '{left.text} / {right.text}'"
                )
            temp = self.codegen.newtemp()
            self.codegen.emit(f"{temp} := {left.place} {op} {right.place}")
            combined_text = f"{left.text} {op} {right.text}"
            self._set_trace_meaning(op_row, f"T => {combined_text}; place = {temp}")
            left = ExprResult(
                place=temp,
                text=combined_text,
                tree=TreeNode(f"T: {combined_text}", [left.tree, right.tree]),
            )
        self._set_trace_meaning(row, f"T => {left.text}; place = {left.place}")
        return left

    def parseFactor(self) -> ExprResult:
        t = self.current.type
        if t == TokenType.TK_LPAREN:
            row = self._trace("F -> ( E )", "遇到左括号：把括号内的 E 当成一个整体 F")
            self._advance()
            inner = self.parseExpr()
            self._match(TokenType.TK_RPAREN)
            text = f"({inner.text})"
            self._set_trace_meaning(row, f"F => {text}; place = {inner.place}")
            return ExprResult(place=inner.place, text=text, tree=TreeNode(f"F: {text}", [TreeNode(f"E: {inner.text}")]))
        if t == TokenType.TK_IDN:
            place = self.current.attr
            self._trace("F -> id", f"F => {place}")
            self._advance()
            return ExprResult(place=place, text=place, tree=TreeNode(f"F: id {place}"))
        if t in NUMERIC_TYPES:
            type_name = token_name(t).lower()
            lexeme = self.current.lexeme
            value = self.current.attr
            if lexeme != value:
                meaning = f"F => {value}，源程序写作 {lexeme}"
                label = f"F: {type_name} {value} (源程序 {lexeme})"
            else:
                meaning = f"F => {value}"
                label = f"F: {type_name} {value}"
            self._trace(f"F -> {type_name}", meaning)
            self._advance()
            return ExprResult(place=value, text=value, tree=TreeNode(label))
        self._syntax_error("expression", self.current)
        self._advance()
        return ExprResult(place="0", text="<error>", tree=TreeNode("F: <error>"))

    # 兼容分工表中的命名
    parseP = parseProgram
    parseS = parseStmt
    parseC = parseCond
    parseE = parseExpr
    parseT = parseTerm
    parseF = parseFactor

    def _parse_if(self) -> TreeNode:
        row = self._trace("S -> if C then S [else S]", "当前识别 if 语句，else 分支可选")
        self._match(TokenType.TK_IF)
        true_label = self.codegen.newlabel()
        false_label = self.codegen.newlabel()
        _, cond_tree = self.parseCond(true_label, false_label)
        self._match(TokenType.TK_THEN)
        self.codegen.emit(f"{true_label}:")
        then_tree = self.parseStmt()

        if self.current.type == TokenType.TK_ELSE:
            end_label = self.codegen.newlabel()
            self._set_trace_meaning(row, f"S => if C then S else S; then->{true_label}, else->{false_label}, 结束->{end_label}")
            self.codegen.emit(f"goto {end_label}")
            self.codegen.emit(f"{false_label}:")
            self._advance()
            else_tree = self.parseStmt()
            self.codegen.emit(f"{end_label}:")
            return TreeNode("S: if C then S else S", [cond_tree, then_tree, else_tree])
        else:
            self._set_trace_meaning(row, f"S => if C then S; 条件真->{true_label}, 条件假->{false_label}")
            self.codegen.emit(f"{false_label}:")
            return TreeNode("S: if C then S", [cond_tree, then_tree])

    def _parse_while(self) -> TreeNode:
        begin_label = self.codegen.newlabel()
        true_label = self.codegen.newlabel()
        false_label = self.codegen.newlabel()
        row = self._trace(
            "S -> while C do S",
            f"当前识别 while 语句；循环入口->{begin_label}, 条件真->{true_label}, 条件假/退出->{false_label}",
        )
        self.codegen.emit(f"{begin_label}:")
        self._match(TokenType.TK_WHILE)
        _, cond_tree = self.parseCond(true_label, false_label)
        self._match(TokenType.TK_DO)
        self.codegen.emit(f"{true_label}:")
        body_tree = self.parseStmt()
        self.codegen.emit(f"goto {begin_label}")
        self.codegen.emit(f"{false_label}:")
        self._set_trace_meaning(
            row,
            f"S => while C do S; 每轮从 {begin_label} 判断，真进 {true_label}，假跳 {false_label}",
        )
        return TreeNode("S: while C do S", [cond_tree, body_tree])

    def _parse_sequence(self, *, stop_at: TokenType, root_label: str = "P") -> TreeNode:
        row = self._trace("P -> S ; P' | ε", "P 表示语句序列：若遇到 S 就分析 S;，若到结尾则取 ε")
        stmt_count = 0
        children: list[TreeNode] = []
        while self.current.type not in {stop_at, TokenType.TK_EOF}:
            if self.current.type == TokenType.TK_SEMI:
                self._syntax_error("statement before ';'", self.current)
                self._advance()
                continue
            stmt_count += 1
            stmt_tree = self.parseStmt()
            if stmt_tree is not None:
                children.append(stmt_tree)
            if self.current.type == TokenType.TK_SEMI:
                self._advance()
            else:
                self._syntax_error(";", self.current)
                self._synchronize()
                if self.current.type == TokenType.TK_SEMI:
                    self._advance()
        self._set_trace_meaning(row, f"P => 共识别 {stmt_count} 条语句；后续 P' => ε")
        return TreeNode(root_label, children)


    @staticmethod
    def _is_zero_constant(text: str) -> bool:
        try:
            return float(text) == 0.0
        except ValueError:
            return False

    def _match(self, expected: TokenType) -> bool:
        if self.current.type == expected:
            self._advance()
            return True
        self._syntax_error(token_name(expected), self.current)
        return False

    def _advance(self) -> None:
        self.current = self.lexer.scan()

    def _syntax_error(self, expected: str, got: Token) -> None:
        message = (
            f"SyntaxError at line {got.line}, column {got.column}: "
            f"expected {expected}, got {token_name(got.type)}"
        )
        self.errors.append(message)

    def _synchronize(self) -> None:
        while self.current.type not in {TokenType.TK_SEMI, TokenType.TK_RBRACE, TokenType.TK_EOF}:
            self._advance()
