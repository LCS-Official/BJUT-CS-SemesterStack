# -*- coding: utf-8 -*-
"""命令行入口。"""
from __future__ import annotations

import argparse
from pathlib import Path

from src.pipeline import compile_file, lex_file


def main() -> int:
    parser = argparse.ArgumentParser(description="编译原理实验 1~3 合并系统：词法分析、语法分析、三地址代码生成")
    parser.add_argument("input", nargs="?", default="input.txt", help="源程序文件，默认 input.txt")
    parser.add_argument("-o", "--output", default="output", help="输出目录，默认 output")
    parser.add_argument("--tokens-only", action="store_true", help="只执行词法分析，用于实验一演示")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"找不到输入文件：{input_path}")
        return 2

    result = lex_file(input_path, args.output) if args.tokens_only else compile_file(input_path, args.output)
    print("已生成：")
    print(f"  {Path(args.output) / 'tokens.txt'}")
    print(f"  {Path(args.output) / 'parse.txt'}")
    print(f"  {Path(args.output) / 'parse_tree.txt'}")
    print(f"  {Path(args.output) / 'tac.txt'}")
    print(f"  {Path(args.output) / 'symbols.txt'}")
    print(f"  {Path(args.output) / 'constants.txt'}")
    print(f"  {Path(args.output) / 'errors.txt'}")
    if args.tokens_only:
        print("词法分析结果：" + ("通过" if result.ok else "存在错误，请查看 errors.txt"))
    else:
        print("语法分析结果：" + ("通过" if result.ok else "存在错误，请查看 errors.txt"))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
