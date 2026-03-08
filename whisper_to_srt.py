#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Whisper AI语音识别生成字幕
"""

import os
import sys
import argparse
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_audio(video_file, audio_file):
    """从视频中提取音频"""
    import subprocess
    
    cmd = [
        'ffmpeg',
        '-i', video_file,
        '-vn',  # 不要视频
        '-acodec', 'pcm_s16le',  # 音频编码
        '-ar', '16000',  # 采样率
        '-ac', '1',  # 单声道
        '-y',
        audio_file
    ]
    
    logger.info("从视频提取音频...")
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )
    
    if result.returncode == 0:
        logger.info(f"✓ 音频提取成功: {audio_file}")
        return True
    else:
        logger.error(f"✗ 音频提取失败: {result.stderr}")
        return False


def format_timestamp(seconds):
    """将秒数转换为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def transcribe_audio(audio_file, model_size='base', language='zh'):
    """使用Whisper识别音频"""
    try:
        import whisper
        
        logger.info(f"加载Whisper模型: {model_size}")
        model = whisper.load_model(model_size)
        
        logger.info("开始语音识别...")
        result = model.transcribe(
            audio_file,
            language=language,
            verbose=False,
            word_timestamps=True
        )
        
        return result
    except ImportError:
        logger.error("✗ 未安装Whisper，请运行: pip install openai-whisper")
        return None
    except Exception as e:
        logger.error(f"✗ 语音识别失败: {e}")
        return None


def merge_segments(segments, max_chars=9, max_duration=3.0):
    """
    合并短片段，确保每句不超过max_chars个字
    优先在标点符号处断句，生成更短更精确的字幕
    
    参数:
        segments: Whisper返回的片段列表
        max_chars: 每句最大字符数（默认9个字）
        max_duration: 每句最大时长（秒，默认3秒）
    """
    # 强断句标点（遇到这些立即分句）
    strong_punctuation = {'。', '.', '！', '!', '？', '?', '；', ';'}
    # 弱断句标点（可以考虑分句）
    weak_punctuation = {'，', ',', '、'}
    
    merged = []
    current = {
        'start': None,
        'end': None,
        'text': ''
    }
    
    for seg in segments:
        text = seg['text'].strip()
        if not text:
            continue
        
        # 如果是第一个片段
        if current['start'] is None:
            current['start'] = seg['start']
            current['end'] = seg['end']
            current['text'] = text
            
            # 检查是否以强标点结尾，如果是就不合并
            if text and text[-1] in strong_punctuation:
                merged.append(current.copy())
                current = {'start': None, 'end': None, 'text': ''}
        else:
            # 检查是否可以合并
            new_text = current['text'] + text
            duration = seg['end'] - current['start']
            
            # 检查当前文本是否以强标点结尾
            ends_with_strong = current['text'] and current['text'][-1] in strong_punctuation
            
            # 判断是否应该分句：
            # 1. 遇到强标点必须分句
            # 2. 超过最大字符数
            # 3. 超过最大时长
            # 4. 当前有弱标点且新文本会超过70%的max_chars
            should_break = (
                ends_with_strong or
                len(new_text) > max_chars or
                duration > max_duration or
                (current['text'] and current['text'][-1] in weak_punctuation and len(new_text) > max_chars * 0.7)
            )
            
            if should_break:
                # 不能合并，保存当前并开始新的
                if current['text']:
                    merged.append(current.copy())
                current['start'] = seg['start']
                current['end'] = seg['end']
                current['text'] = text
                
                # 检查新片段是否以强标点结尾
                if text and text[-1] in strong_punctuation:
                    merged.append(current.copy())
                    current = {'start': None, 'end': None, 'text': ''}
            else:
                # 可以合并
                current['text'] = new_text
                current['end'] = seg['end']
                
                # 合并后检查是否以强标点结尾
                if current['text'] and current['text'][-1] in strong_punctuation:
                    merged.append(current.copy())
                    current = {'start': None, 'end': None, 'text': ''}
    
    # 添加最后一个片段
    if current['text']:
        merged.append(current)
    
    return merged


def split_long_text(text, max_length=9):
    """将长文本分成两行，优先在标点符号处分割"""
    if len(text) <= max_length:
        return text
    
    # 尝试在标点符号处分行（优先强标点）
    strong_punctuation = '。.！!？?；;'
    weak_punctuation = '，,、'
    
    half = len(text) // 2
    best_pos = None
    best_distance = float('inf')
    
    # 先找强标点
    for i in range(len(text)):
        if text[i] in strong_punctuation:
            distance = abs(i + 1 - half)
            if distance < best_distance and distance < len(text) * 0.4:
                best_distance = distance
                best_pos = i + 1
    
    # 如果没找到强标点，找弱标点
    if best_pos is None:
        for i in range(len(text)):
            if text[i] in weak_punctuation:
                distance = abs(i + 1 - half)
                if distance < best_distance and distance < len(text) * 0.4:
                    best_distance = distance
                    best_pos = i + 1
    
    if best_pos:
        return text[:best_pos] + '\n' + text[best_pos:]
    
    # 如果没找到标点，就在中间分割
    return text[:half] + '\n' + text[half:]


def create_srt(segments, max_chars=9):
    """生成SRT字幕内容"""
    srt_lines = []
    
    for i, seg in enumerate(segments, 1):
        text = split_long_text(seg['text'], max_chars)
        
        srt_lines.append(str(i))
        srt_lines.append(f"{format_timestamp(seg['start'])} --> {format_timestamp(seg['end'])}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return '\n'.join(srt_lines)


def whisper_to_srt(video_file, output_srt=None, model_size='base', 
                   language='zh', max_chars=9, max_duration=3.0):
    """
    使用Whisper从视频生成SRT字幕
    
    参数:
        video_file: 视频文件路径
        output_srt: 输出SRT文件路径
        model_size: Whisper模型大小 (tiny, base, small, medium, large)
        language: 语言代码 (zh, en等)
        max_chars: 每句最大字符数
        max_duration: 每句最大时长
    """
    logger.info("=" * 60)
    logger.info("Whisper AI字幕生成工具")
    logger.info("=" * 60)
    
    # 检查视频文件
    if not os.path.exists(video_file):
        logger.error(f"✗ 视频文件不存在: {video_file}")
        return False
    
    # 提取音频
    temp_audio = "temp_audio.wav"
    if not extract_audio(video_file, temp_audio):
        return False
    
    try:
        # 语音识别
        result = transcribe_audio(temp_audio, model_size, language)
        if not result:
            return False
        
        logger.info(f"✓ 识别完成，共 {len(result['segments'])} 个片段")
        
        # 合并短片段
        merged_segments = merge_segments(result['segments'], max_chars, max_duration)
        logger.info(f"✓ 合并后共 {len(merged_segments)} 句")
        
        # 生成SRT
        srt_content = create_srt(merged_segments, max_chars)
        
        # 确定输出文件名
        if output_srt is None:
            video_path = Path(video_file)
            output_srt = str(video_path.parent / f"{video_path.stem}_whisper.srt")
        
        # 写入文件
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        file_size = os.path.getsize(output_srt)
        logger.info("=" * 60)
        logger.info("✓ 字幕文件生成成功！")
        logger.info(f"输出文件: {output_srt}")
        logger.info(f"文件大小: {file_size} 字节")
        logger.info(f"字幕条数: {len(merged_segments)}")
        logger.info("=" * 60)
        
        return output_srt
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
            logger.info("✓ 清理临时文件")


def main():
    parser = argparse.ArgumentParser(
        description='使用Whisper AI从视频生成字幕'
    )
    parser.add_argument('video_file', help='输入视频文件路径')
    parser.add_argument('-o', '--output', help='输出SRT文件路径')
    parser.add_argument('--model', default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper模型大小 (默认: base)')
    parser.add_argument('--language', default='zh', help='语言代码 (默认: zh)')
    parser.add_argument('--max-chars', type=int, default=15, 
                       help='每句最大字符数 (默认: 15)')
    parser.add_argument('--max-duration', type=float, default=5.0,
                       help='每句最大时长秒数 (默认: 5.0)')
    
    args = parser.parse_args()
    
    result = whisper_to_srt(
        args.video_file,
        args.output,
        args.model,
        args.language,
        args.max_chars,
        args.max_duration
    )
    
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
