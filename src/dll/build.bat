@echo off
cd /d "%~dp0"
set T=
set B=..\..\build
if "%1"=="test" (
  set T=test
  set B=..\..\build\test
)
if not exist %B%\classic mkdir %B%\classic
if not exist %B%\dc mkdir %B%\dc
cmd /c "%~dp0build1.bat" x86 classic %T% || exit /b 1
cmd /c "%~dp0build1.bat" x64 dc %T% || exit /b 1
