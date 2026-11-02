@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%CD%\src
"%CD%\.venv\Scripts\python.exe" tools\capture_viewer.py --session main_s4 --queue captures\kit\queue_main_s4.json --incoming captures\incoming\main_s4_retake --seqs 400
pause
