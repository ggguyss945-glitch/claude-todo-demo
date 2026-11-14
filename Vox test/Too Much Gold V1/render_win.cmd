@echo off
rem Windows version of render_loop.sh: re-runs render.js until it finishes. render.js exits with 75
rem when it restarts itself to free memory; finished seconds are kept and skipped.
:loop
node --expose-gc "%~dp0render.js" %*
if %ERRORLEVEL%==75 goto loop
