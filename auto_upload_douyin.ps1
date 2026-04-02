# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# 定义清理服务函数
function Clean-Services {
    Write-Host "清理后台服务..." -ForegroundColor Cyan
    
    # 清理端口 7860
    $port7860 = Get-NetTCPConnection -LocalPort 7860 -ErrorAction SilentlyContinue
    if ($port7860) {
        $processId = $port7860[0].OwningProcess
        $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
        Write-Host "  停止端口 7860 进程: $processName (PID: $processId)" -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    
    # 清理端口 7866
    $port7866 = Get-NetTCPConnection -LocalPort 7866 -ErrorAction SilentlyContinue
    if ($port7866) {
        $processId = $port7866[0].OwningProcess
        $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
        Write-Host "  停止端口 7866 进程: $processName (PID: $processId)" -ForegroundColor Yellow
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    }
    
    # 也尝试停止主进程（如果它们还在运行）
    if ($null -ne $script:process1 -and -not $script:process1.HasExited) {
        Write-Host "  停止 index-tts2 主进程 (PID: $($script:process1.Id))" -ForegroundColor Yellow
        Stop-Process -Id $script:process1.Id -Force -ErrorAction SilentlyContinue
    }
    
    if ($null -ne $script:process2 -and -not $script:process2.HasExited) {
        Write-Host "  停止 InfiniteTalk 主进程 (PID: $($script:process2.Id))" -ForegroundColor Yellow
        Stop-Process -Id $script:process2.Id -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "  ✓ 服务清理完成" -ForegroundColor Green
}

Write-Host "============================================================"
Write-Host "检查并清理端口占用"
Write-Host "============================================================"

# 检查并清理端口 7860
Write-Host "检查端口 7860..." -ForegroundColor Cyan
$port7860 = Get-NetTCPConnection -LocalPort 7860 -ErrorAction SilentlyContinue
if ($port7860) {
    $processId = $port7860[0].OwningProcess
    $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
    Write-Host "  ⚠ 端口 7860 被进程占用: $processName (PID: $processId)" -ForegroundColor Yellow
    Write-Host "  正在强制终止进程..." -ForegroundColor Cyan
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ 进程已终止" -ForegroundColor Green
} else {
    Write-Host "  ✓ 端口 7860 未被占用" -ForegroundColor Green
}

# 检查并清理端口 7866
Write-Host "检查端口 7866..." -ForegroundColor Cyan
$port7866 = Get-NetTCPConnection -LocalPort 7866 -ErrorAction SilentlyContinue
if ($port7866) {
    $processId = $port7866[0].OwningProcess
    $processName = (Get-Process -Id $processId -ErrorAction SilentlyContinue).ProcessName
    Write-Host "  ⚠ 端口 7866 被进程占用: $processName (PID: $processId)" -ForegroundColor Yellow
    Write-Host "  正在强制终止进程..." -ForegroundColor Cyan
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "  ✓ 进程已终止" -ForegroundColor Green
} else {
    Write-Host "  ✓ 端口 7866 未被占用" -ForegroundColor Green
}

Write-Host "✓ 端口检查完成" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================"
Write-Host "启动后台服务"
Write-Host "============================================================"

# 启动第一个 bat 文件 (端口 7866)
Write-Host "启动 index-tts2 服务 (端口 7866)..." -ForegroundColor Cyan
$script:process1 = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d D:\workspace\github\ml\index-tts2 && start.bat" -PassThru -WindowStyle Normal
Write-Host "✓ index-tts2 服务进程已启动 (PID: $($script:process1.Id))" -ForegroundColor Green

# 启动第二个 bat 文件 (端口 7860)
Write-Host "启动 InfiniteTalk 服务 (端口 7860)..." -ForegroundColor Cyan
$script:process2 = Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd /d D:\workspace\github\ml\InfiniteTalk-0926\InfiniteTalk && start.bat" -PassThru -WindowStyle Normal
Write-Host "✓ InfiniteTalk 服务进程已启动 (PID: $($script:process2.Id))" -ForegroundColor Green
Write-Host ""

# 等待服务启动并每 20 秒检查一次
Write-Host "等待服务启动完成..." -ForegroundColor Yellow
Write-Host "提示: AI 服务需要加载模型，可能需要 2-3 分钟" -ForegroundColor Cyan
Write-Host "提示: 可以查看弹出的命令窗口观察启动进度`n" -ForegroundColor Cyan

$totalWaitTime = 120  # 增加到 180 秒（3分钟）
$checkInterval = 20
$elapsed = 0

while ($elapsed -lt $totalWaitTime) {
    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
    
    # 检查端口状态
    $port7860Status = Get-NetTCPConnection -LocalPort 7860 -State Listen -ErrorAction SilentlyContinue
    $port7866Status = Get-NetTCPConnection -LocalPort 7866 -State Listen -ErrorAction SilentlyContinue
    
    $port7860Ready = if ($port7860Status) { "✓ 就绪" } else { "⏳ 等待中" }
    $port7866Ready = if ($port7866Status) { "✓ 就绪" } else { "⏳ 等待中" }
    
    Write-Host "  [$elapsed/$totalWaitTime 秒] 端口 7860 (InfiniteTalk): $port7860Ready | 端口 7866 (index-tts2): $port7866Ready" -ForegroundColor Cyan
    
    # 如果两个端口都已监听，提前退出等待
    if ($port7860Status -and $port7866Status) {
        Write-Host "  ✓ 两个服务都已就绪！实际耗时: $elapsed 秒" -ForegroundColor Green
        break
    }
}

# 最终验证
Write-Host ""
Write-Host "验证服务状态..." -ForegroundColor Cyan
$port7860Final = Get-NetTCPConnection -LocalPort 7860 -State Listen -ErrorAction SilentlyContinue
$port7866Final = Get-NetTCPConnection -LocalPort 7866 -State Listen -ErrorAction SilentlyContinue

if ($port7860Final) {
    Write-Host "✓ 端口 7860 (InfiniteTalk) 已就绪" -ForegroundColor Green
} else {
    Write-Host "⚠ 警告: 端口 7860 (InfiniteTalk) 未监听" -ForegroundColor Yellow
    Write-Host "  提示: 数字人视频生成可能会失败，请检查服务窗口的错误信息" -ForegroundColor Gray
}

if ($port7866Final) {
    Write-Host "✓ 端口 7866 (index-tts2) 已就绪" -ForegroundColor Green
} else {
    Write-Host "⚠ 警告: 端口 7866 (index-tts2) 未监听" -ForegroundColor Yellow
    Write-Host "  提示: TTS 语音生成可能会失败，请检查服务窗口的错误信息" -ForegroundColor Gray
}

# 如果所有服务都未就绪，询问是否继续
if (-not $port7860Final -and -not $port7866Final) {
    Write-Host "`n⚠ 两个服务都未就绪！" -ForegroundColor Red
    Write-Host "建议: 检查服务窗口，确认是否有错误信息" -ForegroundColor Yellow
    Write-Host "      如果服务正在加载模型，可以等待更长时间" -ForegroundColor Yellow
}

Write-Host ""

Write-Host "============================================================"
Write-Host "激活 Conda 环境: social-auto-upload"
Write-Host "============================================================"
conda activate social-auto-upload
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Conda 环境激活失败" -ForegroundColor Red
    Clean-Services
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
    Clean-Services
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
    Clean-Services
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
    Clean-Services
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
    Clean-Services
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
    Clean-Services
    exit 1
}
Write-Host "✓ 步骤5完成" -ForegroundColor Green
Write-Host ""

Write-Host "============================================================"
Write-Host "🎉 所有步骤执行成功！" -ForegroundColor Green
Write-Host "结束时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "============================================================"
Write-Host ""

Write-Host "============================================================"
Write-Host "清理后台服务"
Write-Host "============================================================"
Clean-Services
Write-Host ""
