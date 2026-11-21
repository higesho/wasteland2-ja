@echo off
cd /d "%~dp0"
if not exist ..\..\build\classic mkdir ..\..\build\classic
if not exist ..\..\build\dc mkdir ..\..\build\dc
cmd /c "%~dp0build1.bat" x86 classic || exit /b 1
cmd /c "%~dp0build1.bat" x64 dc || exit /b 1
