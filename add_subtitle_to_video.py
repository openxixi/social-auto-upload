#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频字幕添加脚本
使用FFmpeg将文本文件中的字幕添加到视频文件中
"""

import os
import sys
import subprocess
import argparse
import logging
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fontcolor_to_hex(color):
    """将颜色名称转换为ASS格式的BGR十六进制"""
    color_map = {
        'white': 'FFFFFF',
        'yellow': '00FFFF',
        'red': '0000FF',
        'green': '00FF00',
        'blue': 'FF0000',
        'black': '000000',
        'cyan': 'FFFF00',
        'magenta': 'FF00FF',
    }
    return color_map.get(color.lower(), 'FFFFFF')


def check_ffmpeg():
    """检查FFmpeg是否已安装"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )
        if result.returncode == 0:
            logger.info("✓ 检测到FFmpeg")
            return True
    except FileNotFoundError:
        logger.error("✗ 未检测到FFmpeg，请先安装FFmpeg")
        logger.error("下载地址: https://ffmpeg.org/download.html")
        return False
    return False


def read_subtitle_text(text_file):
    """读取字幕文本文件"""
    if not os.path.exists(text_file):
        logger.error(f"✗ 字幕文件不存在: {text_file}")
        return None
    
    try:
        # 尝试不同的编码
        for encoding in ['utf-8', 'gbk', 'gb2312']:
            try:
                with open(text_file, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                    if content:
                        logger.info(f"✓ 成功读取字幕文件 (编码: {encoding})")
                        logger.info(f"字幕内容长度: {len(content)} 字符")
                        return content
            except UnicodeDecodeError:
                continue
        
        logger.error(f"✗ 无法读取字幕文件，尝试的编码均失败")
        return None
    except Exception as e:
        logger.error(f"✗ 读取字幕文件时出错: {e}")
        return None


def create_subtitle_filter(text, fontsize=24, fontcolor='white', 
                          position='bottom', bg_opacity=0.7):
    """
    创建FFmpeg字幕滤镜
    
    参数:
        text: 字幕文本
        fontsize: 字体大小
        fontcolor: 字体颜色
        position: 位置 (top, center, bottom)
        bg_opacity: 背景透明度 (0-1)
    """
    # 转义特殊字符
    text = text.replace('\\', '\\\\')
    text = text.replace(':', '\\:')
    text = text.replace("'", "\\'")
    
    # 设置位置
    if position == 'top':
        y_pos = 'h*0.1'
    elif position == 'center':
        y_pos = '(h-text_h)/2'
    else:  # bottom
        y_pos = 'h-text_h-20'
    
    # 构建滤镜
    # 使用drawtext滤镜，添加半透明背景
    filter_str = (
        f"drawtext=text='{text}':"
        f"fontfile='C\\:/Windows/Fonts/simhei.ttf':"  # 黑体字体
        f"fontsize={fontsize}:"
        f"fontcolor={fontcolor}:"
        f"x=(w-text_w)/2:"  # 水平居中
        f"y={y_pos}:"
        f"box=1:"  # 启用背景框
        f"boxcolor=black@{bg_opacity}:"  # 黑色半透明背景
        f"boxborderw=5"  # 背景边距
    )
    
    return filter_str


def add_subtitle_to_video(video_file, subtitle_file, output_file=None,
                          fontsize=24, fontcolor='white', position='bottom',
                          bg_opacity=0.7, use_srt=True):
    """
    将字幕添加到视频文件
    
    参数:
        video_file: 输入视频文件路径
        subtitle_file: 字幕文件路径 (SRT格式或纯文本)
        output_file: 输出视频文件路径 (None则自动生成)
        fontsize: 字体大小
        fontcolor: 字体颜色
        position: 字幕位置
        bg_opacity: 背景透明度
        use_srt: 是否使用SRT字幕文件（True）或纯文本叠加（False）
    """
    start_time = datetime.now()
    
    # 检查输入文件
    if not os.path.exists(video_file):
        logger.error(f"✗ 视频文件不存在: {video_file}")
        return False
    
    if not os.path.exists(subtitle_file):
        logger.error(f"✗ 字幕文件不存在: {subtitle_file}")
        return False
    
    # 生成输出文件名
    if output_file is None:
        video_path = Path(video_file)
        output_file = str(video_path.parent / f"{video_path.stem}_字幕{video_path.suffix}")
    
    logger.info(f"输入视频: {video_file}")
    logger.info(f"字幕文件: {subtitle_file}")
    logger.info(f"输出视频: {output_file}")
    logger.info(f"字幕模式: {'SRT字幕' if use_srt else '纯文本叠加'}")
    
    # 构建FFmpeg命令
    if use_srt:
        # 使用SRT字幕文件（需要转义路径）
        subtitle_path = subtitle_file.replace('\\', '/').replace(':', '\\:')
        
        # 使用subtitles滤镜
        subtitle_filter = (
            f"subtitles='{subtitle_path}':"
            f"force_style='FontName=SimHei,FontSize={fontsize},"
            f"PrimaryColour=&H{fontcolor_to_hex(fontcolor)}&,"
            f"OutlineColour=&H000000&,BackColour=&H80000000&,"
            f"BorderStyle=1,Outline=3,Shadow=2,MarginV=20,"
            f"WrapStyle=2,MaxLines=2'"
        )
        
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y',
            output_file
        ]
    else:
        # 使用纯文本叠加（旧方法）
        subtitle_text = read_subtitle_text(subtitle_file)
        if not subtitle_text:
            return False
        
        subtitle_filter = create_subtitle_filter(
            subtitle_text, fontsize, fontcolor, position, bg_opacity
        )
        
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-y',
            output_file
        ]
    
    logger.info("开始处理视频...")
    logger.info(f"FFmpeg命令: {' '.join(cmd)}")
    
    try:
        # 执行FFmpeg命令
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 实时输出进度
        for line in process.stdout:
            line = line.strip()
            if line:
                # FFmpeg的进度信息在stderr中，这里简单输出
                if 'time=' in line or 'frame=' in line:
                    sys.stdout.write(f"\r{line[:80]}")
                    sys.stdout.flush()
        
        process.wait()
        print()  # 换行
        
        if process.returncode == 0:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 获取输出文件大小
            output_size = os.path.getsize(output_file)
            output_size_mb = output_size / (1024 * 1024)
            
            logger.info("=" * 60)
            logger.info("✓ 视频处理完成！")
            logger.info(f"输出文件: {output_file}")
            logger.info(f"文件大小: {output_size_mb:.2f} MB")
            logger.info(f"处理耗时: {duration:.2f} 秒")
            logger.info("=" * 60)
            return True
        else:
            logger.error(f"✗ FFmpeg处理失败，退出代码: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"✗ 处理视频时出错: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='将字幕文本添加到视频文件中',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python add_subtitle_to_video.py video.mp4 subtitle.srt
  python add_subtitle_to_video.py video.mp4 subtitle.txt --text-mode
  python add_subtitle_to_video.py video.mp4 subtitle.srt -o output.mp4 --fontsize 32
        """
    )
    
    parser.add_argument('video_file', help='输入视频文件路径')
    parser.add_argument('subtitle_file', help='字幕文件路径 (SRT或纯文本)')
    parser.add_argument('-o', '--output', help='输出视频文件路径 (默认自动生成)')
    parser.add_argument('--fontsize', type=int, default=24, help='字体大小 (默认: 24)')
    parser.add_argument('--fontcolor', default='white', help='字体颜色 (默认: white)')
    parser.add_argument('--position', choices=['top', 'center', 'bottom'], 
                       default='bottom', help='字幕位置 (默认: bottom, 仅文本模式)')
    parser.add_argument('--bg-opacity', type=float, default=0.7, 
                       help='背景透明度 0-1 (默认: 0.7, 仅文本模式)')
    parser.add_argument('--text-mode', action='store_true',
                       help='使用纯文本叠加模式而不是SRT字幕')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("视频字幕添加工具")
    logger.info("=" * 60)
    
    # 检查FFmpeg
    if not check_ffmpeg():
        return False
    
    # 检查是否使用SRT模式
    use_srt = not args.text_mode and args.subtitle_file.lower().endswith('.srt')
    
    if use_srt:
        logger.info("使用SRT字幕模式")
    else:
        logger.info("使用纯文本叠加模式")
        # 读取字幕文本预览
        subtitle_text = read_subtitle_text(args.subtitle_file)
        if subtitle_text:
            preview = subtitle_text[:100] + ('...' if len(subtitle_text) > 100 else '')
            logger.info(f"字幕内容预览: {preview}")
    
    # 添加字幕到视频
    success = add_subtitle_to_video(
        args.video_file,
        args.subtitle_file,
        args.output,
        args.fontsize,
        args.fontcolor,
        args.position,
        args.bg_opacity,
        use_srt
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
