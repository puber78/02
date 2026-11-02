@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%CD%\src
set HF_HUB_OFFLINE=1
if not exist "captures\incoming\main_s9_retake" mkdir "captures\incoming\main_s9_retake"
echo ============================================================
echo  s9 补拍：仅 seq 858（其他 99 张已通过）
echo  seq 858 原片高光超出内容本身 6.4 个百分点（上限 5）
echo  操作：主界面按 R，只拍 858；拍时点一下屏幕对焦，
echo        把曝光滑块往下调一格（-0.3 EV 左右），再按空格。
echo  拍完照片复制到 captures\incoming\main_s9_retake\
echo  （会自动先显示 seq 858，拍完自动退出）
echo ============================================================
echo.
".venv\Scripts\python.exe" tools\capture_viewer.py --session main_s9 --seqs 858
echo.
echo 拍完后请把照片复制到 captures\incoming\main_s9_retake\
pause
