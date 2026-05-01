# 常用命令记录

## 完整工作流 (Workflow)

### 基本用法
从文本到带字幕的数字人视频的完整流程：

```bash
# 手动执行工作流
python .\workflow.py "D:\video_workspace\source_txt\0_年月日.txt" "D:\video_workspace\source_audio\zyxtest20251221.m4a" "D:\video_workspace\source_picture\6_zyx.webp" .\output_video\ --prompt "男人正在说话"
```

### 自动生成抖音草稿（含服务启动）

完整流程：启动 AI 服务 → 生成日期 → 生成视频 → 上传抖音

```powershell
# 使用默认参数
.\auto_generate_douyin_draft.ps1

# 自定义文本文件
.\auto_generate_douyin_draft.ps1 -TextFile "D:\custom\my_text.txt"

# 自定义所有参数
.\auto_generate_douyin_draft.ps1 -TextFile "D:\texts\content.txt" -AudioFile "D:\audio\voice.m4a" -ImageFile "D:\images\avatar.png" -Prompt "女人在讲解"
```

**参数说明：**
- `-TextFile`: 文本文件路径（默认：`D:\workspace\github\openyixi\social-auto-upload\output_video\date.txt`）
- `-AudioFile`: 音频文件路径（默认：`D:\video_workspace\source_audio\zyxtest20251221.m4a`）
- `-ImageFile`: 图片文件路径（默认：`D:\video_workspace\source_picture\6_zyx.webp`）
- `-Prompt`: 数字人提示词（默认：`"男人正在说话"`）

### 仅上传视频到抖音

```powershell
.\auto_upload_douyin.ps1
```