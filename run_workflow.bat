@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d %~dp0
call .\.venv\Scripts\python.exe .\workflow.py "D:\video_workspace\source_txt\2_我要做什么.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --vram-swap-coef 40
endlocal