#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动字幕处理工具
自动为视频文件添加字幕（从文本文件生成）
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from text_to_srt import create_srt_file
from add_subtitle_to_video import add_subtitle_to_video, check_ffmpeg

# 设置标准输出编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def find_matching_text_file(video_file, text_dirs):
    """
    根据视频文件名查找匹配的文本文件
    匹配规则：文件名包含数字编号
    """
    video_path = Path(video_file)
    video_name = video_path.stem
    
    # 提取数字编号
    import re
    numbers = re.findall(r'\d+', video_name)
    
    if not numbers:
        logger.warning(f"视频文件名不包含数字编号: {video_name}")
        return None
    
    # 搜索包含相同数字的文本文件
    for text_dir in text_dirs:
        if not os.path.exists(text_dir):
            continue
        
        for file in os.listdir(text_dir):
            if not file.endswith('.txt'):
                continue
            
            file_numbers = re.findall(r'\d+', file)
            # 如果文本文件包含视频文件的第一个数字
            if numbers[0] in file_numbers:
                text_file = os.path.join(text_dir, file)
                logger.info(f"✓ 找到匹配的文本文件: {file}")
                return text_file
    
    logger.warning(f"未找到匹配的文本文件 (编号: {numbers[0]})")
    return None


def process_video(video_file, text_file=None, text_dirs=None, output_dir=None,
                 fontsize=28, fontcolor='white', max_length=20, speed=5,
                 skip_existing=True):
    """
    处理单个视频文件，自动生成并添加字幕
    
    参数:
        video_file: 视频文件路径
        text_file: 文本文件路径（如果为None则自动查找）
        text_dirs: 文本文件搜索目录列表
        output_dir: 输出目录
        fontsize: 字体大小
        fontcolor: 字体颜色
        max_length: 每句最大字符数
        speed: 阅读速度（字/秒）
        skip_existing: 是否跳过已存在的输出文件
    """
    video_path = Path(video_file)
    
    if not video_path.exists():
        logger.error(f"✗ 视频文件不存在: {video_file}")
        return False
    
    # 确定输出目录
    if output_dir is None:
        output_dir = video_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    output_video = output_dir / f"{video_path.stem}_字幕{video_path.suffix}"
    
    # 检查是否跳过已存在的文件
    if skip_existing and output_video.exists():
        logger.info(f"⊙ 跳过已存在的文件: {output_video.name}")
        return True
    
    logger.info("=" * 70)
    logger.info(f"处理视频: {video_path.name}")
    logger.info("=" * 70)
    
    # 如果没有指定文本文件，自动查找
    if text_file is None:
        if text_dirs is None:
            text_dirs = [video_path.parent]
        text_file = find_matching_text_file(video_file, text_dirs)
        
        if text_file is None:
            logger.error("✗ 未找到匹配的文本文件，跳过此视频")
            return False
    
    # 生成SRT字幕文件
    srt_file = output_dir / f"{video_path.stem}_字幕.srt"
    
    logger.info("")
    logger.info("步骤 1/2: 生成SRT字幕文件")
    logger.info("-" * 70)
    
    result = create_srt_file(
        text_file,
        str(srt_file),
        video_file,
        max_length,
        speed
    )
    
    if not result:
        logger.error("✗ 字幕文件生成失败")
        return False
    
    # 添加字幕到视频
    logger.info("")
    logger.info("步骤 2/2: 将字幕添加到视频")
    logger.info("-" * 70)
    
    success = add_subtitle_to_video(
        video_file,
        str(srt_file),
        str(output_video),
        fontsize,
        fontcolor,
        'bottom',
        0.7,
        use_srt=True
    )
    
    if success:
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"✓ 完成！输出: {output_video.name}")
        logger.info("=" * 70)
    
    return success


def batch_process(video_dir, text_dirs=None, output_dir=None, 
                 fontsize=28, fontcolor='white', max_length=20, speed=5,
                 pattern='*.mp4', skip_existing=True):
    """
    批量处理目录中的所有视频文件
    
    参数:
        video_dir: 视频文件目录
        text_dirs: 文本文件搜索目录列表
        output_dir: 输出目录
        fontsize: 字体大小
        fontcolor: 字体颜色
        max_length: 每句最大字符数
        speed: 阅读速度（字/秒）
        pattern: 视频文件匹配模式
        skip_existing: 是否跳过已存在的输出文件
    """
    video_dir = Path(video_dir)
    
    if not video_dir.exists():
        logger.error(f"✗ 视频目录不存在: {video_dir}")
        return False
    
    # 查找所有视频文件
    video_files = list(video_dir.glob(pattern))
    
    if not video_files:
        logger.error(f"✗ 在 {video_dir} 中未找到匹配 {pattern} 的视频文件")
        return False
    
    logger.info(f"找到 {len(video_files)} 个视频文件")
    logger.info("")
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, video_file in enumerate(video_files, 1):
        logger.info(f"[{i}/{len(video_files)}] 处理: {video_file.name}")
        
        result = process_video(
            str(video_file),
            text_file=None,
            text_dirs=text_dirs,
            output_dir=output_dir,
            fontsize=fontsize,
            fontcolor=fontcolor,
            max_length=max_length,
            speed=speed,
            skip_existing=skip_existing
        )
        
        if result:
            success_count += 1
        else:
            failed_count += 1
        
        logger.info("")
    
    # 统计结果
    logger.info("=" * 70)
    logger.info("批量处理完成")
    logger.info("=" * 70)
    logger.info(f"✓ 成功: {success_count}")
    logger.info(f"✗ 失败: {failed_count}")
    logger.info(f"总计: {len(video_files)}")
    logger.info("=" * 70)
    
    return failed_count == 0


def main():
    parser = argparse.ArgumentParser(
        description='自动为视频添加字幕（从文本文件生成）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:

1. 处理单个视频（自动查找文本）:
   python auto_subtitle.py video.mp4 --text-dir D:\\texts

2. 处理单个视频（指定文本文件）:
   python auto_subtitle.py video.mp4 --text subtitle.txt

3. 批量处理目录中的所有视频:
   python auto_subtitle.py --batch D:\\videos --text-dir D:\\texts

4. 自定义字幕样式:
   python auto_subtitle.py video.mp4 --text-dir D:\\texts --fontsize 32 --fontcolor yellow

5. 设置断句参数:
   python auto_subtitle.py video.mp4 --text-dir D:\\texts --max-length 15 --speed 6
        """
    )
    
    # 视频文件参数
    parser.add_argument('video', nargs='?', help='视频文件路径（单文件模式）')
    parser.add_argument('--batch', help='批量处理模式：视频文件目录')
    parser.add_argument('--pattern', default='*.mp4', help='批量模式的文件匹配模式（默认: *.mp4）')
    
    # 文本文件参数
    parser.add_argument('--text', help='文本文件路径（单文件模式）')
    parser.add_argument('--text-dir', action='append', dest='text_dirs',
                       help='文本文件搜索目录（可多次指定）')
    
    # 输出参数
    parser.add_argument('-o', '--output-dir', help='输出目录（默认与视频同目录）')
    parser.add_argument('--no-skip', action='store_true', 
                       help='不跳过已存在的输出文件，强制重新生成')
    
    # 字幕样式参数
    parser.add_argument('--fontsize', type=int, default=28, help='字体大小（默认: 28）')
    parser.add_argument('--fontcolor', default='white', help='字体颜色（默认: white）')
    
    # 断句参数
    parser.add_argument('--max-length', type=int, default=20, 
                       help='每句最大字符数（默认: 20）')
    parser.add_argument('--speed', type=float, default=5, 
                       help='阅读速度（字/秒，默认: 5）')
    
    args = parser.parse_args()
    
    # 验证参数
    if not args.video and not args.batch:
        parser.error("请指定视频文件或使用 --batch 指定视频目录")
    
    if args.video and args.batch:
        parser.error("不能同时使用单文件模式和批量模式")
    
    logger.info("=" * 70)
    logger.info("自动字幕处理工具")
    logger.info("=" * 70)
    logger.info("")
    
    # 检查FFmpeg
    if not check_ffmpeg():
        return False
    
    logger.info("")
    
    # 批量处理模式
    if args.batch:
        success = batch_process(
            args.batch,
            args.text_dirs,
            args.output_dir,
            args.fontsize,
            args.fontcolor,
            args.max_length,
            args.speed,
            args.pattern,
            not args.no_skip
        )
    # 单文件模式
    else:
        success = process_video(
            args.video,
            args.text,
            args.text_dirs,
            args.output_dir,
            args.fontsize,
            args.fontcolor,
            args.max_length,
            args.speed,
            not args.no_skip
        )
    
    return success


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序出错: {e}", exc_info=True)
        sys.exit(1)
