@echo off
chcp 65001 >nul
title 代理选型 实拍 s7 补拍 2 张
echo.
echo  s7 补拍 2 张：序 605、643（曝光过度，白色背景被压成纯白）
echo.
echo  操作：
echo   1) 双击后窗口会显示第 1 张（序 605），右下角显示序号。
echo   2) 点屏幕对焦后，把对焦框旁的小太阳往下拖一点（约 -0.3 EV），
echo      看到白色背景不再刺眼、但仍保留层次再按快门。
echo   3) 拍完把 2 张照片复制到 captures\incoming\main_s7_retake\
echo.
echo  位置、距离、屏幕亮度都不要动；只调曝光。
echo.
pause
set PKG=%~dp0..\..
set PY=%PKG%\.venv\Scripts\python.exe
set PYTHONPATH=%PKG%\src
set PYTHONIOENCODING=utf-8
"%PY%" "%PKG%\tools\capture_viewer.py" --queue "%PKG%\captures\kit\queue_main_s7.json" --session main_s7 --seqs 605,643
pause
