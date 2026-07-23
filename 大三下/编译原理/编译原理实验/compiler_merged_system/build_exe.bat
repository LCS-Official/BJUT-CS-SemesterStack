@echo off
chcp 65001 >nul
setlocal

set GROUP=%~1
if "%GROUP%"=="" set GROUP=X

python build_release.py --group %GROUP%
if errorlevel 2 (
    echo 未检测到 PyInstaller，正在安装到当前 Python 环境...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo PyInstaller 安装失败，请检查网络或 Python 环境后重试。
        pause
        exit /b 1
    )
    python build_release.py --group %GROUP%
)

if errorlevel 1 (
    echo 打包失败，请查看上面的错误信息。
    pause
    exit /b 1
)

echo.
echo 打包完成，请查看 release 目录。
pause
