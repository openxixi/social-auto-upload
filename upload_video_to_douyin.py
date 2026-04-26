import asyncio
import platform
from pathlib import Path

from conf import BASE_DIR
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags


if __name__ == '__main__':
    # 根据操作系统设置视频文件路径
    system = platform.system().lower()
    if system == 'linux':
        # Ubuntu/Linux 系统使用共享目录
        filepath = Path("/mnt/win_share/github/openyixi/social-auto-upload/videos")
    else:
        # Windows 系统使用相对路径
        filepath = Path(BASE_DIR) / "videos"
    
    account_file = Path(BASE_DIR / "cookies" / "douyin_uploader" / "account.json")
    # 获取视频目录
    folder_path = Path(filepath)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    
    print(f"\n在 {folder_path} 找到 {file_num} 个视频文件")
    if file_num == 0:
        print("❌ 没有找到视频文件，请将 .mp4 文件放入 videos 文件夹后再运行")
        exit(0)
    
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[19], timestamps=False, start_days=-1)
    cookie_setup = asyncio.run(douyin_setup(account_file, handle=False))
    
    print(f"\n开始处理 {file_num} 个视频...\n")
    for index, file in enumerate(files):
        title, tags = get_title_and_hashtags(str(file))
        # 查找封面文件（优先png，其次jpg）
        thumbnail_path = file.with_suffix('.png')
        if not thumbnail_path.exists():
            thumbnail_path = file.with_suffix('.jpg')
        
        # 打印视频文件名、标题和 hashtag
        print(f"视频文件名：{file}")
        print(f"标题：{title}")
        print(f"Hashtag：{tags}")
        
        # 如果有封面文件，则使用
        if thumbnail_path.exists():
            print(f"封面文件：{thumbnail_path}")
            app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file, thumbnail_path=thumbnail_path)
        else:
            print("未找到封面文件，将自动从视频提取")
            app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file)
        asyncio.run(app.main(), debug=False)
