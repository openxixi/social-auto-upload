# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================================"
Write-Host "激活 Conda 环境: social-auto-upload"
Write-Host "============================================================"
conda activate social-auto-upload
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Conda 环境激活失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ Conda 环境已激活" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================"
Write-Host "清理旧文件"
Write-Host "============================================================"
if (Test-Path ".\videos\tmp.mp4") {
    Remove-Item -Force ".\videos\tmp.mp4"
    Write-Host "✓ 已删除旧的 tmp.mp4" -ForegroundColor Green
}
if (Test-Path ".\videos\tmp.jpg") {
    Remove-Item -Force ".\videos\tmp.jpg"
    Write-Host "✓ 已删除旧的 tmp.jpg" -ForegroundColor Green
}
if (Test-Path ".\output_video\date*") {
    Remove-Item -Force ".\output_video\date*"
    Write-Host "✓ 已删除旧的 date*" -ForegroundColor Green
}
Write-Host "✓ 清理完成" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================"
Write-Host "抖音视频自动上传流程"
Write-Host "开始时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================================"
Write-Host ""

# 步骤1: 为图片添加日期
Write-Host "============================================================"
Write-Host "步骤1: 为图片添加日期"
Write-Host "============================================================"
python add_date_to_image.py ".\videos_pre\tmp.jpg" -o ".\videos\tmp.jpg"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 步骤1失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ 步骤1完成" -ForegroundColor Green
Write-Host ""

# 步骤2: 生成日期文件
Write-Host "============================================================"
Write-Host "步骤2: 生成日期文件"
Write-Host "============================================================"
python generate_date.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 步骤2失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ 步骤2完成" -ForegroundColor Green
Write-Host ""

# 步骤3: 生成数字人视频
Write-Host "============================================================"
Write-Host "步骤3: 生成数字人视频"
Write-Host "============================================================"
python .\workflow.py "D:\workspace\github\openyixi\social-auto-upload\output_video\date.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\4_zyx_ttxd.jpg" .\output_video\ --prompt "男人正在说话"
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 步骤3失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ 步骤3完成" -ForegroundColor Green
Write-Host ""

# 步骤4: 合并视频
Write-Host "============================================================"
Write-Host "步骤4: 合并视频"
Write-Host "============================================================"
python .\merge_videos.py "D:\workspace\github\openyixi\social-auto-upload\videos_pre\tmp.mp4" "D:\workspace\github\openyixi\social-auto-upload\output_video\date.mp4" -o .\videos\tmp.mp4
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 步骤4失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ 步骤4完成" -ForegroundColor Green
Write-Host ""

# 步骤5: 上传视频到抖音
Write-Host "============================================================"
Write-Host "步骤5: 上传视频到抖音"
Write-Host "============================================================"
python upload_video_to_douyin.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 步骤5失败" -ForegroundColor Red
    Read-Host "按任意键退出"
    exit 1
}
Write-Host "✓ 步骤5完成" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================"
Write-Host "🎉 所有步骤执行成功！" -ForegroundColor Green
Write-Host "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================================"
Read-Host "按任意键退出"
