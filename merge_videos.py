#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频融合工具
使用FFmpeg将两段视频融合到一起
"""

import os
import sys
import argparse
import subprocess
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_ffmpeg():
    """检查FFmpeg是否已安装"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            logger.info("✓ FFmpeg已安装")
            return True
    except FileNotFoundError:
        logger.error("错误: 未找到FFmpeg")
        logger.info("请安装FFmpeg: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        logger.error(f"检查FFmpeg失败: {e}")
        return False


def concat_videos(video1, video2, output, cover=None, cover_duration=3):
    """
    方式1: 前后拼接两个视频（简单连接）
    如果提供封面，则按照 封面 -> video1 -> video2 的顺序拼接
    """
    logger.info("正在拼接视频（前后连接）...")
    
    temp_cover_video = None
    
    try:
        # 构建输入参数和filter
        inputs = []
        scale_filters = []
        concat_inputs = []
        n = 0
        
        # 如果有封面，先处理封面
        if cover:
            logger.info(f"正在处理封面（显示{cover_duration}秒）...")
            temp_cover_video = "temp_cover_with_audio.mp4"
            
            # 将封面图片转换为有静音音频的视频
            cmd_cover = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover,
                '-f', 'lavfi',
                '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-c:v', 'libx264',
                '-t', str(cover_duration),
                '-c:a', 'aac',
                '-shortest',
                '-pix_fmt', 'yuv420p',
                '-r', '25',
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-y',
                temp_cover_video
            ]
            
            result = subprocess.run(cmd_cover, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"转换封面失败: {result.stderr}")
                return False
            
            inputs.extend(['-i', temp_cover_video])
            # 封面已经是标准尺寸，直接使用
            scale_filters.append(f'[{n}:v]setsar=1[v{n}]')
            concat_inputs.append(f'[v{n}][{n}:a]')
            n += 1
            logger.info("✓ 封面处理完成")
        
        # 添加视频1
        inputs.extend(['-i', video1])
        # 将视频1缩放到标准尺寸
        scale_filters.append(f'[{n}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25[v{n}]')
        concat_inputs.append(f'[v{n}][{n}:a]')
        n += 1
        
        # 添加视频2
        inputs.extend(['-i', video2])
        # 将视频2缩放到标准尺寸
        scale_filters.append(f'[{n}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25[v{n}]')
        concat_inputs.append(f'[v{n}][{n}:a]')
        n += 1
        
        # 构建完整的 filter_complex
        filter_complex = ';'.join(scale_filters) + ';' + ''.join(concat_inputs) + f'concat=n={n}:v=1:a=1[outv][outa]'
        
        cmd = [
            'ffmpeg'
        ] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-y',
            output
        ]
        
        logger.info("正在拼接视频（统一分辨率为1920x1080）...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"✓ 视频拼接成功: {output}")
            return True
        else:
            logger.error(f"拼接失败: {result.stderr}")
            return False
            
    finally:
        # 清理临时文件
        if temp_cover_video and os.path.exists(temp_cover_video):
            os.remove(temp_cover_video)


def side_by_side_videos(video1, video2, output):
    """
    方式2: 左右并排显示两个视频
    """
    logger.info("正在融合视频（左右并排）...")
    
    cmd = [
        'ffmpeg',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        '[0:v]scale=iw/2:ih[v0];[1:v]scale=iw/2:ih[v1];[v0][v1]hstack=inputs=2',
        '-y',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ 视频融合成功: {output}")
        return True
    else:
        logger.error(f"融合失败: {result.stderr}")
        return False


def top_bottom_videos(video1, video2, output):
    """
    方式3: 上下排列显示两个视频
    """
    logger.info("正在融合视频（上下排列）...")
    
    cmd = [
        'ffmpeg',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        '[0:v]scale=iw:ih/2[v0];[1:v]scale=iw:ih/2[v1];[v0][v1]vstack=inputs=2',
        '-y',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ 视频融合成功: {output}")
        return True
    else:
        logger.error(f"融合失败: {result.stderr}")
        return False


def picture_in_picture(video1, video2, output, position="top-right", scale=0.3):
    """
    方式4: 画中画效果（video2叠加在video1上）
    
    Args:
        video1: 背景视频
        video2: 小窗口视频
        output: 输出文件
        position: 位置 (top-right, top-left, bottom-right, bottom-left, center)
        scale: 小窗口缩放比例 (0-1)
    """
    logger.info(f"正在融合视频（画中画，位置: {position}）...")
    
    # 根据位置生成overlay参数
    positions = {
        'top-right': 'W-w-10:10',
        'top-left': '10:10',
        'bottom-right': 'W-w-10:H-h-10',
        'bottom-left': '10:H-h-10',
        'center': '(W-w)/2:(H-h)/2'
    }
    
    overlay_pos = positions.get(position, 'W-w-10:10')
    
    cmd = [
        'ffmpeg',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        f'[1:v]scale=iw*{scale}:ih*{scale}[pip];[0:v][pip]overlay={overlay_pos}',
        '-y',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ 视频融合成功: {output}")
        return True
    else:
        logger.error(f"融合失败: {result.stderr}")
        return False


def blend_videos(video1, video2, output, opacity=0.5):
    """
    方式5: 混合叠加两个视频（透明度混合）
    """
    logger.info(f"正在融合视频（混合叠加，透明度: {opacity}）...")
    
    cmd = [
        'ffmpeg',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        f'[0:v][1:v]blend=all_mode=overlay:all_opacity={opacity}',
        '-y',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ 视频融合成功: {output}")
        return True
    else:
        logger.error(f"融合失败: {result.stderr}")
        return False


def crossfade_videos(video1, video2, output, duration=1):
    """
    方式6: 交叉淡入淡出过渡
    """
    logger.info(f"正在融合视频（交叉淡化，过渡时长: {duration}秒）...")
    
    cmd = [
        'ffmpeg',
        '-i', video1,
        '-i', video2,
        '-filter_complex',
        f'[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0[v]',
        '-map', '[v]',
        '-y',
        output
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info(f"✓ 视频融合成功: {output}")
        return True
    else:
        logger.error(f"融合失败: {result.stderr}")
        return False


def add_cover_to_video(video, cover_image, output, duration=0.5):
    """
    在视频开头添加封面图片
    
    Args:
        video: 输入视频文件
        cover_image: 封面图片文件
        output: 输出文件
        duration: 封面显示时长（秒）
    """
    logger.info(f"正在添加封面（显示{duration}秒）...")
    
    # 先将图片转换为视频片段
    temp_cover_video = "temp_cover.mp4"
    
    try:
        # 步骤1: 将封面图片转换为短视频
        cmd1 = [
            'ffmpeg',
            '-loop', '1',
            '-i', cover_image,
            '-c:v', 'libx264',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
            '-y',
            temp_cover_video
        ]
        
        logger.info("步骤1: 转换封面图片为视频...")
        result1 = subprocess.run(cmd1, capture_output=True, text=True)
        
        if result1.returncode != 0:
            logger.error(f"转换封面失败: {result1.stderr}")
            return False
        
        # 步骤2: 将封面视频和原视频拼接
        temp_list = "temp_cover_list.txt"
        with open(temp_list, 'w', encoding='utf-8') as f:
            f.write(f"file '{os.path.abspath(temp_cover_video)}'\n")
            f.write(f"file '{os.path.abspath(video)}'\n")
        
        cmd2 = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_list,
            '-c', 'copy',
            '-y',
            output
        ]
        
        logger.info("步骤2: 拼接封面和视频...")
        result2 = subprocess.run(cmd2, capture_output=True, text=True)
        
        # 清理临时文件
        if os.path.exists(temp_list):
            os.remove(temp_list)
        if os.path.exists(temp_cover_video):
            os.remove(temp_cover_video)
        
        if result2.returncode == 0:
            logger.info(f"✓ 封面添加成功: {output}")
            return True
        else:
            logger.error(f"拼接失败: {result2.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"添加封面失败: {e}")
        # 清理临时文件
        if os.path.exists(temp_cover_video):
            os.remove(temp_cover_video)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="视频融合工具 - 使用FFmpeg将两段视频融合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 前后拼接（默认）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4
  
  # 左右并排
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode side
  
  # 上下排列
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode stack
  
  # 画中画（video2叠加在video1右上角）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode pip
  
  # 画中画（自定义位置和大小）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode pip --position bottom-left --scale 0.25
  
  # 混合叠加
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode blend --opacity 0.6
  
  # 交叉淡化过渡
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode crossfade --duration 2
  
  # 添加封面（在视频开头添加封面图片）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --cover cover.jpg
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --cover cover.png --cover-duration 5
        """
    )
    
    parser.add_argument("video1", help="第一个视频文件")
    parser.add_argument("video2", help="第二个视频文件")
    
    # 生成默认输出文件名
    default_output = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    parser.add_argument("--output", "-o", default=default_output,
                        help=f"输出文件路径（默认: {default_output}）")
    
    parser.add_argument("--mode", "-m",
                        choices=["concat", "side", "stack", "pip", "blend", "crossfade"],
                        default="concat",
                        help="""融合模式:
                        concat=前后拼接(默认),
                        side=左右并排,
                        stack=上下排列,
                        pip=画中画,
                        blend=混合叠加,
                        crossfade=交叉淡化""")
    
    # 画中画相关参数
    parser.add_argument("--position", "-p",
                        choices=["top-right", "top-left", "bottom-right", "bottom-left", "center"],
                        default="top-right",
                        help="画中画位置（仅mode=pip时有效）")
    parser.add_argument("--scale", "-s", type=float, default=0.3,
                        help="画中画缩放比例，0-1之间（仅mode=pip时有效，默认0.3）")
    
    # 混合模式参数
    parser.add_argument("--opacity", type=float, default=0.5,
                        help="混合透明度，0-1之间（仅mode=blend时有效，默认0.5）")
    
    # 交叉淡化参数
    parser.add_argument("--duration", "-d", type=float, default=1,
                        help="过渡时长（秒）（仅mode=crossfade时有效，默认1秒）")
    
    # 封面相关参数
    parser.add_argument("--cover", "-c", help="封面图片文件（jpg/png），在视频开头显示")
    parser.add_argument("--cover-duration", type=float, default=0.5,
                        help="封面显示时长（秒）（默认0.5秒）")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.video1):
        logger.error(f"错误: 视频文件不存在: {args.video1}")
        return False
    
    if not os.path.exists(args.video2):
        logger.error(f"错误: 视频文件不存在: {args.video2}")
        return False
    
    # 检查封面文件
    if args.cover and not os.path.exists(args.cover):
        logger.error(f"错误: 封面图片不存在: {args.cover}")
        return False
    
    # 检查FFmpeg
    if not check_ffmpeg():
        return False
    
    logger.info(f"输入视频1: {args.video1}")
    logger.info(f"输入视频2: {args.video2}")
    logger.info(f"融合模式: {args.mode}")
    if args.cover:
        logger.info(f"封面图片: {args.cover} (显示{args.cover_duration}秒)")
    logger.info(f"输出文件: {args.output}")
    logger.info("-" * 60)
    
    # 根据模式执行相应的融合操作
    success = False
    if args.mode == "concat":
        # concat模式支持直接添加封面
        success = concat_videos(args.video1, args.video2, args.output, 
                               args.cover, args.cover_duration)
    elif args.mode == "side":
        success = side_by_side_videos(args.video1, args.video2, args.output)
    elif args.mode == "stack":
        success = top_bottom_videos(args.video1, args.video2, args.output)
    elif args.mode == "pip":
        success = picture_in_picture(args.video1, args.video2, args.output,
                                    args.position, args.scale)
    elif args.mode == "blend":
        success = blend_videos(args.video1, args.video2, args.output, args.opacity)
    elif args.mode == "crossfade":
        success = crossfade_videos(args.video1, args.video2, args.output, args.duration)
    
    if success:
        # 如果是非concat模式且需要添加封面
        if args.cover and args.mode != "concat":
            logger.info("-" * 60)
            logger.info("开始添加封面...")
            
            # 创建临时文件用于保存有封面的视频
            temp_output = args.output.replace('.mp4', '_temp.mp4')
            os.rename(args.output, temp_output)
            
            cover_success = add_cover_to_video(
                temp_output, 
                args.cover, 
                args.output,
                args.cover_duration
            )
            
            # 删除临时文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            if not cover_success:
                logger.error("添加封面失败")
                return False
        
        file_size = os.path.getsize(args.output)
        logger.info("-" * 60)
        logger.info(f"✓✓✓ 完成! 输出文件: {args.output}")
        logger.info(f"文件大小: {file_size / (1024*1024):.2f} MB")
        return True
    else:
        logger.error("视频融合失败")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
