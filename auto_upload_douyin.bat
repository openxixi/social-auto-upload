@echo off
chcp 65001 >nul

echo ============================================================
echo 激活 Conda 环境: social-auto-upload
echo ============================================================
call conda activate social-auto-upload
if %errorlevel% neq 0 (
    echo ✗ Conda 环境激活失败
    pause
    exit /b 1
)
echo ✓ Conda 环境已激活
echo.

echo ============================================================
echo 清理旧文件
echo ============================================================
if exist ".\videos\tmp.mp4" (
    del /F /Q ".\videos\tmp.mp4"
    echo ✓ 已删除旧的 tmp.mp4
)
if exist ".\videos\tmp.jpg" (
    del /F /Q ".\videos\tmp.jpg"
    echo ✓ 已删除旧的 tmp.jpg
)
if exist ".\output_video\date*" (
    del /F /Q ".\output_video\date*"
    echo ✓ 已删除旧的 date*
)

echo ✓ 清理完成
echo.

echo ============================================================
echo 抖音视频自动上传流程
echo 开始时间: %date% %time%
echo ============================================================
echo.

echo ============================================================
echo 步骤1: 为图片添加日期
echo ============================================================
python add_date_to_image.py ".\videos_pre\tmp.jpg" -o ".\videos\tmp.jpg"
if %errorlevel% neq 0 (
    echo ✗ 步骤1失败
    pause
    exit /b 1
)
echo ✓ 步骤1完成
echo.

echo ============================================================
echo 步骤2: 生成日期文件
echo ============================================================
python generate_date.py
if %errorlevel% neq 0 (
    echo ✗ 步骤2失败
    pause
    exit /b 1
)
echo ✓ 步骤2完成
echo.

echo ============================================================
echo 步骤3: 生成数字人视频
echo ============================================================
python .\workflow.py "D:\workspace\github\openyixi\social-auto-upload\output_video\date.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\4_zyx_ttxd.jpg" .\output_video\ --prompt "男人正在说话"
if %errorlevel% neq 0 (
    echo ✗ 步骤3失败
    pause
    exit /b 1
)
echo ✓ 步骤3完成
echo.

echo ============================================================
echo 步骤4: 合并视频
echo ============================================================
python .\merge_videos.py "D:\workspace\github\openyixi\social-auto-upload\videos_pre\tmp.mp4" "D:\workspace\github\openyixi\social-auto-upload\output_video\date.mp4" -o .\videos\tmp.mp4
if %errorlevel% neq 0 (
    echo ✗ 步骤4失败
    pause
    exit /b 1
)
echo ✓ 步骤4完成
echo.

echo ============================================================
echo 步骤5: 上传视频到抖音
echo ============================================================
python upload_video_to_douyin.py
if %errorlevel% neq 0 (
    echo ✗ 步骤5失败
    pause
    exit /b 1
)
echo ✓ 步骤5完成
echo.

echo ============================================================
echo 🎉 所有步骤执行成功！
echo 结束时间: %date% %time%
echo ============================================================
pause
