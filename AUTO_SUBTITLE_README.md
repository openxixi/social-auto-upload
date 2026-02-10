# 自动字幕工具使用说明

## 功能特点

✨ **全自动处理**：智能匹配文本和视频文件，自动生成并添加字幕
✨ **智能断句**：按标点符号自动断句，支持自定义每句长度
✨ **时间轴同步**：根据视频时长自动分配字幕显示时间
✨ **批量处理**：支持一次处理多个视频文件
✨ **跳过已处理**：自动跳过已存在的输出文件，避免重复处理

## 快速开始

### 方式1：使用PowerShell快捷脚本（推荐）

编辑 [auto_subtitle.ps1](auto_subtitle.ps1) 文件，修改配置：

```powershell
# 单文件模式
$VIDEO_PATH = ".\output_video\你的视频.mp4"
$TEXT_DIR = "D:\video_workspace\source_txt"
$BATCH_MODE = $false

# 或批量模式
$BATCH_MODE = $true
$VIDEO_DIR = ".\output_video"
$PATTERN = "*.mp4"
```

然后运行：
```powershell
.\auto_subtitle.ps1
```

### 方式2：命令行使用

**处理单个视频**（自动查找匹配的文本文件）：
```bash
python auto_subtitle.py video.mp4 --text-dir D:\texts
```

**处理单个视频**（指定文本文件）：
```bash
python auto_subtitle.py video.mp4 --text subtitle.txt
```

**批量处理目录中的所有视频**：
```bash
python auto_subtitle.py --batch D:\videos --text-dir D:\texts
```

## 详细参数说明

### 基础参数

- `video` - 视频文件路径（单文件模式）
- `--batch DIR` - 批量处理模式，指定视频目录
- `--text FILE` - 指定文本文件（单文件模式）
- `--text-dir DIR` - 文本文件搜索目录（可多次使用）
- `-o, --output-dir DIR` - 输出目录（默认与视频同目录）

### 字幕样式参数

- `--fontsize SIZE` - 字体大小（默认：28）
- `--fontcolor COLOR` - 字体颜色（white/yellow/red等，默认：white）

### 断句参数

- `--max-length N` - 每句最大字符数（默认：20）
- `--speed N` - 阅读速度，字/秒（默认：5）

### 其他参数

- `--pattern PATTERN` - 批量模式的文件匹配模式（默认：*.mp4）
- `--no-skip` - 强制重新生成，不跳过已存在的文件

## 使用示例

### 示例1：自动匹配文本处理单个视频
```bash
python auto_subtitle.py video.mp4 --text-dir D:\texts
```
脚本会在 `D:\texts` 目录中查找与视频编号匹配的文本文件。

### 示例2：指定文本文件
```bash
python auto_subtitle.py video.mp4 --text subtitle.txt -o output_dir
```

### 示例3：批量处理并自定义样式
```bash
python auto_subtitle.py --batch D:\videos --text-dir D:\texts --fontsize 32 --fontcolor yellow
```

### 示例4：处理特定模式的视频
```bash
python auto_subtitle.py --batch D:\videos --text-dir D:\texts --pattern "*_trim.mp4"
```

### 示例5：自定义断句规则
```bash
python auto_subtitle.py video.mp4 --text-dir D:\texts --max-length 15 --speed 6
```
每句最多15字，阅读速度6字/秒。

## 文件匹配规则

脚本通过文件名中的数字编号自动匹配视频和文本文件：

- 视频：`2_视频名称.mp4` → 编号：`2`
- 文本：`2_文本内容.txt` → 编号：`2`

只要编号匹配，就会自动关联。

## 输出文件

处理完成后会生成：

1. **SRT字幕文件**：`视频名_字幕.srt`
2. **带字幕视频**：`视频名_字幕.mp4`

## 断句规则

1. 优先按句末标点（。！？.!?）断句
2. 长句按逗号（，,、）再分割
3. 超长句按最大字符数强制分割
4. 自动过滤单独的标点符号

## 注意事项

- ✅ 需要安装FFmpeg（脚本会自动检测）
- ✅ 文本文件支持UTF-8/GBK/GB2312编码
- ✅ 默认跳过已存在的输出文件（使用 `--no-skip` 强制重新生成）
- ✅ 批量处理会显示详细进度和统计信息

## 相关脚本

- [text_to_srt.py](text_to_srt.py) - 文本转SRT字幕（单独使用）
- [add_subtitle_to_video.py](add_subtitle_to_video.py) - 添加字幕到视频（单独使用）
- [auto_subtitle.py](auto_subtitle.py) - 全自动字幕处理（推荐）
- [auto_subtitle.ps1](auto_subtitle.ps1) - PowerShell快捷脚本

## 获取帮助

```bash
python auto_subtitle.py --help
```
