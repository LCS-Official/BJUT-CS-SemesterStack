# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BUILD_ROOT = ROOT / "build"
DIST_ROOT = BUILD_ROOT / "dist"
WORK_ROOT = BUILD_ROOT / "pyinstaller"
SPEC_ROOT = BUILD_ROOT / "spec"
RELEASE_ROOT = ROOT / "release"


def pyinstaller_available() -> bool:
    return importlib.util.find_spec("PyInstaller") is not None


def run_pyinstaller(arguments: list[str]) -> None:
    command = [sys.executable, "-m", "PyInstaller", *arguments]
    subprocess.run(command, cwd=ROOT, check=True)


def build_executables(gui_name: str, cli_name: str) -> None:
    common = [
        "--noconfirm",
        "--clean",
        f"--distpath={DIST_ROOT}",
        f"--workpath={WORK_ROOT}",
        f"--specpath={SPEC_ROOT}",
    ]
    run_pyinstaller(
        common
        + [
            "--onefile",
            "--windowed",
            f"--name={gui_name}",
            "gui_tkinter.py",
        ]
    )
    run_pyinstaller(
        common
        + [
            "--onefile",
            "--console",
            f"--name={cli_name}",
            "main.py",
        ]
    )


def prepare_release(gui_name: str, cli_name: str, year: str, academy: str, group: str) -> tuple[Path, Path]:
    package_dir = RELEASE_ROOT / gui_name
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "output").mkdir(exist_ok=True)

    gui_exe = DIST_ROOT / f"{gui_name}.exe"
    cli_exe = DIST_ROOT / f"{cli_name}.exe"
    shutil.copy2(gui_exe, package_dir / gui_exe.name)
    shutil.copy2(cli_exe, package_dir / cli_exe.name)
    shutil.copy2(ROOT / "input.txt", package_dir / "input.txt")

    sample_input = ROOT / "tests" / "inputs" / "05_teacher_sample.txt"
    if sample_input.exists():
        shutil.copy2(sample_input, package_dir / "示例输入_教师样例.txt")

    shutil.copy2(ROOT / "README.md", package_dir / "项目说明_README.md")

    instructions = textwrap.dedent(
        f"""\
        编译原理实验可运行程序包

        启动文件：
        1. {gui_name}.exe    —— 图形界面版，建议验收时双击运行
        2. {cli_name}.exe    —— 命令行版，可在终端中运行

        当前配置：
        - 学院：{academy}
        - 年份：{year}
        - 组号：{group}

        使用说明：
        1. 双击 {gui_name}.exe。
        2. 可直接编辑界面中的源程序，或打开同目录下的 input.txt。
        3. 点击“编译并生成输出文件”后，会在当前目录的 output 文件夹下生成：
           tokens.txt / parse.txt / parse_tree.txt / tac.txt / symbols.txt / constants.txt / errors.txt

        命令行版示例：
        {cli_name}.exe input.txt -o output

        典型样例：
        - input.txt
        - 示例输入_教师样例.txt
        """
    )
    (package_dir / "运行说明.txt").write_text(instructions, encoding="utf-8")

    zip_path = RELEASE_ROOT / f"{gui_name}_可运行程序包.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in package_dir.rglob("*"):
            archive.write(path, Path(package_dir.name) / path.relative_to(package_dir))
    return package_dir, zip_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="构建编译原理实验可运行程序包")
    parser.add_argument("--group", default="X", help="组号，例如 3")
    parser.add_argument("--year", default="2026", help="年份，默认 2026")
    parser.add_argument("--academy", default="计算机学院", help="学院名称，默认 计算机学院")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not pyinstaller_available():
        print("未检测到 PyInstaller。")
        print("可执行以下命令安装：")
        print("  python -m pip install pyinstaller")
        return 2

    gui_name = f"{args.academy}{args.year}年第{args.group}组"
    cli_name = f"{gui_name}_命令行"

    build_executables(gui_name, cli_name)
    package_dir, zip_path = prepare_release(gui_name, cli_name, args.year, args.academy, str(args.group))

    print("构建完成：")
    print(f"  GUI 启动文件：{package_dir / f'{gui_name}.exe'}")
    print(f"  CLI 启动文件：{package_dir / f'{cli_name}.exe'}")
    print(f"  发布目录：{package_dir}")
    print(f"  发布压缩包：{zip_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
