@echo off
chcp 65001 >nul
title 代理选型 实拍 s6 补拍 2 张
echo.
echo  s6 补拍 2 张：序 579、584（清晰度不足）
echo.
echo  1) 先把 s6 照片全部复制到 captures\incoming\main_s6\ 后关闭浏览器？
echo     不需要：直接拍这 2 张，号码会自动跳过已拍的。
echo  2) 保持显示器、手机、三脚架位置不变；确认手机对焦（点一下屏幕中心）
echo     与曝光锁定后再按快门。
echo  3) 拍完把新照片放进 captures\incoming\main_s6_retake\，关闭窗口即可。
echo.
pause
set PKG=%~dp0..\..
set PY=%PKG%\.venv\Scripts\python.exe
set PYTHONPATH=%PKG%\src
set PYTHONIOENCODING=utf-8
"%PY%" "%PKG%\tools\capture_viewer.py" --queue "%PKG%\captures\kit\queue_main_s6.json" --session main_s6 --seqs 579,584
pause
