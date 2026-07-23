@echo off
cd /d "%~dp0"
echo 正在启动智能实验室预约与设备管理系统动态原型...
echo 浏览器打开：http://127.0.0.1:5050/
echo.
conda run -n csv python app.py
pause
