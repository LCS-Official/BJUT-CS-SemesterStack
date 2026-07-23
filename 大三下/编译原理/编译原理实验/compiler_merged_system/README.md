# 编译原理实验 1~3 合并系统

本项目把“词法分析器、语法分析器、语法制导三地址代码生成器”合并为一个完整的小型编译前端系统。

系统流程：

```text
input.txt
  -> Lexer.scan() 词法分析，输出 output/tokens.txt
  -> Parser 递归下降语法分析，输出 output/parse.txt
  -> CodeGenerator 三地址代码生成，输出 output/tac.txt
  -> 错误信息输出 output/errors.txt
```

## 运行方式

### 1. 命令行运行

```bash
python main.py input.txt -o output

# 只演示实验一词法分析
python main.py tests/inputs/01_lexer.txt -o output --tokens-only
```

Windows 可以直接双击：

```text
run_cli.bat
```

### 2. 图形界面运行

无需额外依赖的 Tkinter GUI：

```bash
python gui_tkinter.py
```

也可双击：

```text
run_gui_tkinter.bat
```

可选 PyQt6 GUI：

```bash
pip install PyQt6
python gui_pyqt6.py
```

### 3. 生成 exe / 可运行程序包

指导书要求提交可运行程序包，且启动文件名形如：

```text
***学院20**年第X组.exe
```

本项目已经把 `Tkinter` 图形界面版设为正式启动文件，默认名称为：

```text
计算机学院2026年第X组.exe
```

打包命令：

```text
build_exe.bat
```

如果已知实际组号，可以直接写：

```text
build_exe.bat 3
```

此时会生成：

- `release/计算机学院2026年第3组/计算机学院2026年第3组.exe`：正式启动文件
- `release/计算机学院2026年第3组/计算机学院2026年第3组_命令行.exe`：命令行版
- `release/计算机学院2026年第3组_可运行程序包.zip`：可直接提交的压缩包

说明：

- `build_exe.bat` 会调用当前 Python 环境中的 `PyInstaller`。
- 若本机尚未安装 `PyInstaller`，脚本会自动执行 `python -m pip install pyinstaller`。
- 验收演示建议直接双击图形界面版启动文件。

## 支持的语言结构

赋值语句：

```text
x = a + b;
```

if 语句：

```text
if a > b then x = 1;
```

if-else 语句：

```text
if a > b then x = 1 else x = 2;
```

while 语句：

```text
while a < b do a = a + 1;
```

复合语句：

```text
{
    x = 1;
    y = 2;
};
```

## 项目结构

```text
compiler_merged_system/
├─ main.py                  命令行入口
├─ gui_tkinter.py            标准库 GUI，演示推荐
├─ gui_pyqt6.py              可选 PyQt6 GUI
├─ input.txt                 默认输入文件
├─ output/                   编译输出目录
├─ src/
│  ├─ token_defs.py          Token 类型、Token 结构
│  ├─ lexer.py               词法分析器 Lexer.scan()
│  ├─ parser.py              递归下降语法分析器 Parser
│  ├─ codegen.py             三地址代码生成器
│  └─ pipeline.py            完整编译流程封装
├─ tests/
│  ├─ inputs/                典型输入
│  └─ outputs/               已生成的典型输出
└─ docs/                     合并要求、分工、PPT/报告提纲
```

## 输出文件

- `tokens.txt`：Token 序列，格式为 `TOKEN 属性`。
- `parse.txt`：递归下降分析过程和接受/拒绝结果。
- `tac.txt`：三地址代码序列。
- `errors.txt`：词法/语法错误定位；无错误时输出 `No errors.`。

## 组长集成口径

本系统不是完整 C 编译器，而是“简单语言 -> 三地址代码”的编译前端。演示时重点说明三个实验如何通过统一 Token、统一接口和统一输出文件合并成完整系统。

## 2026-06-05 更新：增强 parse.txt 展示

`parse.txt` 已改为两栏输出：

```txt
产生式                    | 当前源程序中的真实含义 / 属性值
C -> E relop E             | C => (a3 + 15) > 10; 真->L1, 假->L2
F -> int16                 | F => 10，源程序写作 0xa
S -> id = E                | S => c = b * c + d
```

左栏仍然保留实验要求中的产生式推导；右栏用于验收演示，说明当前的 `S / C / E / T / F` 在源程序中实际代表哪一段内容，以及表达式生成三地址代码时对应的 `place`。

## 拓展版说明

本拓展版保留 `parse.txt` 两栏解释与 `parse_tree.txt` 缩进语法树，并新增：REAL10/REAL8/REAL16、拓展标识符、symbols.txt、constants.txt、常量除零语义检查。详见 `docs/拓展功能说明.md`。
