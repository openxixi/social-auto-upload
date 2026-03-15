# -*- coding: utf-8 -*-
"""
视频处理工具函数
"""
import subprocess
import os
from pathlib import Path


def extract_video_frame(video_path: str, output_path: str = None, time: str = "00:00:01") -> str:
    """
    从视频中提取一帧作为图片
    
    Args:
        video_path: 视频文件路径
        output_path: 输出图片路径，如果为None则自动生成
        time: 提取帧的时间点，格式为 HH:MM:SS，默认提取第1秒的帧
        
    Returns:
        生成的图片文件路径
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    # 如果没有指定输出路径，自动生成
    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_cover.jpg"
    else:
        output_path = Path(output_path)
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 使用ffmpeg提取视频帧
    cmd = [
        'ffmpeg',
        '-ss', time,  # 指定时间点
        '-i', str(video_path),  # 输入文件
        '-vframes', '1',  # 只提取1帧
        '-q:v', '2',  # 设置图片质量（2是高质量）
        '-y',  # 覆盖已存在的文件
        str(output_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"  [+] 成功从视频提取封面: {output_path}")
        return str(output_path)
    except subprocess.CalledProcessError as e:
        print(f"  [-] 提取视频帧失败: {e.stderr}")
        raise
    except FileNotFoundError:
        print("  [-] 未找到ffmpeg，请确保已安装ffmpeg并添加到系统PATH")
        raise


def get_video_duration(video_path: str) -> float:
    """
    获取视频时长（秒）
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        视频时长（秒）
    """
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(video_path)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"  [-] 获取视频时长失败: {e}")
        return 0.0


if __name__ == "__main__":
    # 测试代码
    import sys
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        try:
            # 提取第1秒的帧
            cover = extract_video_frame(video_file, time="00:00:01")
            print(f"封面已保存到: {cover}")
            
            # 获取视频时长
            duration = get_video_duration(video_file)
            print(f"视频时长: {duration}秒")
        except Exception as e:
            print(f"错误: {e}")
    else:
        print("用法: python video_utils.py <视频文件路径>")
