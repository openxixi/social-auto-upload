# 设置UTF-8编码
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'

# 设置工作目录
Set-Location -Path $PSScriptRoot

# 定义文件路径
$VIDEO_FILE = ".\output_video\4_替天行道.mp4"
$TEXT_FILE = "D:\video_workspace\source_txt\4_替天行道.txt"
$WHISPER_SRT = ".\output_video\4_替天行道.srt"
$CORRECTED_SRT = ".\output_video\4_替天行道_corrected.srt"

Write-Host "========================================"
Write-Host "Whisper AI字幕生成工具"
Write-Host "========================================"
Write-Host ""
Write-Host "步骤1: 使用Whisper识别语音并生成字幕"
Write-Host "========================================"

# 执行Whisper字幕生成
& python ".\whisper_to_srt.py" $VIDEO_FILE -o $WHISPER_SRT --model base --language zh --max-chars 13

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "字幕识别失败" -ForegroundColor Red
    Read-Host "按Enter键继续"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "步骤2: 使用原文本矫正字幕"
Write-Host "========================================"

# 使用原文本矫正字幕
& python ".\correct_subtitle.py" $WHISPER_SRT $TEXT_FILE -o $CORRECTED_SRT --max-chars 13

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "字幕矫正失败，将使用Whisper原始字幕" -ForegroundColor Yellow
    $CORRECTED_SRT = $WHISPER_SRT
}

Write-Host ""
Write-Host "========================================"
Write-Host "步骤3: 将字幕添加到视频"
Write-Host "========================================"
Write-Host ""

# 执行字幕添加
& python ".\add_subtitle_to_video.py" $VIDEO_FILE $CORRECTED_SRT -o ".\output_video\最终视频.mp4" --fontsize 14 --fontcolor yellow

Write-Host ""
Write-Host "========================================"
if ($LASTEXITCODE -eq 0) {
    Write-Host "处理完成" -ForegroundColor Green
} else {
    Write-Host "处理失败" -ForegroundColor Red
}
Write-Host "========================================"
Write-Host ""

Read-Host "按Enter键继续"
