from pathlib import Path
import platform
import os

BASE_DIR = Path(__file__).parent.resolve()
XHS_SERVER = "http://127.0.0.1:11901"

# 使用本地 Chrome 浏览器（Chromium 不支持 H.264 编解码器，会导致腾讯视频上传失败）
# 根据操作系统自动选择 Chrome 路径
def get_chrome_path():
    """根据操作系统返回 Chrome 路径"""
    system = platform.system()
    
    if system == "Windows":
        # Windows 常见路径
        possible_paths = [
            "C:/Program Files/Google/Chrome/Application/chrome.exe",
            "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
            os.path.expandvars(r"${LOCALAPPDATA}/Google/Chrome/Application/chrome.exe"),
        ]
    elif system == "Linux":
        # Linux/Ubuntu 常见路径
        possible_paths = [
            "/usr/bin/google-chrome",
        ]
    elif system == "Darwin":  # macOS
        # macOS 路径
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:
        return None
    
    # 查找第一个存在的路径
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

LOCAL_CHROME_PATH = get_chrome_path()
LOCAL_CHROME_HEADLESS = False
