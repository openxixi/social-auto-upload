# 视频自动加字幕工具 - PowerShell快捷脚本
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = 1

# ========== 配置区域 ==========
# 根据你的实际情况修改以下路径

# 视频文件路径
$VIDEO_FILE = ".\output_video\WanVideo2_1_InfiniteTalk_00001-audio.mp4_1769601898.mp4_trim.mp4"

# 文本文件目录（自动匹配）或指定文本文件
$TEXT_DIR = "D:\video_workspace\source_txt"
# $TEXT_FILE = "D:\video_workspace\source_txt\2_我要做什么.txt"  # 取消注释以指定具体文件

# 输出视频路径（留空则自动生成）
$OUTPUT_FILE = ""

# 字幕样式
$FONT_SIZE = 28
$FONT_COLOR = "white"

# 断句设置
$MAX_LENGTH = 20  # 每句最大字符数
$SPEED = 5        # 阅读速度（字/秒）

# 强制重新生成（不跳过已存在的文件）
$FORCE = $false

# ==============================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  视频自动加字幕工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "视频文件: $VIDEO_FILE" -ForegroundColor Gray

# 构建命令参数
$args = @(
    "$VIDEO_FILE"
)

if ($TEXT_FILE) {
    $args += "--text", "$TEXT_FILE"
    Write-Host "文本文件: $TEXT_FILE" -ForegroundColor Gray
} else {
    $args += "--text-dir", "$TEXT_DIR"
    Write-Host "文本目录: $TEXT_DIR (自动匹配)" -ForegroundColor Gray
}

if ($OUTPUT_FILE) {
    $args += "-o", "$OUTPUT_FILE"
}

$args += "--fontsize", $FONT_SIZE
$args += "--fontcolor", $FONT_COLOR
$args += "--max-length", $MAX_LENGTH
$args += "--speed", $SPEED

if ($FORCE) {
    $args += "--force"
}

Write-Host ""
& .\.venv\Scripts\python.exe .\add_subtitle_simple.py @args

Write-Host ""
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ 处理完成！" -ForegroundColor Green
} else {
    Write-Host "✗ 处理失败" -ForegroundColor Red
}

Write-Host ""
Read-Host "按回车键退出"
