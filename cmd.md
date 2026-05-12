# 工具使用指南

本项目是一个社交媒体视频自动化处理和上传工具集，支持视频处理、字幕添加、自动上传等功能。

---

## 📋 目录

1. [自动化流程工具](#自动化流程工具)
2. [视频处理工具](#视频处理工具)
3. [图片处理工具](#图片处理工具)
4. [字幕工具](#字幕工具)
5. [上传工具](#上传工具)
6. [辅助工具](#辅助工具)

---

## 🤖 自动化流程工具

### pipeline.py - 自动化处理和上传流程

**功能：** 自动扫描文件夹，按倒序处理视频，每天凌晨5点自动执行，晚上19:00定时发布到抖音。

**运行模式：**

```bash
# 默认模式：从最大数字文件夹开始，倒序处理，每天凌晨5点执行
python pipeline.py

# 单次运行模式：只执行一次就退出
python pipeline.py --once

# 继续模式：继续之前保存的进度
python pipeline.py --continue
```

**工作流程：**
1. **步骤1**：清理旧文件（删除 videos_pre 中的临时文件）
2. **步骤2**：从数字文件夹复制新文件（jpg + mp4）
3. **步骤3**：处理视频和图片
   - 为图片添加日期水印
   - 为视频添加日期尾部（抖音竖屏全屏格式 1080x1920）
4. **步骤4**：上传视频到抖音

**文件夹命名规则：**
- 文件夹名以数字开头，如：`01_标题`, `02_标题`, `10_标题`
- 自动按数字排序，倒序处理（从大到小）
- 处理到最小索引后，自动回到最大索引循环

**目录结构：**
```
D:\video_workspace\jianying_output\    (Windows)
/mnt/d/video_workspace/jianying_output\ (Linux)
├── 01_标题/
│   ├── 封面.jpg
│   └── 视频.mp4
├── 02_标题/
└── ...
```

**停止程序：** 按 `Ctrl+C` 优雅停止

---

### auto_generate_douyin_draft.ps1 - 自动生成抖音草稿

**功能：** 完整流程 - 启动 AI 服务 → 生成日期 → 生成数字人视频 → 上传抖音

```powershell
# 使用默认参数
.\auto_generate_douyin_draft.ps1

# 自定义文本文件
.\auto_generate_douyin_draft.ps1 -TextFile "D:\video_workspace\source_txt\5_余喜仗义留情面20260505.txt"

# 自定义所有参数
.\auto_generate_douyin_draft.ps1 `
  -TextFile "D:\texts\content.txt" `
  -AudioFile "D:\audio\voice.m4a" `
  -ImageFile "D:\images\avatar.png" `
  -Prompt "男人正在说话"
```

**参数说明：**
- `-TextFile`: 文本文件路径（默认：`output_video\date.txt`）
- `-AudioFile`: 音频文件路径（默认：`D:\video_workspace\source_audio\zyxtest20251221.m4a`）
- `-ImageFile`: 图片文件路径（默认：`D:\video_workspace\source_picture\6_zyx.webp`）
- `-Prompt`: 数字人提示词（默认：`"男人正在说话"`）

---

### auto_generate_jpg_mp4.ps1/sh - 批量处理视频

**功能：** 自动为视频添加封面图片和日期尾巴

```powershell
# Windows
.\auto_generate_jpg_mp4.ps1

# Linux
./auto_generate_jpg_mp4.sh
```

**处理流程：**
1. 为图片添加日期水印
2. 为视频添加日期尾部
3. 输出到 `videos/` 目录

---

## 🎬 视频处理工具

### auto_add_tail_to_videos.py - 添加日期尾部

**功能：** 为视频末尾添加年月日视频片段，支持抖音全屏格式

```bash
# 基本用法（从日期字典自动查找今天的日期视频）
python auto_add_tail_to_videos.py input.mp4 -o output.mp4

# 指定日期
python auto_add_tail_to_videos.py input.mp4 -o output.mp4 --date 2026-05-05

# 添加封面
python auto_add_tail_to_videos.py input.mp4 -c cover.jpg -o output.mp4

# 抖音竖屏全屏（推荐）
python auto_add_tail_to_videos.py input.mp4 \
  -c cover.jpg \
  -o output.mp4 \
  -r 1080x1920 \
  -f crop

# 指定日期字典目录
python auto_add_tail_to_videos.py input.mp4 \
  -o output.mp4 \
  -d /path/to/date_dictionary
```

**参数说明：**
- `input_video`: 输入视频文件路径（必需）
- `-o, --output`: 输出视频文件路径（默认：output_with_date.mp4）
- `-d, --date-dict`: 日期字典目录路径
- `--date`: 指定日期（格式：YYYY-MM-DD），默认今天
- `-c, --cover`: 封面图片文件路径（可选）
- `-r, --resolution`: 输出分辨率（默认：auto）
  - `auto`: 自动使用原视频分辨率
  - `1080x1920`: 抖音竖屏全屏
  - `1920x1080`: 横屏
- `-f, --fit-mode`: 填充模式（默认：pad）
  - `pad`: 添加黑边（保留完整内容）
  - `crop`: 裁剪填满（**抖音全屏推荐**）

**日期字典文件命名规则：**
```
date_dictionary/
├── 2026.mp4 或 2026年.mp4     (年份)
├── 5.mp4 或 5月.mp4            (月份)
└── 5.mp4 或 5日.mp4            (日期)
```

---

### merge_videos.py - 视频合并工具

**功能：** 合并多个视频，支持封面、分辨率调整、音量匹配

```bash
# 前后拼接多个视频
python merge_videos.py video1.mp4 video2.mp4 video3.mp4 -o output.mp4

# 添加封面（显示3秒）
python merge_videos.py video1.mp4 video2.mp4 \
  --cover cover.jpg \
  --cover-duration 3 \
  -o output.mp4

# 指定输出分辨率
python merge_videos.py video1.mp4 video2.mp4 \
  --resolution 1920x1080 \
  -o output.mp4

# 抖音竖屏全屏格式
python merge_videos.py video1.mp4 video2.mp4 video3.mp4 \
  -o output.mp4 \
  --resolution 1080x1920 \
  --fit-mode crop

# 其他合并模式
python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode side    # 左右并排
python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode stack   # 上下堆叠
python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode pip     # 画中画
```

**参数说明：**
- `videos`: 输入视频文件列表（至少1个）
- `-o, --output`: 输出文件路径
- `-m, --mode`: 合并模式
  - `concat`: 前后拼接（默认）
  - `side`: 左右并排
  - `stack`: 上下堆叠
  - `pip`: 画中画
  - `blend`: 混合
  - `crossfade`: 交叉淡入淡出
- `-c, --cover`: 封面图片文件
- `--cover-duration`: 封面显示时长（秒），默认0.5秒
- `-r, --resolution`: 输出分辨率
  - `auto`: 自动（默认）
  - `1920x1080`: 1080p横屏
  - `1080x1920`: 1080p竖屏（抖音）
  - `1280x720`: 720p
  - `3840x2160`: 4K
- `-f, --fit-mode`: 填充模式
  - `pad`: 添加黑边（默认）
  - `crop`: 裁剪填满（抖音全屏推荐）

**特性：**
- ✓ 自动音量匹配（以最大音量为准）
- ✓ 视频参数自动检测（分辨率、帧率、码率）
- ✓ 跨平台支持（Windows/Linux）
- ✓ 高质量编码（保持原视频质量）

---

### workflow.py - 完整工作流

**功能：** 从文本生成带字幕的数字人视频

```bash
python workflow.py \
  "D:\source_txt\0_年月日.txt" \
  "D:\source_audio\voice.m4a" \
  "D:\source_picture\avatar.webp" \
  .\output_video\ \
  --prompt "男人正在说话"
```

---

## 🖼️ 图片处理工具

### add_date_to_image.py - 添加日期水印

**功能：** 在图片上添加当天日期水印

```bash
# 基本用法（覆盖原图）
python add_date_to_image.py input.jpg

# 指定输出路径
python add_date_to_image.py input.jpg -o output.jpg

# 自定义日期格式
python add_date_to_image.py input.jpg -o output.jpg --format "%Y/%m/%d"
```

**参数说明：**
- `image`: 输入图片路径
- `-o, --output`: 输出图片路径（默认覆盖原图）
- `--format`: 日期格式（默认：`%Y年%m月%d日`）

**特性：**
- ✓ 自动识别中文字体（Windows: 微软雅黑，Linux: 文泉驿正黑）
- ✓ 水印大小自适应图片尺寸
- ✓ 水印前缀："余喜"

---

## 📝 字幕工具

### auto_subtitle.py - 自动生成字幕

**功能：** 使用 Whisper 自动识别音频生成字幕

```bash
# 自动生成字幕
python auto_subtitle.py video.mp4

# 指定输出路径
python auto_subtitle.py video.mp4 -o output.srt
```

详细文档参见：[AUTO_SUBTITLE_README.md](AUTO_SUBTITLE_README.md)

---

### add_subtitle_to_video.py - 添加字幕到视频

**功能：** 将 SRT 字幕文件嵌入视频

```bash
python add_subtitle_to_video.py video.mp4 subtitle.srt -o output.mp4
```

---

### correct_subtitle.py - 字幕纠错

**功能：** 使用 AI 修正字幕中的错误

```bash
python correct_subtitle.py input.srt -o corrected.srt
```

---

## 📤 上传工具

### auto_upload_douyin.ps1/sh - 上传抖音

**功能：** 自动上传视频到抖音

```powershell
# Windows
.\auto_upload_douyin.ps1

# Linux
./auto_upload_douyin.sh
```

**配置文件：** `conf.py`

---

### run_upload_all_douyin.py - 批量上传

**功能：** 批量上传 `videos/` 目录下的所有视频到抖音

```bash
python run_upload_all_douyin.py
```

**说明：**
- 自动读取账号配置
- 支持定时发布（晚上19:00）
- 支持多账号

---

### cli_main.py - 命令行工具

**功能：** 通过命令行登录和上传到各平台

```bash
# 登录平台
python cli_main.py <platform> <account_name> login

# 上传视频
python cli_main.py <platform> <account_name> upload <video_file>

# 定时上传（晚上19:00发布）
python cli_main.py <platform> <account_name> upload <video_file> -pt 1 -t "2026-05-05 19:00"
```

**支持平台：**
- `douyin`: 抖音
- `tiktok`: TikTok
- `bilibili`: B站
- `xiaohongshu`: 小红书
- `kuaishou`: 快手
- `tencent`: 视频号
- `baijiahao`: 百家号

---

## 🛠️ 辅助工具

### generate_date.py - 生成日期文本

**功能：** 生成今天的日期文本文件

```bash
python generate_date.py
```

**输出：** `output_video/date.txt`  
**内容示例：** `2026年5月5日`

---

### cp_dir.py - 目录复制

**功能：** 复制整个目录

```bash
python cp_dir.py source_dir target_dir
```

---

### check_video_info.py - 视频信息检查

**功能：** 检查视频详细信息（分辨率、码率、帧率等）

```bash
python check_video_info.py video.mp4
```

**输出信息：**
- 视频流：分辨率、宽高比、帧率、编码器、比特率
- 音频流：编码器、采样率、声道、比特率
- 文件信息：时长、大小、总比特率
- 抖音兼容性检查

---

## 🌐 Web 服务

### sau_backend.py - 后端服务

**功能：** 提供 Web 界面管理账号和视频上传

```bash
python sau_backend.py
```

**访问地址：** `http://localhost:5409`

---

### sau_frontend - 前端界面

**启动方式：**

```bash
cd sau_frontend
npm install
npm run dev
```

**访问地址：** `http://localhost:5173`

---

## 📌 常见使用场景

### 场景1：快速上传单个视频

```bash
# 1. 添加日期尾部和封面
python auto_add_tail_to_videos.py video.mp4 \
  -c cover.jpg \
  -o output.mp4 \
  -r 1080x1920 \
  -f crop

# 2. 上传到抖音
python cli_main.py douyin 账号名 upload output.mp4 -pt 1 -t "2026-05-05 19:00"
```

---

### 场景2：自动化批量处理

```bash
# 启动自动化流程（每天凌晨5点执行）
python pipeline.py
```

**流程：**
- 自动从 `jianying_output/` 文件夹获取素材
- 倒序处理（从最大数字开始）
- 自动添加日期和封面
- 自动上传到抖音（19:00发布）
- 处理完一个，索引-1，继续下一个

---

### 场景3：手动处理和上传

```powershell
# 1. 生成日期
python generate_date.py

# 2. 批量处理视频
.\auto_generate_jpg_mp4.ps1

# 3. 批量上传
python run_upload_all_douyin.py
```

---

## ⚙️ 系统要求

**必需软件：**
- Python 3.10+
- FFmpeg（用于视频处理）
- Playwright（用于浏览器自动化）

**安装依赖：**

```bash
# Python 依赖
pip install -r requirements.txt

# Playwright 浏览器
playwright install chromium
```

---

## 📖 配置说明

### conf.py - 主配置文件

从 `conf.example.py` 复制并修改：

```bash
cp conf.example.py conf.py
```

**配置项：**
- 账号信息
- 上传平台选择
- Cookie 存储路径
- 视频文件路径

---

## 🔍 调试工具

### 查看 FFmpeg 版本

```bash
ffmpeg -version
```

### 查看视频信息

```bash
python check_video_info.py video.mp4
```

### 测试视频处理

```bash
# 单次运行（不启动定时任务）
python pipeline.py --once
```

---

## 📞 常见问题

**Q: 视频在抖音上有黑边？**  
A: 使用 `-r 1080x1920 -f crop` 参数，裁剪填满全屏。

**Q: Linux 下字体显示方框？**  
A: 安装中文字体：`sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei`

**Q: 如何停止自动化流程？**  
A: 按 `Ctrl+C` 即可优雅停止程序。

**Q: 如何从指定文件夹继续处理？**  
A: 编辑 `pipeline_index.txt` 文件，修改索引值。

---

## 📚 更多文档

- [完整工作流说明](WORKFLOW_WITH_SUBTITLE_README.md)
- [字幕工具使用说明](AUTO_SUBTITLE_README.md)
- [项目概述](CLAUDE.md)