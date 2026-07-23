@echo off
setlocal
set PYTHON_EXE=python

if "%~1"=="" (
  %PYTHON_EXE% "%~dp0task3_codegen.py" "%~dp0input.txt" "%~dp0output.txt"
) else if "%~2"=="" (
  %PYTHON_EXE% "%~dp0task3_codegen.py" "%~1" "%~dp0output.txt"
) else (
  %PYTHON_EXE% "%~dp0task3_codegen.py" "%~1" "%~2"
)

pause
endlocal
