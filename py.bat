@echo off
setlocal enabledelayedexpansion
setlocal enableextensions

REM Clumsy workaround to make `nox`s python discovery
REM work on Windows systems without py (python launcher),
REM such as Anaconda installations on Windows.
REM NOTE: Does NOT replace python launcher for other purposes!

REM Check for presence of py.exe, so that this batch file
REM does not break a working python launcher in the path.
where py.exe 2>NUL
if %errorlevel%==0 (
  py.exe %*
) else (

  if "%1"=="" (
    ECHO ERROR: py.bat missing parameter -VERSION 1>&2
    exit /b 1
  )

  ECHO No py.exe found, trying to check whether python in the PATH satisfies %1 1>&2
  set par=%1

  REM Remove leading hyphen from version parameter,
  REM e.g. "-3.6" becomes "3.6"
  set ver=!par:~1,3!

  REM Get output of (first) python interpreter in path
  FOR /F "tokens=*" %%L in ('python --version') do (SET output=%%L)

  ECHO Requiring !ver!, found "!output!" 1>&2

  REM Check three-character versions like 2.7, 3.4:
  set output=!output:~0,10!

  ECHO "!output!"=="Python !ver!" 1>&2
  if "!output!"=="Python !ver!" (
    python %2 %3 %4 %5 %6 %7 %8 %9
    exit /b 0
  )

  REM Also try one-character versions like 2, 3
  set output=!output:~0,8!
  ECHO "!output!"=="Python !ver!" 1>&2
  if "!output!"=="Python !ver!" (
    python %2 %3 %4 %5 %6 %7 %8 %9
    exit /b 0
  )

  ECHO py.bat could not find a matching python interpreter 1>&2
  exit /b 2

)
