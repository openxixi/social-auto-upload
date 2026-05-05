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


def get_video_volume(video_path):
    """
    获取视频的平均音量
    """
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-af', 'volumedetect',
            '-vn',
            '-sn',
            '-dn',
            '-f', 'null',
            '-'
        ]
        
        # ffmpeg 的 volumedetect 输出在 stderr 中
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # volumedetect 的输出在 stderr 中
        output = result.stderr
        
        # 从输出中提取平均音量
        for line in output.split('\n'):
            if 'mean_volume' in line:
                # 示例: mean_volume: -20.5 dB
                parts = line.split(':')
                if len(parts) >= 2:
                    volume_str = parts[1].strip().split()[0]
                    try:
                        return float(volume_str)
                    except:
                        pass
        
        logger.warning(f"无法从输出中提取音量信息: {video_path}")
        return None
    except Exception as e:
        logger.error(f"获取音量失败: {e}")
        return None


def get_video_info(video_path):
    """
    获取视频的详细信息
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-show_format',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            # 获取视频流信息
            video_stream = None
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'video' and not video_stream:
                    video_stream = stream
                elif stream.get('codec_type') == 'audio' and not audio_stream:
                    audio_stream = stream
            
            if video_stream:
                info = {
                    'width': int(video_stream.get('width', 1920)),
                    'height': int(video_stream.get('height', 1080)),
                    'fps': eval(video_stream.get('r_frame_rate', '25/1')),
                    'bit_rate': int(data.get('format', {}).get('bit_rate', 5000000)),
                    'codec': video_stream.get('codec_name', 'h264'),
                }
                
                # 打印视频信息用于调试
                logger.info(f"视频信息: {info['width']}x{info['height']}, {info['fps']}fps, 码率:{info['bit_rate']/1000}kbps")
                
                if audio_stream:
                    info['audio_bit_rate'] = int(audio_stream.get('bit_rate', 192000))
                    info['audio_sample_rate'] = int(audio_stream.get('sample_rate', 44100))
                else:
                    info['audio_bit_rate'] = 192000
                    info['audio_sample_rate'] = 44100
                
                return info
        
        return None
    except Exception as e:
        logger.error(f"获取视频信息失败: {e}")
        return None


def concat_videos(videos, output, cover=None, cover_duration=3, resolution="auto", fit_mode="pad"):
    """
    方式1: 前后拼接多个视频（简单连接）
    如果提供封面，则按照 封面 -> video1 -> video2 -> ... 的顺序拼接
    
    Args:
        videos: 视频文件路径列表
        output: 输出文件路径
        cover: 封面图片路径（可选）
        cover_duration: 封面显示时长（秒）
        resolution: 输出分辨率，"auto" 表示使用第一个视频的分辨率，或指定如 "1920x1080"
    """
    if not videos or len(videos) == 0:
        logger.error("至少需要提供1个视频文件")
        return False
    
    logger.info(f"正在拼接 {len(videos)} 个视频（前后连接）...")
    
    temp_cover_video = None
    
    try:
        # 获取第一个视频的信息
        video_info = get_video_info(videos[0])
        
        if not video_info:
            logger.warning("⚠️ 无法获取视频信息，使用高质量默认参数")
            video_info = {
                'width': 1920,
                'height': 1080,
                'fps': 25,
                'bit_rate': 8000000,    # 提高到 8000kbps
                'audio_bit_rate': 192000,
                'audio_sample_rate': 44100
            }
            logger.info(f"默认参数: 码率 8000kbps")
        else:
            logger.info(f"✓ 成功获取视频信息: 码率 {video_info['bit_rate']/1000}kbps")
        
        # 如果指定了分辨率，使用指定的；否则使用第一个视频的
        if resolution == "auto":
            target_width = video_info['width']
            target_height = video_info['height']
            logger.info(f"使用第一个视频的分辨率: {target_width}x{target_height}")
        else:
            target_width, target_height = resolution.split('x')
            target_width, target_height = int(target_width), int(target_height)
            logger.info(f"使用指定分辨率: {target_width}x{target_height}")
        
        target_resolution = f"{target_width}:{target_height}"
        target_fps = int(video_info['fps'])
        video_bitrate = int(video_info['bit_rate'] / 1000)  # 转换为 kbps
        audio_bitrate = int(video_info['audio_bit_rate'] / 1000)  # 转换为 kbps
        audio_sample_rate = video_info['audio_sample_rate']
        
        logger.info(f"视频参数: {target_width}x{target_height}, {target_fps}fps, 视频码率:{video_bitrate}k, 音频码率:{audio_bitrate}k")
        logger.info(f"填充模式: {fit_mode} ({'裁剪填满' if fit_mode == 'crop' else '添加黑边'})")
        
        # 根据fit_mode选择滤镜
        if fit_mode == "crop":
            # 裁剪模式：放大到能覆盖目标尺寸，然后从中心裁剪
            # 明确指定裁剪坐标确保在所有FFmpeg版本中都居中裁剪
            fit_filter = f"scale={target_resolution}:force_original_aspect_ratio=increase,crop={target_resolution}:(in_w-{target_width})/2:(in_h-{target_height})/2"
        else:
            # pad模式：缩小到能装入目标尺寸，然后填充黑边
            fit_filter = f"scale={target_resolution}:force_original_aspect_ratio=decrease,pad={target_resolution}:(ow-iw)/2:(oh-ih)/2"
        
        # 获取所有视频的音量，用于音量匹配
        logger.info("正在分析视频音量...")
        volumes = []
        for i, video in enumerate(videos, 1):
            volume = get_video_volume(video)
            volumes.append(volume)
            if volume is not None:
                logger.info(f"视频{i}平均音量: {volume:.1f} dB")
        
        # 计算每个视频的音量调整值
        volume_adjustments = []
        valid_volumes = [v for v in volumes if v is not None]
        
        if valid_volumes:
            # 找出音量最大的（分贝更高的，注意-14 > -33.7）
            target_volume = max(valid_volumes)
            logger.info(f"目标音量（以更大的为准）: {target_volume:.1f} dB")
            
            # 计算每个视频需要调整的音量
            for i, volume in enumerate(volumes, 1):
                if volume is not None:
                    adjustment = target_volume - volume
                    volume_adjustments.append(adjustment)
                    if abs(adjustment) > 0.5:
                        logger.info(f"将视频{i}音量调整: {adjustment:+.1f} dB")
                else:
                    volume_adjustments.append(0)
        else:
            logger.warning("无法获取音量信息，不进行音量调整")
            volume_adjustments = [0] * len(videos)
        
        # 构建输入参数和filter
        inputs = []
        scale_filters = []
        audio_filters = []
        concat_inputs = []
        n = 0
        
        # 如果有封面，先处理封面
        if cover:
            logger.info(f"正在处理封面（显示{cover_duration}秒）...")
            temp_cover_video = "temp_cover_with_audio.mp4"
            
            # 将封面图片转换为有静音音频的视频（使用高码率）
            cmd_cover = [
                'ffmpeg',
                '-loop', '1',
                '-i', cover,
                '-f', 'lavfi',
                '-i', f'anullsrc=channel_layout=stereo:sample_rate={audio_sample_rate}',
                '-c:v', 'libx264',
                '-t', str(cover_duration),
                '-c:a', 'aac',
                '-b:v', f'{video_bitrate}k',    # 使用与原视频相同的码率
                '-b:a', f'{audio_bitrate}k',    # 使用与原视频相同的音频码率
                '-shortest',
                '-pix_fmt', 'yuv420p',
                '-r', str(target_fps),
                '-vf', fit_filter,
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
            audio_filters.append(f'[{n}:a]anull[a{n}]')  # 封面音频（静音）
            concat_inputs.append(f'[v{n}][a{n}]')
            n += 1
            logger.info("✓ 封面处理完成")
        
        # 添加所有视频
        for i, video in enumerate(videos):
            inputs.extend(['-i', video])
            # 将视频缩放到指定尺寸（根据fit_mode选择pad或crop）
            scale_filters.append(f'[{n}:v]{fit_filter},setsar=1,fps={target_fps}[v{n}]')
            # 调整视频的音量（如果需要）
            if abs(volume_adjustments[i]) > 0.5:  # 只有差异大于0.5dB时才调整
                audio_filters.append(f'[{n}:a]volume={volume_adjustments[i]}dB[a{n}]')
            else:
                audio_filters.append(f'[{n}:a]anull[a{n}]')  # 差异很小，不调整
            concat_inputs.append(f'[v{n}][a{n}]')
            n += 1
            logger.info(f"  添加视频 {i+1}/{len(videos)}: {os.path.basename(video)}")
        
        # 构建完整的 filter_complex
        all_filters = scale_filters + audio_filters
        filter_complex = ';'.join(all_filters) + ';' + ''.join(concat_inputs) + f'concat=n={n}:v=1:a=1[outv][outa]'
        
        # 高质量编码参数（使用第一个视频的参数）
        cmd = [
            'ffmpeg'
        ] + inputs + [
            '-filter_complex', filter_complex,
            '-map', '[outv]',
            '-map', '[outa]',
            # 视频编码参数 - 使用原视频码率保证质量
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', f'{video_bitrate}k',        # 使用第一个视频的码率
            '-maxrate', f'{int(video_bitrate * 1.3)}k',  # 最大码率
            '-bufsize', f'{int(video_bitrate * 2)}k',     # 缓冲区大小
            '-pix_fmt', 'yuv420p',
            '-profile:v', 'high',
            '-level', '4.1',
            '-r', str(target_fps),              # 使用第一个视频的帧率
            # 音频编码参数
            '-c:a', 'aac',
            '-b:a', f'{audio_bitrate}k',        # 使用第一个视频的音频码率
            '-ar', str(audio_sample_rate),       # 使用第一个视频的采样率
            # 色彩空间和元数据
            '-colorspace', 'bt709',
            '-color_primaries', 'bt709',
            '-color_trc', 'bt709',
            '-movflags', '+faststart',
            '-y',
            output
        ]
        
        logger.info(f"正在拼接视频（使用第一个视频的参数）...")
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
        description="视频融合工具 - 使用FFmpeg将多段视频融合",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 前后拼接（支持多个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4
  python merge_videos.py video1.mp4 video2.mp4 video3.mp4 video4.mp4 -o output.mp4
  
  # 左右并排（仅支持2个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode side
  
  # 上下排列（仅支持2个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode stack
  
  # 画中画（video2叠加在video1右上角，仅支持2个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode pip
  
  # 画中画（自定义位置和大小）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode pip --position bottom-left --scale 0.25
  
  # 混合叠加（仅支持2个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode blend --opacity 0.6
  
  # 交叉淡化过渡（仅支持2个视频）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --mode crossfade --duration 2
  
  # 添加封面（在视频开头添加封面图片）
  python merge_videos.py video1.mp4 video2.mp4 -o output.mp4 --cover cover.jpg
  python merge_videos.py video1.mp4 video2.mp4 video3.mp4 -o output.mp4 --cover cover.png --cover-duration 5
  
  # 使用第一个视频的分辨率和参数（默认，自动匹配）
  python merge_videos.py video1.mp4 video2.mp4 video3.mp4
  
  # 指定输出分辨率（1080p横屏）
  python merge_videos.py video1.mp4 video2.mp4 video3.mp4 --resolution 1920x1080
  
  # 指定输出分辨率（1080p竖屏，抖音常用）
  python merge_videos.py video1.mp4 video2.mp4 --resolution 1080x1920 --cover cover.jpg
  
  # 指定输出分辨率（720p）
  python merge_videos.py video1.mp4 video2.mp4 --resolution 1280x720
        """
    )
    
    parser.add_argument("videos", nargs='+', help="要合并的视频文件（支持多个）")
    
    # 默认输出文件名
    default_output = "tmp.mp4"
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
    
    # 分辨率参数
    parser.add_argument("--resolution", "-r",
                        choices=["auto", "1920x1080", "1280x720", "1080x1920", "720x1280", "3840x2160"],
                        default="auto",
                        help="输出视频分辨率（auto=使用第一个视频的分辨率(默认), 1920x1080=1080p横屏, 1080x1920=1080p竖屏, 1280x720=720p, 3840x2160=4K）")
    
    # 填充模式参数
    parser.add_argument("--fit-mode", "-f",
                        choices=["pad", "crop"],
                        default="pad",
                        help="视频适配模式（默认: pad添加黑边保留完整内容, crop=裁剪填满适合抖音全屏）")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if len(args.videos) == 0:
        logger.error("错误: 至少需要提供1个视频文件")
        return False
    
    for video in args.videos:
        if not os.path.exists(video):
            logger.error(f"错误: 视频文件不存在: {video}")
            return False
    
    # 检查封面文件
    if args.cover and not os.path.exists(args.cover):
        logger.error(f"错误: 封面图片不存在: {args.cover}")
        return False
    
    # 检查FFmpeg
    if not check_ffmpeg():
        return False
    
    logger.info(f"输入视频数量: {len(args.videos)}")
    for i, video in enumerate(args.videos, 1):
        logger.info(f"  视频{i}: {video}")
    logger.info(f"融合模式: {args.mode}")
    if args.cover:
        logger.info(f"封面图片: {args.cover} (显示{args.cover_duration}秒)")
    logger.info(f"输出文件: {args.output}")
    logger.info("-" * 60)
    
    # 根据模式执行相应的融合操作
    success = False
    if args.mode == "concat":
        # concat模式支持多个视频和直接添加封面
        success = concat_videos(args.videos, args.output, 
                               args.cover, args.cover_duration, args.resolution, args.fit_mode)
    elif args.mode in ["side", "stack", "pip", "blend", "crossfade"]:
        # 其他模式仅支持2个视频
        if len(args.videos) != 2:
            logger.error(f"错误: {args.mode} 模式仅支持2个视频文件，但提供了{len(args.videos)}个")
            return False
        
        if args.mode == "side":
            success = side_by_side_videos(args.videos[0], args.videos[1], args.output)
        elif args.mode == "stack":
            success = top_bottom_videos(args.videos[0], args.videos[1], args.output)
        elif args.mode == "pip":
            success = picture_in_picture(args.videos[0], args.videos[1], args.output,
                                        args.position, args.scale)
        elif args.mode == "blend":
            success = blend_videos(args.videos[0], args.videos[1], args.output, args.opacity)
        elif args.mode == "crossfade":
            success = crossfade_videos(args.videos[0], args.videos[1], args.output, args.duration)
    
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
