# -*- coding: utf-8 -*-
"""编译流程封装：源程序 -> tokens.txt -> parse.txt -> parse_tree.txt -> tac.txt -> errors.txt。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .codegen import CodeGenerator
from .lexer import Lexer
from .parser import Parser
from .token_defs import TokenType, token_output_line


@dataclass
class CompileResult:
    ok: bool
    tokens_text: str
    parse_text: str
    parse_tree_text: str
    tac_text: str
    symbols_text: str
    constants_text: str
    errors_text: str


def compile_text(source_text: str) -> CompileResult:
    lexer = Lexer(source_text, from_text=True)
    codegen = CodeGenerator()
    parser = Parser(lexer, codegen)
    ok = parser.parseProgram()

    tokens_text = "\n".join(
        token_output_line(token) for token in lexer.tokens if token.type != TokenType.TK_EOF
    )
    if tokens_text:
        tokens_text += "\n"

    parse_text = parser.format_trace()
    parse_tree_text = parser.format_tree()
    tac_text = codegen.text()
    symbols_text = lexer.format_identifier_table()
    constants_text = lexer.format_constant_table()
    all_errors = lexer.errors + parser.errors
    errors_text = "\n".join(all_errors) + ("\n" if all_errors else "No errors.\n")

    return CompileResult(
        ok=ok,
        tokens_text=tokens_text,
        parse_text=parse_text,
        parse_tree_text=parse_tree_text,
        tac_text=tac_text,
        symbols_text=symbols_text,
        constants_text=constants_text,
        errors_text=errors_text,
    )


def compile_file(input_path: str | Path, output_dir: str | Path = "output") -> CompileResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_text = input_path.read_text(encoding="utf-8")
    result = compile_text(source_text)
    (output_dir / "tokens.txt").write_text(result.tokens_text, encoding="utf-8")
    (output_dir / "parse.txt").write_text(result.parse_text, encoding="utf-8")
    (output_dir / "parse_tree.txt").write_text(result.parse_tree_text, encoding="utf-8")
    (output_dir / "tac.txt").write_text(result.tac_text, encoding="utf-8")
    (output_dir / "symbols.txt").write_text(result.symbols_text, encoding="utf-8")
    (output_dir / "constants.txt").write_text(result.constants_text, encoding="utf-8")
    (output_dir / "errors.txt").write_text(result.errors_text, encoding="utf-8")
    return result


def lex_text(source_text: str) -> CompileResult:
    """只做词法分析，用于实验一单独演示。"""
    lexer = Lexer(source_text, from_text=True)
    while True:
        token = lexer.scan()
        if token.type == TokenType.TK_EOF:
            break
    tokens_text = "\n".join(
        token_output_line(token) for token in lexer.tokens if token.type != TokenType.TK_EOF
    )
    if tokens_text:
        tokens_text += "\n"
    symbols_text = lexer.format_identifier_table()
    constants_text = lexer.format_constant_table()
    errors_text = "\n".join(lexer.errors) + ("\n" if lexer.errors else "No errors.\n")
    return CompileResult(
        ok=not lexer.errors,
        tokens_text=tokens_text,
        parse_text="词法分析模式：未执行语法分析。\n",
        parse_tree_text="词法分析模式：未构建语法树。\n",
        tac_text="词法分析模式：未生成三地址代码。\n",
        symbols_text=symbols_text,
        constants_text=constants_text,
        errors_text=errors_text,
    )


def lex_file(input_path: str | Path, output_dir: str | Path = "output") -> CompileResult:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result = lex_text(input_path.read_text(encoding="utf-8"))
    (output_dir / "tokens.txt").write_text(result.tokens_text, encoding="utf-8")
    (output_dir / "parse.txt").write_text(result.parse_text, encoding="utf-8")
    (output_dir / "parse_tree.txt").write_text(result.parse_tree_text, encoding="utf-8")
    (output_dir / "tac.txt").write_text(result.tac_text, encoding="utf-8")
    (output_dir / "symbols.txt").write_text(result.symbols_text, encoding="utf-8")
    (output_dir / "constants.txt").write_text(result.constants_text, encoding="utf-8")
    (output_dir / "errors.txt").write_text(result.errors_text, encoding="utf-8")
    return result
