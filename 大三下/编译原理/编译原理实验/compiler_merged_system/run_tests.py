# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

from src.pipeline import compile_file, lex_file


def main() -> None:
    root = Path(__file__).parent
    input_dir = root / "tests" / "inputs"
    output_root = root / "tests" / "outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    for input_file in sorted(input_dir.glob("*.txt")):
        out_dir = output_root / input_file.stem
        if input_file.name.startswith("01_"):
            result = lex_file(input_file, out_dir)
        else:
            result = compile_file(input_file, out_dir)
        print(f"{input_file.name}: {'OK' if result.ok else 'HAS ERRORS'} -> {out_dir}")


if __name__ == "__main__":
    main()
