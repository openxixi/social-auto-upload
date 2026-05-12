# 视频增强功能 - 提高抖音原创性

## 📌 问题背景

抖音上传视频时，如果被判定为"原创性不足"，可能导致：
- 视频流量受限
- 无法获得推荐
- 账号权重降低

## ✨ 解决方案

新增 `enhance_video.py` 脚本，自动为视频添加以下元素来提高原创性：

### 1. 🎵 背景音乐
- 自动从 `bgm/` 目录随机选择音乐
- 以较低音量（默认 12-15%）混入视频
- 不影响原视频的语音内容

### 2. 📝 动态文字水印
- 在视频右下角添加半透明文字
- 随机选择文案（或自定义）
- 增加视频的个性化元素

### 3. 🔍 视觉效果（可选）
- 轻微的缩放效果
- 让画面更有动感

## 🚀 快速开始

### 步骤 1: 准备背景音乐

在项目根目录创建 `bgm/` 文件夹，并放入音乐文件：

```bash
mkdir bgm
# 将音乐文件（.mp3, .m4a, .wav）复制到 bgm/ 目录
```

**音乐建议：**
- 使用无版权音乐（避免侵权）
- 轻音乐、纯音乐效果最好
- 建议准备 5-10 个不同的音乐，让每个视频都有变化

**无版权音乐资源：**
- [YouTube Audio Library](https://www.youtube.com/audiolibrary)
- [Bensound](https://www.bensound.com/)
- [Free Music Archive](https://freemusicarchive.org/)
- [爱给网](https://www.aigei.com/music/)

### 步骤 2: Pipeline 自动增强

Pipeline 已经自动集成了视频增强功能，只需正常运行：

```bash
python pipeline.py
```

处理流程：
1. ✅ 清理旧文件
2. ✅ 复制新文件
3. ✅ 处理视频和图片
   - 为图片添加日期
   - 为视频添加日期尾部
   - **🆕 增强视频（添加音乐+文字）**
4. ✅ 上传到抖音

### 步骤 3: 单独使用增强脚本

如果想单独处理某个视频：

```bash
# 基本使用（添加音乐+文字）
python enhance_video.py input.mp4 -o output.mp4

# 自定义文字
python enhance_video.py input.mp4 -o output.mp4 --text "关注不迷路"

# 调整音乐音量（0.1 = 10%）
python enhance_video.py input.mp4 -o output.mp4 --volume 0.1

# 不添加文字
python enhance_video.py input.mp4 -o output.mp4 --no-text

# 不添加音乐
python enhance_video.py input.mp4 -o output.mp4 --no-music

# 添加缩放效果（较慢）
python enhance_video.py input.mp4 -o output.mp4 --add-zoom

# 指定音乐目录
python enhance_video.py input.mp4 -o output.mp4 --music-dir ./my_music
```

## 📊 效果对比

| 项目 | 增强前 | 增强后 |
|------|--------|--------|
| 背景音乐 | ❌ 无 | ✅ 有 |
| 文字水印 | ❌ 无 | ✅ 有 |
| 视觉动态 | ⚪ 静态 | ✅ 动态 |
| 原创性判定 | ⚠️ 可能不足 | ✅ 提高 |

## ⚙️ 配置选项

### 音乐音量调整

在 `pipeline.py` 中修改：

```python
'--volume', '0.12'  # 默认 12%，可调整为 0.08-0.20
```

### 自定义水印文字

在 `enhance_video.py` 中的 `texts` 列表添加你想要的文案：

```python
texts = [
    "每天学习一点",
    "关注不迷路",
    "分享生活日常",
    "记录美好瞬间",
    "每日更新",
    # 添加你自己的文案
    "你的自定义文案",
]
```

### 关闭某些功能

修改 `pipeline.py` 的增强命令：

```python
# 只添加音乐，不添加文字
'--no-text'

# 只添加文字，不添加音乐
'--no-music'
```

## 🔧 故障排查

### 问题 1: 找不到 bgm 目录

```
背景音乐目录不存在: ./bgm，跳过添加背景音乐
```

**解决方案：**
```bash
mkdir bgm
# 然后添加音乐文件
```

### 问题 2: 音乐文件不支持

```
背景音乐目录中没有音乐文件
```

**解决方案：**
确保音乐文件格式为 `.mp3`, `.m4a`, 或 `.wav`

### 问题 3: FFmpeg 错误

```
添加背景音乐失败: ...
```

**解决方案：**
1. 检查 FFmpeg 是否正确安装
2. 尝试更新 FFmpeg 到最新版本
3. 检查音乐文件是否损坏

### 问题 4: 增强失败但不影响上传

脚本设计为如果增强失败，会自动使用原始视频继续后续流程，不会中断上传。

## 💡 进阶技巧

### 1. 为不同类型的视频使用不同的音乐

```bash
# 创建多个音乐目录
mkdir bgm_calm      # 平静音乐
mkdir bgm_upbeat    # 欢快音乐
mkdir bgm_tech      # 科技感音乐
```

然后修改 pipeline.py 根据内容选择目录。

### 2. 批量处理已有视频

```bash
# 创建批处理脚本
for file in ./output_video/*.mp4; do
    python enhance_video.py "$file" -o "${file%.mp4}_enhanced.mp4"
done
```

### 3. 组合多种效果

```bash
# 添加所有效果
python enhance_video.py input.mp4 -o output.mp4 \
    --add-zoom \
    --text "我的频道" \
    --volume 0.15
```

## 📈 测试建议

建议先用一个视频测试效果：

1. 准备一个测试视频
2. 运行增强脚本
3. 查看输出视频效果
4. 调整参数（音量、文字等）
5. 确认满意后再用于 pipeline

```bash
# 测试命令
python enhance_video.py ./test_video.mp4 -o ./test_output.mp4
```

## 📝 注意事项

1. **音乐版权**：确保使用无版权音乐，避免侵权
2. **音量平衡**：背景音乐音量不要太大，建议 10-20%
3. **文字内容**：避免使用敏感词汇
4. **处理时间**：添加缩放效果会显著增加处理时间
5. **磁盘空间**：确保有足够空间存储临时文件

## 🎯 预期效果

使用视频增强后：
- ✅ 降低"原创性不足"的判定风险
- ✅ 视频更具个性化
- ✅ 提升用户观看体验
- ✅ 增加视频的丰富度

## 🤝 进一步优化建议

如果仍然被判定原创性不足，可以考虑：

1. 在剪映中添加更多元素：
   - 文字动画
   - 转场效果
   - 贴纸
   - 滤镜

2. 调整视频内容：
   - 增加片头片尾
   - 添加口播解说
   - 画中画效果

3. 使用不同的模板和风格
