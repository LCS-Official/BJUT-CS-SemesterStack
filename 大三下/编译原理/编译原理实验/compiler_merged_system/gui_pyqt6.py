# -*- coding: utf-8 -*-
"""可选 PyQt6 GUI：需要先安装 PyQt6。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (
        QApplication, QFileDialog, QHBoxLayout, QMainWindow, QMessageBox,
        QPushButton, QTabWidget, QTextEdit, QVBoxLayout, QWidget
    )
except ImportError as exc:
    print("未安装 PyQt6。请先运行：pip install PyQt6")
    raise SystemExit(1) from exc

from src.pipeline import compile_file, compile_text

SAMPLE_PROGRAM = """while (a3+15)>0xa do
if x2 = 07 then
while y<z do
y = x * y / z;
c=b*c+d;
a=6.2+a*0X88.80;
my_var = c / 01;
"""


class CompilerWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("编译原理实验 1~3 合并系统 - PyQt6")
        self.resize(1200, 760)
        self.current_file: Path | None = None
        self._build_ui()
        self.source.setPlainText(SAMPLE_PROGRAM)

    def _build_ui(self) -> None:
        root = QWidget()
        main_layout = QVBoxLayout(root)

        buttons = QHBoxLayout()
        for text, slot in [
            ("打开 input.txt", self.open_file),
            ("保存源程序", self.save_file),
            ("填入老师样例", self.load_sample),
            ("编译并生成输出文件", self.compile_to_files),
            ("仅在界面编译", self.compile_in_memory),
        ]:
            button = QPushButton(text)
            button.clicked.connect(slot)
            buttons.addWidget(button)
        main_layout.addLayout(buttons)

        body = QHBoxLayout()
        self.source = QTextEdit()
        self.source.setPlaceholderText("在这里输入源程序，或打开 input.txt")
        body.addWidget(self.source, 1)

        self.tabs = QTabWidget()
        self.outputs: dict[str, QTextEdit] = {}
        for name in ["tokens.txt", "parse.txt", "parse_tree.txt", "tac.txt", "symbols.txt", "constants.txt", "errors.txt"]:
            text = QTextEdit()
            text.setReadOnly(True)
            self.outputs[name] = text
            self.tabs.addTab(text, name)
        body.addWidget(self.tabs, 1)
        main_layout.addLayout(body)
        self.setCentralWidget(root)

    def open_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "打开源程序", "", "Text files (*.txt);;All files (*.*)")
        if filename:
            self.current_file = Path(filename)
            self.source.setPlainText(self.current_file.read_text(encoding="utf-8"))

    def save_file(self) -> None:
        if self.current_file is None:
            filename, _ = QFileDialog.getSaveFileName(self, "保存源程序", "input.txt", "Text files (*.txt)")
            if not filename:
                return
            self.current_file = Path(filename)
        self.current_file.write_text(self.source.toPlainText().rstrip() + "\n", encoding="utf-8")
        QMessageBox.information(self, "保存成功", f"已保存到：{self.current_file}")

    def load_sample(self) -> None:
        self.source.setPlainText(SAMPLE_PROGRAM)

    def compile_in_memory(self) -> None:
        self._show_result(compile_text(self.source.toPlainText()))

    def compile_to_files(self) -> None:
        root = Path.cwd()
        input_path = root / "input.txt"
        output_dir = root / "output"
        input_path.write_text(self.source.toPlainText().rstrip() + "\n", encoding="utf-8")
        result = compile_file(input_path, output_dir)
        self._show_result(result)
        QMessageBox.information(self, "编译完成", "已在 output/ 下生成 tokens、parse、parse_tree、tac、symbols、constants、errors 等输出文件。")

    def _show_result(self, result) -> None:
        self.outputs["tokens.txt"].setPlainText(result.tokens_text)
        self.outputs["parse.txt"].setPlainText(result.parse_text)
        self.outputs["parse_tree.txt"].setPlainText(result.parse_tree_text)
        self.outputs["tac.txt"].setPlainText(result.tac_text)
        self.outputs["symbols.txt"].setPlainText(result.symbols_text)
        self.outputs["constants.txt"].setPlainText(result.constants_text)
        self.outputs["errors.txt"].setPlainText(result.errors_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerWindow()
    window.show()
    sys.exit(app.exec())
