#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据Whisper识别的时间戳和原文本矫正字幕
"""

import os
import re
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def read_text_file(file_path):
    """读取文本文件"""
    if not os.path.exists(file_path):
        logger.error(f"✗ 文件不存在: {file_path}")
        return None
    
    for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read().strip()
                if content:
                    # 将换行符替换为空格
                    content = content.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
                    # 将多个连续空格合并
                    content = re.sub(r'\s+', '', content)
                    logger.info(f"✓ 成功读取原文 (编码: {encoding})")
                    return content
        except UnicodeDecodeError:
            continue
    
    logger.error("✗ 无法读取文件")
    return None


def parse_srt(srt_file):
    """解析SRT字幕文件，提取时间戳"""
    if not os.path.exists(srt_file):
        logger.error(f"✗ SRT文件不存在: {srt_file}")
        return None
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析SRT格式
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    timestamps = []
    for match in matches:
        timestamps.append({
            'start': match[1],
            'end': match[2],
            'text': match[3].replace('\n', '')
        })
    
    logger.info(f"✓ 解析SRT文件，共 {len(timestamps)} 个时间戳")
    return timestamps


def split_text_by_timestamps(text, timestamps, max_chars=15):
    """
    根据Whisper识别的字符数比例来分配原文本，并自动换行
    
    参数:
        text: 原文本
        timestamps: Whisper的时间戳列表（包含识别的文本）
        max_chars: 每行最大字符数
    """
    # 计算每个时间戳对应的字符数比例
    whisper_texts = [ts['text'].strip() for ts in timestamps]
    whisper_lengths = [len(t) for t in whisper_texts]
    total_whisper_len = sum(whisper_lengths)
    
    if total_whisper_len == 0:
        return [text]
    
    # 按比例分配原文本
    segments = []
    start_pos = 0
    
    for i, length in enumerate(whisper_lengths):
        # 计算这一段应该占的比例
        ratio = length / total_whisper_len
        # 计算这一段的字符数
        segment_len = int(len(text) * ratio)
        
        # 最后一段取到结尾
        if i == len(whisper_lengths) - 1:
            segment = text[start_pos:]
        else:
            # 尝试在标点符号处断开
            end_pos = start_pos + segment_len
            
            # 在end_pos附近寻找标点符号
            best_pos = end_pos
            search_range = min(10, segment_len // 2)
            
            for offset in range(search_range):
                for pos in [end_pos + offset, end_pos - offset]:
                    if pos < len(text) and text[pos] in '。！？；.!?;，,、':
                        best_pos = pos + 1
                        break
                if best_pos != end_pos:
                    break
            
            segment = text[start_pos:best_pos]
            start_pos = best_pos
        
        if segment.strip():
            # 自动换行：如果超过max_chars，智能断句
            segment = segment.strip()
            
            # 去掉开头的标点符号
            segment = re.sub(r'^[。！？；.!?;，,、\s]+', '', segment)
            
            # 如果去掉标点后为空或只剩标点，跳过
            if not segment or re.match(r'^[。！？；.!?;，,、\s]+$', segment):
                continue
            
            if len(segment) >= max_chars:
                lines = []
                remaining = segment
                while len(remaining) > max_chars:
                    # 尝试在max_chars位置附近找标点符号断开
                    split_pos = max_chars
                    found_punct = False
                    
                    # 向前找标点符号（扩大搜索范围到一半）
                    search_range = min(max_chars // 2 + 2, max_chars)
                    for i in range(max_chars, max(0, max_chars - search_range), -1):
                        if i < len(remaining) and remaining[i-1] in '。！？；.!?;，,、':
                            split_pos = i
                            found_punct = True
                            break
                    
                    # 如果没找到标点，就强制在max_chars处断开
                    if not found_punct:
                        split_pos = max_chars
                    
                    line = remaining[:split_pos]
                    # 清理每行开头的标点符号
                    line = re.sub(r'^[。！？；.!?;，,、\s]+', '', line)
                    if line:  # 只添加非空行
                        lines.append(line)
                    remaining = remaining[split_pos:]
                
                if remaining:
                    # 清理最后一行开头的标点符号
                    remaining = re.sub(r'^[。！？；.!?;，,、\s]+', '', remaining)
                    if remaining:
                        lines.append(remaining)
                
                # 过滤掉只包含标点符号的行
                lines = [line for line in lines if not re.match(r'^[。！？；.!?;，,、\s]*$', line)]
                
                if lines:  # 只有在有有效行时才添加
                    segment = '\n'.join(lines)
                else:
                    continue
            
            segments.append(segment)
    
    return segments


def split_long_line(text, max_length=9):
    """将长文本分成两行"""
    if len(text) <= max_length:
        return text
    
    # 定义标点符号优先级（强标点优先于弱标点）
    strong_punctuation = set('。.！!？?；;')
    weak_punctuation = set('，,、')
    
    # 尝试在标点符号处分行
    half = len(text) // 2
    best_pos = None
    best_distance = float('inf')
    
    # 先找强标点符号
    for i in range(len(text)):
        if text[i] in strong_punctuation:
            distance = abs(i + 1 - half)
            if distance < best_distance and distance < len(text) * 0.4:
                best_distance = distance
                best_pos = i + 1
    
    # 如果没有强标点，再找弱标点
    if not best_pos:
        for i in range(len(text)):
            if text[i] in weak_punctuation:
                distance = abs(i + 1 - half)
                if distance < best_distance and distance < len(text) * 0.4:
                    best_distance = distance
                    best_pos = i + 1
    
    if best_pos:
        return text[:best_pos] + '\n' + text[best_pos:]
    
    # 如果没找到标点，在中间分割
    return text[:half] + '\n' + text[half:]


def correct_srt(whisper_srt, text_file, output_srt=None, max_chars=9):
    """
    根据Whisper的时间戳和原文本生成矫正后的字幕
    
    参数:
        whisper_srt: Whisper生成的SRT文件（提供时间戳）
        text_file: 原文本文件（提供准确文字）
        output_srt: 输出SRT文件
        max_chars: 每句最大字符数
    """
    logger.info("=" * 60)
    logger.info("字幕矫正工具")
    logger.info("=" * 60)
    
    # 读取原文本
    text = read_text_file(text_file)
    if not text:
        return False
    
    logger.info(f"原文本长度: {len(text)} 字符")
    
    # 解析Whisper字幕的时间戳
    timestamps = parse_srt(whisper_srt)
    if not timestamps:
        return False
    
    # 根据Whisper识别的字符数比例分配原文本（每行最多9字）
    segments = split_text_by_timestamps(text, timestamps, max_chars=max_chars)
    logger.info(f"✓ 文本分割完成，共 {len(segments)} 句")
    
    # 显示分句结果
    for i, seg in enumerate(segments, 1):
        logger.info(f"  [{i}] {seg}")
    
    # 生成新的SRT内容
    srt_lines = []
    for i, (ts, seg) in enumerate(zip(timestamps, segments), 1):
        # segment已经在split_text_by_timestamps中处理过换行了
        # 不需要再调用split_long_line
        
        srt_lines.append(str(i))
        srt_lines.append(f"{ts['start']} --> {ts['end']}")
        srt_lines.append(seg)
        srt_lines.append("")
    
    srt_content = '\n'.join(srt_lines)
    
    # 确定输出文件名
    if output_srt is None:
        output_srt = whisper_srt.replace('.srt', '_corrected.srt')
    
    # 写入文件
    try:
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        file_size = os.path.getsize(output_srt)
        logger.info("=" * 60)
        logger.info("✓ 矫正后的字幕文件生成成功！")
        logger.info(f"输出文件: {output_srt}")
        logger.info(f"文件大小: {file_size} 字节")
        logger.info(f"字幕条数: {len(segments)}")
        logger.info("=" * 60)
        return output_srt
    except Exception as e:
        logger.error(f"✗ 写入文件失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='根据Whisper时间戳和原文本矫正字幕'
    )
    parser.add_argument('whisper_srt', help='Whisper生成的SRT文件')
    parser.add_argument('text_file', help='原文本文件')
    parser.add_argument('-o', '--output', help='输出SRT文件路径')
    parser.add_argument('--max-chars', type=int, default=13,
                       help='每句最大字符数 (默认: 13)')
    
    args = parser.parse_args()
    
    result = correct_srt(
        args.whisper_srt,
        args.text_file,
        args.output,
        args.max_chars
    )
    
    return 0 if result else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
