# -*- coding: utf-8 -*-
"""实验三：三地址代码生成器。"""
from __future__ import annotations


class CodeGenerator:
    def __init__(self) -> None:
        self.temp_count = 0
        self.label_count = 0
        self.lines: list[str] = []

    def newtemp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def newlabel(self) -> str:
        label = f"L{self.label_count}"
        self.label_count += 1
        return label

    def emit(self, code: str) -> None:
        self.lines.append(code)

    def text(self) -> str:
        return "\n".join(self.lines) + ("\n" if self.lines else "")
