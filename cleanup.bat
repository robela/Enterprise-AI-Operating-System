@echo off
REM Remove corrupted files from repository
cd /d "c:\Code\Enterprise-AI-Operating-System\Enterprise-AI-Operating-System"

echo Removing corrupted files...
echo.

REM Remove files with special characters and spaces
for /f "delims=" %%A in ('dir /b /s | findstr /R "pan initialization"') do (
    echo Removing: %%A
    del "%%A" /F /Q 2>nul
)

REM Remove single letter files at root
del "e" /F /Q 2>nul
del "h" /F /Q 2>nul
del "t" /F /Q 2>nul

REM Remove other corrupted files
del "tatus" /F /Q 2>nul
del "ubprocess" /F /Q 2>nul

echo.
echo Cleanup complete. Running git status...
echo.

git status --short

echo.
echo Now try: git add .
pause
