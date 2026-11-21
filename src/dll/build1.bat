@echo off
rem build1.bat x86 classic / build1.bat x64 dc
cd /d "%~dp0"
if "%1"=="x86" (
  call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars32.bat" >nul 2>nul
  set DEF=
  set MH=
) else (
  call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul 2>nul
  set DEF=/DWL2DC
  set MH=minhook\src\hook.c minhook\src\buffer.c minhook\src\trampoline.c minhook\src\hde\hde64.c
)
set OUT=..\..\build\%2
rc /nologo %DEF% /fo %OUT%\wl2jp.res wl2jp.rc || exit /b 1
cl /nologo /O2 /MT /W3 /utf-8 /LD /D_CRT_SECURE_NO_WARNINGS %DEF% /Fo%OUT%\ proxy.c wl2jp.c test.c lz4.c %MH% %OUT%\wl2jp.res /Fe%OUT%\version.dll /link /DEF:version.def kernel32.lib user32.lib dxguid.lib || exit /b 1
