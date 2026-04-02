import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description):
    """
    执行命令并检查结果
    
    Args:
        command: 要执行的命令（字符串或列表）
        description: 命令描述
    
    Returns:
        bool: 命令是否成功执行
    """
    print(f"\n{'='*60}")
    print(f"⏳ {description}")
    print(f"{'='*60}")
    print(f"命令: {command if isinstance(command, str) else ' '.join(command)}")
    print()
    
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, check=True, encoding='utf-8')
        else:
            result = subprocess.run(command, check=True, encoding='utf-8')
        
        print(f"\n✓ {description} - 成功完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ {description} - 失败")
        print(f"错误代码: {e.returncode}")
        return False
    except Exception as e:
        print(f"\n✗ {description} - 异常")
        print(f"错误信息: {e}")
        return False

def main():
    """主流程：按顺序执行所有步骤"""
    start_time = datetime.now()
    print(f"\n{'#'*60}")
    print(f"# 抖音视频自动上传流程")
    print(f"# 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    steps = [
        {
            "command": 'python add_date_to_image.py ".\\videos_pre\\tmp.jpg" -o ".\\videos\\tmp.jpg"',
            "description": "步骤1: 为图片添加日期"
        },
        {
            "command": "python generate_date.py",
            "description": "步骤2: 生成日期文件"
        },
        {
            "command": 'python .\\workflow.py "D:\\video_workspace\\source_txt\\8_海尔能做我就能说.txt" "D:\\video_workspace\\source_audio\\zyxtest20251221.m4a" "D:\\video_workspace\\source_picture\\4_zyx_ttxd.jpg" .\\output_video\\ --prompt "男人正在说话"',
            "description": "步骤3: 生成数字人视频"
        },
        {
            "command": 'python .\\merge_videos.py "D:\\workspace\\movie\\cailiao\\demo\\demo.mp4" "D:\\workspace\\github\\openyixi\\social-auto-upload\\output_video\\data.mp4" -o .\\videos\\tmp.mp4',
            "description": "步骤4: 合并视频"
        },
        {
            "command": "python upload_video_to_douyin.py",
            "description": "步骤5: 上传视频到抖音"
        }
    ]
    
    # 执行所有步骤
    success_count = 0
    failed_steps = []
    
    for i, step in enumerate(steps, 1):
        success = run_command(step["command"], step["description"])
        
        if success:
            success_count += 1
        else:
            failed_steps.append(f"步骤{i}: {step['description']}")
            print(f"\n⚠️  步骤失败，自动继续执行后续步骤...")
            # 自动继续执行，不再需要用户确认
    
    # 总结
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'#'*60}")
    print(f"# 流程执行总结")
    print(f"{'#'*60}")
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration}")
    print(f"成功步骤: {success_count}/{len(steps)}")
    
    if failed_steps:
        print(f"\n失败步骤:")
        for step in failed_steps:
            print(f"  ✗ {step}")
    
    if success_count == len(steps):
        print(f"\n🎉 所有步骤执行成功！")
        print(f"{'#'*60}\n")
        return 0
    else:
        print(f"\n⚠️  部分步骤执行失败")
        print(f"{'#'*60}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())