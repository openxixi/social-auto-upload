# AI字幕生成系统 - 快速指南

## 🚀 一键运行

```powershell
.\add_subtitle_whisper.ps1
```

## 📁 核心文件

| 文件 | 功能 |
|------|------|
| `add_subtitle_whisper.ps1` | **主脚本** - 一键完成所有流程 |
| `whisper_to_srt.py` | AI语音识别生成字幕 |
| `correct_subtitle.py` | 使用原文本矫正字幕 |
| `add_subtitle_to_video.py` | 字幕嵌入视频 |

## ⚙️ 配置文件路径

编辑 `add_subtitle_whisper.ps1` 的第10-11行：

```powershell
$VIDEO_FILE = ".\output_video\你的视频.mp4"
$TEXT_FILE = "D:\video_workspace\source_txt\你的文本.txt"
```

## 📊 处理流程

```
输入视频 
   ↓
Whisper AI识别 (10秒) → whisper_字幕.srt
   ↓
文本矫正 (1秒) → corrected_字幕.srt
   ↓
字幕嵌入 (5秒) → 最终视频.mp4
```

## 🎨 当前配置

- **字体大小**: 14
- **字体颜色**: 黄色
- **每行字符**: 最多13字
- **边框粗细**: 3像素黑边
- **阴影**: 2像素

## 📝 输出文件

所有文件保存在 `output_video/` 目录：
- `whisper_字幕.srt` - AI识别原始字幕
- `corrected_字幕.srt` - 矫正后的字幕
- `最终视频.mp4` - 带字幕的视频（约12MB）

## ⏱️ 处理时间

以81秒视频为例：
- Whisper识别: ~10秒
- 文本矫正: ~1秒  
- 视频合成: ~5秒
- **总计**: ~20秒

## 🛠️ 常用调整

### 字幕太小
```powershell
--fontsize 16  # 改大字号
```

### 字幕出框
```powershell
--max-chars 11  # 减少每行字数
```

### 换个颜色
```powershell
--fontcolor white   # 白色
--fontcolor cyan    # 青色
--fontcolor red     # 红色
```

## 📖 详细文档

查看 [字幕工具使用说明.md](字幕工具使用说明.md) 了解更多细节。

## ✅ 系统测试结果

最后测试时间: 2026-02-03 23:55

```
✓ Whisper识别: 成功 (32句字幕)
✓ 文本矫正: 成功 (394字符匹配)
✓ 视频合成: 成功 (12.05MB)
✓ 总耗时: 20秒
```

## 🎯 版本信息

- 版本: 1.0
- 更新日期: 2026-02-03
- 作者: OpenYiXi
