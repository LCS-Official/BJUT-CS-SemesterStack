@echo off
REM ================================================================
REM  编译原理实验二：语法分析程序 - 编译脚本 (Windows)
REM  使用 win_flex 和 win_bison 生成词法和语法分析器
REM ================================================================

setlocal enabledelayedexpansion

REM 设置工具路径
set FLEX="c:\Users\龙绍恒\.trae-cn\work\6a1cf4b5ffd8a08b3b1df424\win_flex_bison\win_flex.exe"
set BISON="c:\Users\龙绍恒\.trae-cn\work\6a1cf4b5ffd8a08b3b1df424\win_flex_bison\win_bison.exe"

echo ========================================
echo  编译原理实验二：语法分析程序
echo  开始编译...
echo ========================================

REM 步骤1: 用 Bison 生成语法分析器
echo.
echo [1/3] 生成语法分析器 (Bison)...
%bison% -d part2_tree.y
if errorlevel 1 (
    echo [错误] Bison 生成失败！
    exit /b 1
)
echo [完成] 生成 part2_tree.tab.c 和 part2_tree.tab.h

REM 步骤2: 用 Flex 生成词法分析器
echo.
echo [2/3] 生成词法分析器 (Flex)...
%flex% -o part2_tree.lex.c part2_tree.l
if errorlevel 1 (
    echo [错误] Flex 生成失败！
    exit /b 1
)
echo [完成] 生成 part2_tree.lex.c

REM 步骤3: 用 GCC 编译链接
echo.
echo [3/3] 编译链接 (GCC)...
gcc -o tree.exe part2_tree.tab.c part2_tree.lex.c part2funcs.c -Wall
if errorlevel 1 (
    echo [错误] GCC 编译失败！
    exit /b 1
)
echo [完成] 生成 tree.exe

echo.
echo ========================================
echo  编译成功！可执行文件: tree.exe
echo ========================================
echo.
echo 使用方法:
echo   tree.exe               (使用默认 input.txt)
echo   tree.exe test.txt      (指定输入文件)
echo.
endlocal
