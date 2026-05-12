#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频增强脚本 - 提高抖音原创性
添加背景音乐、文字水印、视觉效果等
"""

import os
import sys
import argparse
import subprocess
import logging
import random
from pathlib import Path

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


def add_background_music(video_path, output_path, music_dir="./bgm", volume=0.15):
    """
    添加背景音乐
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        music_dir: 背景音乐目录
        volume: 音乐音量 (0.0-1.0)，建议0.1-0.2
    """
    music_path_obj = Path(music_dir)
    
    if not music_path_obj.exists():
        logger.warning(f"背景音乐目录不存在: {music_dir}，跳过添加背景音乐")
        # 直接复制文件
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # 查找音乐文件
    music_files = list(music_path_obj.glob('*.mp3')) + list(music_path_obj.glob('*.m4a')) + list(music_path_obj.glob('*.wav'))
    
    if not music_files:
        logger.warning(f"背景音乐目录中没有音乐文件，跳过添加背景音乐")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    # 随机选择一个音乐文件
    music_file = random.choice(music_files)
    logger.info(f"选择背景音乐: {music_file.name}")
    
    temp_output = output_path + ".temp.mp4"
    
    try:
        # 混合原视频音频和背景音乐
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', str(music_file),
            '-filter_complex',
            f'[0:a]volume=1.0[a0];[1:a]volume={volume}[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=2',
            '-c:v', 'copy',
            '-shortest',  # 以最短的流为准
            '-y', temp_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 替换为最终输出
        os.replace(temp_output, output_path)
        logger.info("✓ 背景音乐添加完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"添加背景音乐失败: {e.stderr.decode('utf-8', errors='ignore')}")
        # 如果失败，直接复制原文件
        import shutil
        shutil.copy2(video_path, output_path)
    except Exception as e:
        logger.error(f"添加背景音乐异常: {e}")
        import shutil
        shutil.copy2(video_path, output_path)
    
    return output_path


def add_text_watermark(video_path, output_path, text="", fontsize=35):
    """
    添加动态文字水印
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        text: 水印文字（空则使用默认）
        fontsize: 字体大小
    """
    if not text:
        # 可以使用一些通用的文字
        texts = [
            "每天学习一点",
            "关注不迷路",
            "分享生活日常",
            "记录美好瞬间",
            "距离一亿人还差一个关注",
            "原创内容，欢迎点赞",
            "感谢观看，喜欢关注",
            "生活不止眼前的苟且，还有不买海尔",
            "每一天都是新的开始",
            "王侯将相宁有种乎",
            "路漫漫其修远兮，余喜将上下而求索",
            "天行健，余喜以自强不息",
            "地势坤，余喜以厚德载物",
            "革命尚未成功，余喜仍需努力",
            "黑夜给了我黑色的眼睛，余喜用它寻找光明",
            "卑鄙是高尚者的通行证，高尚是卑鄙者的墓志铭",
            "不买海尔，天下为公",
            "持续号召一亿人不买海尔",

        ]
        text = random.choice(texts)
    
    logger.info(f"添加文字水印: {text}")
    
    temp_output = output_path + ".temp2.mp4"
    
    try:
        # 在视频右下角添加半透明文字
        # 使用系统字体，Windows 和 Linux 都支持
        fontfile = "/Windows/Fonts/msyh.ttc" if os.path.exists("/Windows/Fonts/msyh.ttc") else ""
        
        if fontfile:
            fontfile_param = f":fontfile={fontfile}"
        else:
            fontfile_param = ""
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf',
            f"drawtext=text='{text}':x=w-tw-30:y=h-th-100:fontsize={fontsize}:fontcolor=white@0.7:box=1:boxcolor=black@0.4:boxborderw=8{fontfile_param}",
            '-c:a', 'copy',
            '-y', temp_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 替换为最终输出
        os.replace(temp_output, output_path)
        logger.info("✓ 文字水印添加完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"添加文字水印失败: {e.stderr.decode('utf-8', errors='ignore')}")
        # 如果失败，使用输入文件
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    except Exception as e:
        logger.error(f"添加文字水印异常: {e}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    
    return output_path


def add_filter_effect(video_path, output_path, filter_name="vintage"):
    """
    添加滤镜效果
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        filter_name: 滤镜名称
            - vintage: 复古效果（棕褐色调）
            - vibrant: 鲜艳效果（增加饱和度）
            - cool: 冷色调（蓝色调）
            - warm: 暖色调（橙黄色调）
            - sharp: 锐化效果
            - soft: 柔和效果（轻微模糊）
            - bright: 明亮效果
            - contrast: 高对比度
            - bw: 黑白效果
            - cinematic: 电影感（暗角+色彩）
    """
    logger.info(f"添加滤镜效果: {filter_name}")
    
    # 定义不同的滤镜效果
    filters = {
        'vintage': 'colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.1:brightness=0.05',
        'vibrant': 'eq=saturation=1.4:contrast=1.1',
        'cool': 'colortemperature=8000,eq=saturation=1.2',
        'warm': 'colortemperature=3500,eq=saturation=1.2',
        'sharp': 'unsharp=5:5:1.0:5:5:0.0',
        'soft': 'gblur=sigma=0.8',
        'bright': 'eq=brightness=0.08:contrast=1.05',
        'contrast': 'eq=contrast=1.3:saturation=1.15',
        'bw': 'hue=s=0',
        'cinematic': 'vignette=angle=PI/4,eq=contrast=1.2:saturation=0.9:brightness=-0.03'
    }
    
    if filter_name not in filters:
        logger.warning(f"未知的滤镜名称: {filter_name}，使用默认滤镜 vintage")
        filter_name = 'vintage'
    
    filter_string = filters[filter_name]
    temp_output = output_path + ".temp_filter.mp4"
    
    try:
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf', filter_string,
            '-c:a', 'copy',
            '-y', temp_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 替换为最终输出
        os.replace(temp_output, output_path)
        logger.info(f"✓ 滤镜效果 '{filter_name}' 添加完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"添加滤镜效果失败: {e.stderr.decode('utf-8', errors='ignore')}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    except Exception as e:
        logger.error(f"添加滤镜效果异常: {e}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    
    return output_path


def adjust_playback_speed(video_path, output_path, speed=1.0):
    """
    调整播放速度（提高原创性的有效方法）
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        speed: 播放速度倍数
            - 1.05: 加速5%（推荐，不易察觉）
            - 0.95: 减速5%（推荐，不易察觉）
            - 1.1: 加速10%
            - 0.9: 减速10%
            注意：速度范围建议在0.9-1.1之间，避免过于明显
    """
    if speed == 1.0:
        logger.info("播放速度为1.0，跳过速度调整")
        import shutil
        shutil.copy2(video_path, output_path)
        return output_path
    
    logger.info(f"调整播放速度: {speed}x")
    
    temp_output = output_path + ".temp_speed.mp4"
    
    try:
        # 计算 setpts 和 atempo 参数
        # setpts 用于视频，atempo 用于音频
        video_speed = 1.0 / speed  # setpts 参数是倒数
        audio_speed = speed
        
        # 如果速度变化超过2倍，需要链式使用atempo
        # 但通常我们不会超过1.1倍，所以直接使用即可
        if 0.5 <= audio_speed <= 2.0:
            audio_filter = f"atempo={audio_speed}"
        else:
            # 对于极端速度，需要分解
            logger.warning(f"播放速度 {speed} 超出推荐范围，可能效果不佳")
            audio_filter = f"atempo={audio_speed}"
        
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter_complex',
            f"[0:v]setpts={video_speed}*PTS[v];[0:a]{audio_filter}[a]",
            '-map', '[v]',
            '-map', '[a]',
            '-y', temp_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 替换为最终输出
        os.replace(temp_output, output_path)
        logger.info(f"✓ 播放速度调整完成 ({speed}x)")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"调整播放速度失败: {e.stderr.decode('utf-8', errors='ignore')}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    except Exception as e:
        logger.error(f"调整播放速度异常: {e}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    
    return output_path


def add_slight_zoom(video_path, output_path, zoom_factor=0.0008):
    """
    添加轻微的缩放效果
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        zoom_factor: 缩放因子，越大缩放越明显（建议0.0005-0.002）
    """
    logger.info(f"添加轻微缩放效果")
    
    temp_output = output_path + ".temp3.mp4"
    
    try:
        # 使用 zoompan 滤镜添加缓慢放大效果
        # z='min(zoom+0.0008,1.15)' 表示最多放大到1.15倍
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vf',
            f"zoompan=z='min(zoom+{zoom_factor},1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
            '-c:a', 'copy',
            '-y', temp_output
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # 替换为最终输出
        os.replace(temp_output, output_path)
        logger.info("✓ 缩放效果添加完成")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"添加缩放效果失败: {e.stderr.decode('utf-8', errors='ignore')}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    except Exception as e:
        logger.error(f"添加缩放效果异常: {e}")
        if os.path.exists(video_path) and not os.path.exists(output_path):
            import shutil
            shutil.copy2(video_path, output_path)
    
    return output_path


def enhance_video(input_video, output_video, 
                  add_music=True, add_text=True, add_zoom=False, add_filter=False,
                  music_dir="./bgm", text="", music_volume=0.15, filter_name="vintage",
                  playback_speed=1.0, zoom_factor=0.0008):
    """
    综合增强视频
    
    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        add_music: 是否添加背景音乐
        add_text: 是否添加文字水印
        add_zoom: 是否添加缩放效果（较慢）
        add_filter: 是否添加滤镜效果
        music_dir: 背景音乐目录
        text: 水印文字
        music_volume: 音乐音量
        filter_name: 滤镜名称
        playback_speed: 播放速度（1.0为正常，推荐0.95-1.05）
        zoom_factor: 缩放因子（建议0.0005-0.002，默认0.0008）
    """
    logger.info("=" * 60)
    logger.info("开始视频增强处理")
    logger.info("=" * 60)
    
    if not os.path.exists(input_video):
        logger.error(f"输入视频不存在: {input_video}")
        return False
    
    # 创建临时文件
    temp_dir = Path("./temp_enhance")
    temp_dir.mkdir(exist_ok=True)
    
    current_video = input_video
    step = 1
    
    # 步骤1: 调整播放速度（如果需要的话，放在第一步）
    if playback_speed != 1.0:
        logger.info(f"步骤{step}: 调整播放速度")
        temp_video = str(temp_dir / f"step{step}.mp4")
        current_video = adjust_playback_speed(current_video, temp_video, playback_speed)
        step += 1
    
    # 步骤2: 添加滤镜效果
    if add_filter:
        logger.info(f"步骤{step}: 添加滤镜效果")
        temp_video = str(temp_dir / f"step{step}.mp4")
        current_video = add_filter_effect(current_video, temp_video, filter_name)
        step += 1
    
    # 步骤3: 添加背景音乐
    if add_music:
        logger.info(f"步骤{step}: 添加背景音乐")
        temp_video = str(temp_dir / f"step{step}.mp4")
        current_video = add_background_music(current_video, temp_video, music_dir, music_volume)
        step += 1
    
    # 步骤4: 添加文字水印
    if add_text:
        logger.info(f"步骤{step}: 添加文字水印")
        temp_video = str(temp_dir / f"step{step}.mp4")
        current_video = add_text_watermark(current_video, temp_video, text)
        step += 1
    
    # 步骤5: 添加缩放效果（可选，比较耗时）
    if add_zoom:
        logger.info(f"步骤{step}: 添加缩放效果")
        temp_video = str(temp_dir / f"step{step}.mp4")
        current_video = add_slight_zoom(current_video, temp_video, zoom_factor)
        step += 1
    
    # 复制最终结果
    if current_video != output_video:
        import shutil
        shutil.copy2(current_video, output_video)
    
    # 清理临时文件
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass
    
    logger.info("=" * 60)
    logger.info(f"✓ 视频增强完成: {output_video}")
    logger.info("=" * 60)
    
    return True


def main():
    parser = argparse.ArgumentParser(description='视频增强 - 提高抖音原创性')
    parser.add_argument('input', help='输入视频路径')
    parser.add_argument('-o', '--output', required=True, help='输出视频路径')
    parser.add_argument('--no-music', action='store_true', help='不添加背景音乐')
    parser.add_argument('--no-text', action='store_true', help='不添加文字水印')
    parser.add_argument('--add-zoom', action='store_true', help='添加缩放效果（较慢）')
    parser.add_argument('--zoom-factor', type=float, default=0.0008,
                        help='缩放因子，越大缩放越明显（建议0.0005-0.002，默认0.0008）')
    parser.add_argument('--add-filter', action='store_true', help='添加滤镜效果')
    parser.add_argument('--filter', dest='filter_name', default='vintage', 
                        choices=['vintage', 'vibrant', 'cool', 'warm', 'sharp', 'soft', 'bright', 'contrast', 'bw', 'cinematic'],
                        help='滤镜类型（默认: vintage）')
    parser.add_argument('--speed', type=float, default=1.0, 
                        help='播放速度倍数（推荐0.95-1.05，默认1.0不调整）')
    parser.add_argument('--music-dir', default='./bgm', help='背景音乐目录（默认: ./bgm）')
    parser.add_argument('--text', default='', help='自定义水印文字')
    parser.add_argument('--volume', type=float, default=0.15, help='背景音乐音量（0.0-1.0，默认0.15）')
    
    args = parser.parse_args()
    
    success = enhance_video(
        args.input,
        args.output,
        add_music=not args.no_music,
        add_text=not args.no_text,
        add_zoom=args.add_zoom,
        add_filter=args.add_filter,
        music_dir=args.music_dir,
        text=args.text,
        music_volume=args.volume,
        filter_name=args.filter_name,
        playback_speed=args.speed,
        zoom_factor=args.zoom_factor
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
