@echo off
REM Clumsy workaround to make `nox`s python discovery
REM work on Windows systems without py (python launcher),
REM such as Anaconda installations on Windows.
REM NOTE: Does NOT replace python launcher for other purposes!

REM Check for presence of py.exe, so that this batch file
REM does not break a working python launcher in the path.
where py.exe
if errorlevel 0 (
  py.exe %*
) else (

  REM No py.exe found, trying to check whether python
  REM in the PATH satisfies the given version.
  set ver=%1

  REM Remove leading hyphen from version parameter,
  REM e.g. "-3.6" becomes "3.6"
  set ver=%ver:~1%

  REM Get output of (first) python interpreter in path
  FOR /F "tokens=*" %%L in ('python --version') do (SET output=%%L)

  REM Check three-character versions like 2.7, 3.4:
  set output=%output~0,10%
  if %output%==Python %ver% (
    python %2 %3 %4 %5 %6 %7 %8 %9
    exit 0
  ) else (

    REM Also try one-character versions like 2, 3
    set output=%output~0,8%
    if %output%==Python %ver% (
      python %2 %3 %4 %5 %6 %7 %8 %9
      exit 0
    ) else (
      echo PY.BAT COULD NOT DISCOVER PYTHON
      exit 1
    )

  )
)
