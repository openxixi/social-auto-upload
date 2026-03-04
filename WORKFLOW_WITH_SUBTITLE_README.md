# Workflow 自动字幕功能使用说明

## 功能概述

workflow.py 现在支持完整的自动字幕流程：
1. **Step 1**: 文本 → TTS 语音合成（生成音频）
2. **Step 2**: 音频 + 图片 → 数字人视频（生成视频）
3. **Step 3**: 视频 → 自动字幕（Whisper 识别 + 原文矫正 + 嵌入字幕）

## 使用方法

### 基础用法（不加字幕）

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话"
```

**生成文件：**
- `3_余喜致良知1.wav` - 音频文件
- `3_余喜致良知1.mp4` - 视频文件（无字幕）

### 带字幕用法（推荐）

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --add-subtitle
```

**生成文件：**
- `3_余喜致良知1.wav` - 音频文件
- `3_余喜致良知1.mp4` - 视频文件（无字幕）
- `3_余喜致良知1_whisper.srt` - Whisper 识别的字幕
- `3_余喜致良知1_corrected.srt` - 矫正后的字幕
- `3_余喜致良知1_字幕.mp4` - **最终带字幕的视频**

## 字幕相关参数

### --add-subtitle
启用自动字幕功能

### --whisper-model
Whisper 模型大小（默认：base）
- `tiny` - 最快，准确度较低
- `base` - 平衡（推荐）
- `small` - 更准确
- `medium` - 很准确
- `large` - 最准确但最慢

```bash
--add-subtitle --whisper-model small
```

### --max-chars
每行字幕最大字符数（默认：13）

```bash
--add-subtitle --max-chars 15
```

### --subtitle-fontsize
字幕字体大小（默认：14）

```bash
--add-subtitle --subtitle-fontsize 16
```

### --subtitle-fontcolor
字幕字体颜色（默认：yellow）

支持的颜色：white, yellow, red, green, blue, black 等

```bash
--add-subtitle --subtitle-fontcolor white
```

## 完整示例

### 基础字幕

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --add-subtitle
```

### 自定义字幕样式

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --add-subtitle --subtitle-fontsize 16 --subtitle-fontcolor white --max-chars 15
```

### 使用更好的 Whisper 模型

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --add-subtitle --whisper-model small
```

### 保留音频文件

```bash
python .\workflow.py "D:\video_workspace\source_txt\3_余喜致良知1.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\3_zyx_jpl.jpg" .\output_video\ --prompt "男人正在说话" --add-subtitle --keep-audio
```

## 输出文件命名规则

所有文件都基于输入文本文件名称：

假设输入文本文件为：`D:\video_workspace\source_txt\3_余喜致良知1.txt`

**不加字幕：**
- `3_余喜致良知1.wav` - 音频
- `3_余喜致良知1.mp4` - 视频

**加字幕：**
- `3_余喜致良知1.wav` - 音频
- `3_余喜致良知1.mp4` - 无字幕视频
- `3_余喜致良知1_whisper.srt` - Whisper 字幕
- `3_余喜致良知1_corrected.srt` - 矫正字幕
- `3_余喜致良知1_字幕.mp4` - **带字幕视频（最终输出）**

## 注意事项

1. **Whisper 模型**首次使用会自动下载，需要一些时间
2. **字幕生成**需要额外 1-2 分钟处理时间
3. 推荐使用 `base` 或 `small` 模型获得速度和准确度的平衡
4. 字幕会自动使用原文本进行矫正，提高准确度
5. 最终带字幕的视频会覆盖同名文件

## 故障排除

### 字幕生成失败
- 确保 FFmpeg 已安装并在 PATH 中
- 检查 Whisper 模型是否正确下载
- 查看日志中的详细错误信息

### 字幕显示不正确
- 尝试调整 `--max-chars` 参数
- 检查原文本文件编码是否为 UTF-8
- 尝试使用更大的 Whisper 模型（如 `small`）

### 视频文件未找到
- 确认视频生成步骤成功完成
- 检查输出目录中的文件列表
- 查看日志中的详细路径信息
