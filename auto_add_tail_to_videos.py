#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动添加日期尾部到视频
根据今天的日期，从日期字典目录中找到对应的年月日视频文件，拼接到主视频末尾
"""

import os
import sys
import platform
import argparse
import subprocess
import logging
from datetime import datetime
from pathlib import Path

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


def find_date_videos(date_dict_dir, year, month, day):
    """
    从日期字典目录中查找对应的年月日视频文件
    
    支持多种命名格式：
    年份: 2026.mp4, 2026nian.mp4, 2026年.mp4, 年_2026.mp4
    月份: 4.mp4, 4yue.mp4, 4月.mp4, 月_4.mp4
    日期: 27.mp4, 27ri.mp4, 27日.mp4, 日_27.mp4
    
    Args:
        date_dict_dir: 日期字典目录路径
        year: 年份（如 2026）
        month: 月份（如 4）
        day: 日期（如 27）
    
    Returns:
        包含年、月、日视频路径的字典，如果找不到则返回 None
    """
    date_dict_path = Path(date_dict_dir)
    
    if not date_dict_path.exists():
        logger.error(f"日期字典目录不存在: {date_dict_dir}")
        return None
    
    # 支持多种文件命名格式和扩展名
    video_extensions = ['.mp4', '.MP4', '.avi', '.mov', '.MOV']
    
    date_videos = {}
    
    # 查找年份视频 - 支持多种格式
    year_str = str(year)
    year_video = None
    year_patterns = [
        f"{year_str}",           # 2026.mp4
        f"{year_str}nian",       # 2026nian.mp4
        f"{year_str}年",         # 2026年.mp4
        f"年_{year_str}",        # 年_2026.mp4
    ]
    
    for ext in video_extensions:
        for pattern in year_patterns:
            candidate = date_dict_path / f"{pattern}{ext}"
            if candidate.exists():
                year_video = str(candidate)
                break
        if year_video:
            break
    
    if not year_video:
        logger.error(f"找不到年份视频文件: {year_str} (尝试了: {', '.join([p + '.mp4' for p in year_patterns])})")
        return None
    
    date_videos['year'] = year_video
    logger.info(f"✓ 找到年份视频: {os.path.basename(year_video)}")
    
    # 查找月份视频 - 支持多种格式
    month_str = str(month)
    month_video = None
    month_patterns = [
        f"{month_str}",          # 4.mp4
        f"{month_str}yue",       # 4yue.mp4
        f"{month_str}月",        # 4月.mp4
        f"月_{month_str}",       # 月_4.mp4
    ]
    
    for ext in video_extensions:
        for pattern in month_patterns:
            candidate = date_dict_path / f"{pattern}{ext}"
            if candidate.exists():
                month_video = str(candidate)
                break
        if month_video:
            break
    
    if not month_video:
        logger.error(f"找不到月份视频文件: {month_str} (尝试了: {', '.join([p + '.mp4' for p in month_patterns])})")
        return None
    
    date_videos['month'] = month_video
    logger.info(f"✓ 找到月份视频: {os.path.basename(month_video)}")
    
    # 查找日期视频 - 支持多种格式
    day_str = str(day)
    day_video = None
    day_patterns = [
        f"{day_str}",            # 27.mp4
        f"{day_str}ri",          # 27ri.mp4
        f"{day_str}日",          # 27日.mp4
        f"日_{day_str}",         # 日_27.mp4
    ]
    
    for ext in video_extensions:
        for pattern in day_patterns:
            candidate = date_dict_path / f"{pattern}{ext}"
            if candidate.exists():
                day_video = str(candidate)
                break
        if day_video:
            break
    
    if not day_video:
        logger.error(f"找不到日期视频文件: {day_str} (尝试了: {', '.join([p + '.mp4' for p in day_patterns])})")
        return None
    
    date_videos['day'] = day_video
    logger.info(f"✓ 找到日期视频: {os.path.basename(day_video)}")
    
    return date_videos


def concat_videos_with_date(input_video, output_video, date_dict_dir, target_date=None, cover=None, resolution="auto", fit_mode="pad"):
    """
    将输入视频与日期视频拼接（使用 merge_videos.py）
    
    Args:
        input_video: 输入视频路径
        output_video: 输出视频路径
        date_dict_dir: 日期字典目录
        target_date: 目标日期（datetime对象），默认为今天
        cover: 封面图片路径（可选）
    
    Returns:
        成功返回True，失败返回False
    """
    if not check_ffmpeg():
        return False
    
    # 检查输入视频
    if not os.path.exists(input_video):
        logger.error(f"输入视频不存在: {input_video}")
        return False
    
    # 获取日期
    if target_date is None:
        target_date = datetime.now()
    
    year = target_date.year
    month = target_date.month
    day = target_date.day
    
    logger.info(f"目标日期: {year}年{month}月{day}日")
    
    # 查找日期视频
    date_videos = find_date_videos(date_dict_dir, year, month, day)
    if not date_videos:
        logger.error("无法找到所有需要的日期视频文件")
        return False
    
    try:
        # 构建命令：使用 merge_videos.py 合并视频
        # 顺序：主视频 -> 年 -> 月 -> 日
        cmd = [
            'python',
            'merge_videos.py',
            input_video,
            date_videos['year'],
            date_videos['month'],
            date_videos['day'],
            '-o', output_video
        ]
        
        # 如果有封面，添加封面参数
        if cover and os.path.exists(cover):
            cmd.extend(['--cover', cover])
            logger.info(f"使用封面: {cover}")
        
        logger.info("视频拼接顺序:")
        logger.info(f"  1. {os.path.basename(input_video)} (主视频)")
        logger.info(f"  2. {os.path.basename(date_videos['year'])} (年)")
        logger.info(f"  3. {os.path.basename(date_videos['month'])} (月)")
        logger.info(f"  4. {os.path.basename(date_videos['day'])} (日)")
        
        logger.info("开始拼接视频...")
        logger.info(f"命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✓ 视频拼接成功: {output_video}")
            
            # 检查输出文件
            if os.path.exists(output_video):
                file_size = os.path.getsize(output_video) / (1024 * 1024)
                logger.info(f"  输出文件大小: {file_size:.2f} MB")
                return True
            else:
                logger.error("输出文件不存在")
                return False
        else:
            logger.error("视频拼接失败")
            logger.error(f"错误信息: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"视频拼接失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    # 根据操作系统设置默认日期字典路径
    if platform.system() == 'Linux':
        default_date_dict = '/home/nuc/date_dictionary'
    else:  # Windows
        default_date_dict = r'D:\video_workspace\jianying_output\date_dictionary'
    
    parser = argparse.ArgumentParser(
        description='自动添加日期尾部到视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认日期字典目录和今天的日期
  python auto_add_tail_to_videos.py input.mp4 -o output.mp4
  
  # 指定日期字典目录
  python auto_add_tail_to_videos.py input.mp4 -o output.mp4 -d D:\\video_workspace\\jianying_output\\date_dictionary
  
  # 指定日期
  python auto_add_tail_to_videos.py input.mp4 -o output.mp4 --date 2026-04-27
  
  # 添加封面
  python auto_add_tail_to_videos.py input.mp4 -o output.mp4 --cover cover.jpg
        """
    )
    
    parser.add_argument(
        'input_video',
        help='输入视频文件路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='output_with_date.mp4',
        help='输出视频文件路径（默认: output_with_date.mp4）'
    )
    
    parser.add_argument(
        '-d', '--date-dict',
        default=default_date_dict,
        help=f'日期字典目录路径（默认: {default_date_dict}）'
    )
    
    parser.add_argument(
        '--date',
        help='指定日期（格式: YYYY-MM-DD），默认为今天'
    )
    
    parser.add_argument(
        '-c', '--cover',
        help='封面图片文件路径（可选）'
    )
    
    args = parser.parse_args()
    
    # 解析日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
            logger.info(f"使用指定日期: {args.date}")
        except ValueError:
            logger.error(f"日期格式错误: {args.date}，应为 YYYY-MM-DD")
            return 1
    else:
        target_date = datetime.now()
        logger.info(f"使用今天日期: {target_date.strftime('%Y-%m-%d')}")
    
    # 拼接视频
    success = concat_videos_with_date(
        args.input_video,
        args.output,
        args.date_dict,
        target_date,
        args.cover
    )
    
    if success:
        logger.info("=" * 60)
        logger.info("✓ 所有操作完成！")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("✗ 操作失败")
        logger.error("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
