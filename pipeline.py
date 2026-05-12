#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline 自动处理流程
从数字文件夹中依次获取素材文件
"""

import os
import sys
import platform
import shutil
import re
import subprocess
from pathlib import Path
import logging
import random

# 设置标准输出编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
import time
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
INDEX_FILE = "pipeline_index.txt"  # 保存当前索引的文件
VIDEOS_PRE_DIR = "./videos_pre"


def get_source_dir():
    """根据操作系统获取源目录"""
    if platform.system() == 'Windows':
        return r'D:\video_workspace\jianying_output'
    else:  # Linux
        return '/mnt/d/video_workspace/jianying_output'


def load_current_index(max_index=None):
    """加载当前索引
    
    Args:
        max_index: 最大索引值，用于初始化
    """
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, 'r') as f:
                index = int(f.read().strip())
                logger.info(f"加载索引: {index}")
                return index
        except:
            if max_index is not None:
                logger.warning(f"索引文件损坏，重置为最大值 {max_index}")
                return max_index
            else:
                logger.warning("索引文件损坏，重置为 0")
                return 0
    else:
        if max_index is not None:
            logger.info(f"索引文件不存在，初始化为最大值 {max_index}")
            return max_index
        else:
            logger.info("索引文件不存在，初始化为 0")
            return 0


def save_current_index(index):
    """保存当前索引"""
    with open(INDEX_FILE, 'w') as f:
        f.write(str(index))
    logger.info(f"保存索引: {index}")


def get_numbered_folders(source_dir):
    """
    获取所有数字开头的文件夹并排序
    
    Returns:
        排序后的文件夹列表
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        logger.error(f"源目录不存在: {source_dir}")
        return []
    
    # 查找所有数字开头的文件夹
    folders = []
    for item in source_path.iterdir():
        if item.is_dir():
            # 检查文件夹名是否以数字开头
            match = re.match(r'^(\d+)', item.name)
            if match:
                folder_num = int(match.group(1))
                folders.append((folder_num, item.name, str(item)))
    
    # 按数字排序
    folders.sort(key=lambda x: x[0])
    
    logger.info(f"找到 {len(folders)} 个数字开头的文件夹")
    for num, name, _ in folders[:5]:  # 只显示前5个
        logger.info(f"  - {name}")
    if len(folders) > 5:
        logger.info(f"  ... 还有 {len(folders) - 5} 个")
    
    return folders


def clear_videos_pre():
    """清空 videos_pre 目录中的 tmp.jpg 和 tmp.mp4"""
    logger.info("=" * 60)
    logger.info("步骤1: 清理旧文件")
    logger.info("=" * 60)
    
    videos_pre_path = Path(VIDEOS_PRE_DIR)
    
    # 确保目录存在
    videos_pre_path.mkdir(parents=True, exist_ok=True)
    
    # 删除旧文件
    for filename in ['tmp.jpg', 'tmp.mp4']:
        file_path = videos_pre_path / filename
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✓ 删除: {filename}")
        else:
            logger.info(f"  跳过: {filename} (不存在)")


def move_files_from_folder(folder_path):
    """
    从指定文件夹中移动 .jpg 和 .mp4 文件到 videos_pre
    
    Args:
        folder_path: 文件夹路径
    
    Returns:
        成功返回 True，失败返回 False
    """
    logger.info("=" * 60)
    logger.info("步骤2: 复制新文件")
    logger.info("=" * 60)
    
    folder = Path(folder_path)
    videos_pre_path = Path(VIDEOS_PRE_DIR)
    
    # 查找 .jpg 和 .mp4 文件
    jpg_files = list(folder.glob('*.jpg')) + list(folder.glob('*.JPG'))
    mp4_files = list(folder.glob('*.mp4')) + list(folder.glob('*.MP4'))
    
    if not jpg_files:
        logger.error(f"✗ 未找到 .jpg 文件: {folder}")
        return False
    
    if not mp4_files:
        logger.error(f"✗ 未找到 .mp4 文件: {folder}")
        return False
    
    # 使用第一个找到的文件
    jpg_source = jpg_files[0]
    mp4_source = mp4_files[0]
    
    jpg_dest = videos_pre_path / 'tmp.jpg'
    mp4_dest = videos_pre_path / 'tmp.mp4'
    
    try:
        # 复制文件（使用复制而不是移动，保留源文件）
        shutil.copy2(jpg_source, jpg_dest)
        logger.info(f"✓ 复制图片: {jpg_source.name} -> tmp.jpg")
        
        shutil.copy2(mp4_source, mp4_dest)
        logger.info(f"✓ 复制视频: {mp4_source.name} -> tmp.mp4")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 复制失败: {e}")
        return False


def process_videos(folder_num=None, is_first_run=False):
    """
    步骤3: 处理视频和图片
    - 为图片添加日期
    - 为视频添加日期尾部
    
    Args:
        folder_num: 文件夹编号（从文件夹名中提取的数字）
        is_first_run: 是否是第一次运行（影响视频增强参数）
    
    Returns:
        成功返回 True，失败返回 False
    """
    logger.info("=" * 60)
    logger.info(f"步骤3: 处理视频和图片 (文件夹编号: {folder_num})")
    logger.info("=" * 60)
    
    # 确保 videos 目录存在
    videos_dir = Path("./videos")
    videos_dir.mkdir(parents=True, exist_ok=True)
    
    # 3.1 为图片添加日期
    logger.info("3.1 为图片添加日期...")
    try:
        result = subprocess.run(
            ['python', 'add_date_to_image.py', './videos_pre/tmp.jpg', '-o', './videos/tmp.jpg'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        logger.info("✓ 图片处理完成")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ 图片处理失败: {e}")
        logger.error(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ 图片处理异常: {e}")
        return False
    try:
        # text 是位置参数，需要放在 image 之后，-o 之前
        result = subprocess.run(
            ['python', 'add_txt_to_image.py', './videos/tmp.jpg', 
             f"第{folder_num}集" if folder_num is not None else "第0集",
             '-o', './videos/tmp.jpg'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        logger.info("✓ 图片添加集数完成")
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ 图片添加集数失败: {e}")
        logger.error(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ 图片添加集数异常: {e}")
        return False

    # 3.2 为视频添加日期尾部
    logger.info("3.2 为视频添加日期尾部...")
    try:
        result = subprocess.run(
            ['python', './auto_add_tail_to_videos.py', './videos_pre/tmp.mp4', 
             '-c', './videos/tmp.jpg', '-o', './videos_pre/tmp_raw.mp4',  # 先输出为 tmp_raw.mp4 20260513
             ],  # 抖音竖屏全屏
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        logger.info("✓ 视频处理完成（抖音竖屏全屏）")
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-5:]:  # 只显示最后5行
                logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ 视频处理失败: {e}")
        logger.error(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ 视频处理异常: {e}")
        return False
    
    # 3.3 增强视频（添加背景音乐、文字水印、滤镜、速度、缩放等，提高原创性）
    logger.info("3.3 增强视频（提高原创性）...")
    
    # 第一次运行时使用默认参数，之后使用随机参数
    if is_first_run:
        # 第一次：不使用增强参数，只添加音乐和水印
        logger.info("  第一次运行，使用默认参数（仅音乐+水印）")
        cmd = [
            'python', 'enhance_video.py', './videos_pre/tmp_raw.mp4', 
            '-o', './videos/tmp.mp4',
            '--music-dir', './bgm',
            '--volume', '0.12'  # 背景音乐音量 12%
        ]
    else:
        # 之后运行：使用随机参数
        filter_types = ['vintage', 'vibrant', 'cool', 'warm', 'sharp', 'soft', 'bright', 'contrast', 'cinematic']
        random_filter = random.choice(filter_types)
        random_speed = round(random.uniform(0.95, 1.05), 3)  # 0.95-1.05 之间
        random_zoom = round(random.uniform(0.0005, 0.002), 4)  # 0.0005-0.002 之间
        
        logger.info(f"  随机参数: filter={random_filter}, speed={random_speed}, zoom={random_zoom}")
        
        cmd = [
            'python', 'enhance_video.py', './videos/tmp_raw.mp4', 
            '-o', './videos/tmp.mp4',
            '--add-filter', '--filter', random_filter,
            '--speed', str(random_speed),
            '--add-zoom', '--zoom-factor', str(random_zoom),
            '--music-dir', './bgm',
            '--volume', '0.12'  # 背景音乐音量 12%
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        logger.info("✓ 视频增强完成")
        if result.stdout:
            for line in result.stdout.strip().split('\n')[-5:]:
                logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"⚠ 视频增强失败，使用原视频: {e}")
        # 如果增强失败，使用未增强的视频
        import shutil
        shutil.copy2('./videos/tmp_raw.mp4', './videos/tmp.mp4')
    except Exception as e:
        logger.warning(f"⚠ 视频增强异常，使用原视频: {e}")
        import shutil
        shutil.copy2('./videos/tmp_raw.mp4', './videos/tmp.mp4')
    
    return True


def upload_to_douyin():
    """
    步骤4: 上传视频到抖音
    
    Returns:
        成功返回 True，失败返回 False
    """
    logger.info("=" * 60)
    logger.info("步骤4: 上传视频到抖音")
    logger.info("=" * 60)
    
    try:
        result = subprocess.run(
            ['python', 'upload_video_to_douyin.py'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=True
        )
        logger.info("✓ 视频上传完成")
        if result.stdout:
            # 显示输出的最后10行
            for line in result.stdout.strip().split('\n')[-10:]:
                logger.info(f"  {line}")
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ 视频上传失败: {e}")
        logger.error(f"错误信息: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"✗ 视频上传异常: {e}")
        return False
    
    return True


def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline 自动处理流程")
    logger.info("=" * 60)
    
    # 获取源目录
    source_dir = get_source_dir()
    logger.info(f"源目录: {source_dir}")
    
    # 获取所有数字文件夹
    folders = get_numbered_folders(source_dir)
    
    if not folders:
        logger.error("没有找到任何数字开头的文件夹")
        return 1
    
    # 最大索引值
    max_index = len(folders) - 1
    
    # 加载当前索引（如果不存在则初始化为最大值）
    current_index = load_current_index(max_index)
    
    # 如果索引超出范围或为负数，重置为最大索引
    if current_index >= len(folders) or current_index < 0:
        logger.info(f"索引 {current_index} 超出范围，重置为最大索引 {max_index} ({folders[max_index][1]})")
        current_index = max_index
    
    # 获取当前要处理的文件夹
    folder_num, folder_name, folder_path = folders[current_index]
    
    logger.info("=" * 60)
    logger.info(f"当前处理: [{current_index + 1}/{len(folders)}] {folder_name}")
    logger.info("=" * 60)
    
    # 步骤1: 清理旧文件
    clear_videos_pre()
    
    # 步骤2: 复制新文件
    success = move_files_from_folder(folder_path)
    
    if not success:
        logger.error("=" * 60)
        logger.error(f"✗ 步骤2失败，终止处理")
        logger.error("=" * 60)
        return 1
    
    # 步骤3: 处理视频和图片
    # 判断是否是第一次运行：current_index == max_index 说明是首次运行
    is_first_run = (current_index == max_index)
    success = process_videos(folder_num, is_first_run)
    
    if not success:
        logger.error("=" * 60)
        logger.error(f"✗ 步骤3失败，终止处理")
        logger.error("=" * 60)
        return 1
    
    # 步骤4: 上传视频到抖音
    success = upload_to_douyin()
    
    if success:
        # 更新索引（倒序：从大到小，到0后回到最大）
        next_index = current_index - 1
        if next_index < 0:
            # 已经到最小值，回到最大值
            next_index = len(folders) - 1
            logger.info(f"已处理到最小索引，下次从最大索引 {next_index} 重新开始")
        
        save_current_index(next_index)
        
        logger.info("=" * 60)
        logger.info(f"✓ 全部处理成功！")
        logger.info(f"下次将处理: [{next_index + 1}/{len(folders)}] {folders[next_index][1]}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error(f"✗ 步骤4失败")
        logger.error("=" * 60)
        return 1


def wait_until_next_run(target_hour=5):
    """
    计算并等待到下一个执行时间
    
    Args:
        target_hour: 目标执行小时（0-23），默认5表示凌晨5点
    
    Returns:
        下一次执行的datetime对象
    """
    now = datetime.now()
    
    # 计算今天的目标时间
    today_target = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
    
    # 如果今天的目标时间已经过了，计算明天的目标时间
    if now >= today_target:
        next_run = today_target + timedelta(days=1)
    else:
        next_run = today_target
    
    # 计算需要等待的秒数
    wait_seconds = (next_run - now).total_seconds()
    
    logger.info("=" * 60)
    logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"下次执行: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"等待时间: {wait_seconds/3600:.1f} 小时")
    logger.info("=" * 60)
    
    return next_run, wait_seconds


def run_scheduler(target_hour=5, reset_index=True):
    """
    定时调度器，每天在指定时间执行一次
    
    Args:
        target_hour: 目标执行小时（0-23），默认5表示凌晨5点
        reset_index: 是否在启动时重置索引为最大值（默认True）
    """
    logger.info("\n" + "=" * 60)
    logger.info("Pipeline 定时调度器已启动")
    logger.info(f"执行时间: 每天 {target_hour:02d}:00")
    logger.info("=" * 60)
    
    # 如果需要重置索引，先强制设置为最大值
    if reset_index:
        # 获取源目录和文件夹列表
        source_dir = get_source_dir()
        folders = get_numbered_folders(source_dir)
        if folders:
            max_index = len(folders) - 1
            save_current_index(max_index)
            logger.info(f"✓ 索引已重置为最大值: {max_index} ({folders[max_index][1]})")
    
    # 首次运行
    logger.info("\n首次立即执行...")
    try:
        result = main()
        if result == 0:
            logger.info("✓ 首次执行成功")
        else:
            logger.error("✗ 首次执行失败")
    except Exception as e:
        logger.error(f"✗ 首次执行异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 进入定时循环
    while True:
        try:
            # 计算下次执行时间并等待
            next_run, wait_seconds = wait_until_next_run(target_hour)
            
            # 休眠到下次执行时间
            # 使用分段休眠，每小时唤醒一次，便于监控和中断
            while True:
                now = datetime.now()
                remaining = (next_run - now).total_seconds()
                
                if remaining <= 0:
                    break
                
                # 每次最多休眠1小时
                sleep_time = min(remaining, 3600)
                logger.info(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 休眠中... 剩余 {remaining/3600:.1f} 小时")
                time.sleep(sleep_time)
            
            # 执行任务
            logger.info("\n" + "=" * 60)
            logger.info(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始执行定时任务")
            logger.info("=" * 60)
            
            result = main()
            
            if result == 0:
                logger.info("\n" + "=" * 60)
                logger.info(f"✓ 定时任务执行成功")
                logger.info("=" * 60)
            else:
                logger.error("\n" + "=" * 60)
                logger.error(f"✗ 定时任务执行失败")
                logger.error("=" * 60)
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 60)
            logger.info("收到中断信号，停止调度器")
            logger.info("=" * 60)
            break
        except Exception as e:
            logger.error(f"\n调度器异常: {e}")
            import traceback
            traceback.print_exc()
            logger.info("5分钟后重试...")
            time.sleep(300)  # 异常后等待5分钟


if __name__ == '__main__':
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # 单次运行模式
        logger.info("单次运行模式")
        sys.exit(main())
    elif len(sys.argv) > 1 and sys.argv[1] == '--continue':
        # 定时调度模式（继续之前的进度）
        logger.info("定时调度模式（继续之前的进度）")
        try:
            run_scheduler(target_hour=5, reset_index=False)
        except KeyboardInterrupt:
            logger.info("\n程序已停止")
            sys.exit(0)
    else:
        # 定时调度模式（默认：重置索引）
        logger.info("定时调度模式（从最大索引开始）")
        try:
            run_scheduler(target_hour=5, reset_index=True)  # 每天凌晨5点执行
        except KeyboardInterrupt:
            logger.info("\n程序已停止")
            sys.exit(0)
