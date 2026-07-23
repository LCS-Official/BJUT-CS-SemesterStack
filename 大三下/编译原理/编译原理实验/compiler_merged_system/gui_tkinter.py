# -*- coding: utf-8 -*-
"""标准库 Tkinter GUI：无需安装额外依赖，适合验收演示。"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.pipeline import compile_file, compile_text

SAMPLE_PROGRAM = """while (a3+15)>0xa do
if x2 = 07 then
while y<z do
y = x * y / z;
c=b*c+d;
a=6.2+a*0X88.80;
my_var = c / 01;
"""


class CompilerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("编译原理实验 1~3 合并系统")
        self.geometry("1200x760")
        self.current_file: Path | None = None
        self._build_ui()
        self.source.insert("1.0", SAMPLE_PROGRAM)

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=8)
        top.pack(fill=tk.X)
        ttk.Button(top, text="打开 input.txt", command=self.open_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="保存源程序", command=self.save_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="填入老师样例", command=self.load_sample).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="编译并生成输出文件", command=self.compile_to_files).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="仅在界面编译", command=self.compile_in_memory).pack(side=tk.LEFT, padx=4)

        pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        left = ttk.Frame(pane)
        pane.add(left, weight=1)
        ttk.Label(left, text="源程序 input.txt").pack(anchor=tk.W)
        self.source = tk.Text(left, wrap=tk.NONE, font=("Consolas", 12))
        self.source.pack(fill=tk.BOTH, expand=True)

        right = ttk.Frame(pane)
        pane.add(right, weight=1)
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.outputs: dict[str, tk.Text] = {}
        for name in ["tokens.txt", "parse.txt", "parse_tree.txt", "tac.txt", "symbols.txt", "constants.txt", "errors.txt"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)
            text = tk.Text(frame, wrap=tk.NONE, font=("Consolas", 11))
            text.pack(fill=tk.BOTH, expand=True)
            self.outputs[name] = text

    def open_file(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not filename:
            return
        self.current_file = Path(filename)
        self.source.delete("1.0", tk.END)
        self.source.insert("1.0", self.current_file.read_text(encoding="utf-8"))

    def save_file(self) -> None:
        if self.current_file is None:
            filename = filedialog.asksaveasfilename(defaultextension=".txt", initialfile="input.txt")
            if not filename:
                return
            self.current_file = Path(filename)
        self.current_file.write_text(self.source.get("1.0", tk.END).rstrip() + "\n", encoding="utf-8")
        messagebox.showinfo("保存成功", f"已保存到：{self.current_file}")

    def load_sample(self) -> None:
        self.source.delete("1.0", tk.END)
        self.source.insert("1.0", SAMPLE_PROGRAM)

    def compile_in_memory(self) -> None:
        result = compile_text(self.source.get("1.0", tk.END))
        self._show_result(result)

    def compile_to_files(self) -> None:
        root = Path.cwd()
        input_path = root / "input.txt"
        output_dir = root / "output"
        input_path.write_text(self.source.get("1.0", tk.END).rstrip() + "\n", encoding="utf-8")
        result = compile_file(input_path, output_dir)
        self._show_result(result)
        messagebox.showinfo("编译完成", "已在 output/ 下生成 tokens.txt、parse.txt、parse_tree.txt、tac.txt、symbols.txt、constants.txt、errors.txt")

    def _show_result(self, result) -> None:
        mapping = {
            "tokens.txt": result.tokens_text,
            "parse.txt": result.parse_text,
            "parse_tree.txt": result.parse_tree_text,
            "tac.txt": result.tac_text,
            "symbols.txt": result.symbols_text,
            "constants.txt": result.constants_text,
            "errors.txt": result.errors_text,
        }
        for name, content in mapping.items():
            text = self.outputs[name]
            text.delete("1.0", tk.END)
            text.insert("1.0", content)


if __name__ == "__main__":
    CompilerGUI().mainloop()
