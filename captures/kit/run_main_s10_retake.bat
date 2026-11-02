@echo off
chcp 65001 >nul
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
set PYTHONPATH=%CD%\src
set HF_HUB_OFFLINE=1
if not exist "captures\incoming\main_s10_retake" mkdir "captures\incoming\main_s10_retake"
echo ============================================================
echo  s10 补拍：仅 seq 963 与 seq 996（其余 98 张已通过）
echo  963 是雪景（整片白色），996 是白衣人像，两处高光超出内容
echo  操作：主界面按 R，依次拍 963、996
echo        每张先点屏幕对焦，把曝光滑块往下调一格（约 -0.3 EV），
echo        再按空格；两张拍完自动退出
echo  拍完照片复制到 captures\incoming\main_s10_retake\
echo ============================================================
echo.
".venv\Scripts\python.exe" tools\capture_viewer.py --session main_s10 --seqs 963,996
echo.
echo 拍完后请把两张照片复制到 captures\incoming\main_s10_retake\
pause
