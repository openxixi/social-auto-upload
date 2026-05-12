import os
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import argparse

# 设置标准输出编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def add_date_to_image(image_path, output_path=None, date_format="%Y年%m月%d日"):
    """
    在图片上添加当天日期
    
    Args:
        image_path: 输入图片路径
        output_path: 输出图片路径（如果为None，则覆盖原图）
        date_format: 日期格式，默认为 "年月日" 格式
    """
    # 获取当天日期
    today = datetime.now()
    date_text = "余喜 " + today.strftime(date_format)
    
    print(f"正在处理图片: {image_path}")
    print(f"添加日期: {date_text}")
    
    # 打开图片
    image = Image.open(image_path)
    width, height = image.size
    print(f"图片尺寸: {width} x {height}")
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # 设置字体和大小
    font_size = int(height * 0.035)  # 字体大小为图片高度的3.5%（适配底部小字）
    
    try:
        # 根据操作系统选择字体路径
        import platform
        
        if platform.system() == 'Windows':
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",  # 宋体
            ]
        else:  # Linux/Mac
            font_paths = [
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  # 文泉驿正黑
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # 文泉驿微米黑
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Droid
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",  # 思源黑体
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Liberation
                "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
            ]
        
        font = None
        for font_path in font_paths:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                print(f"使用字体: {font_path}")
                break
        
        if font is None:
            print("警告: 未找到中文字体，使用默认字体")
            print("Linux 用户请安装字体: sudo apt-get install fonts-wqy-zenhei fonts-wqy-microhei")
            font = ImageFont.load_default()
    except Exception as e:
        print(f"加载字体失败: {e}，使用默认字体")
        font = ImageFont.load_default()
    
    # 获取文字边界框
    bbox = draw.textbbox((0, 0), date_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 计算文字位置（右下角，红框位置）
    margin_right = int(width * 0.08)  # 距离右边8%
    margin_bottom = int(height * 0.20)  # 距离底部20%
    x = width - text_width - margin_right
    y = height - text_height - margin_bottom
    
    # 添加文字阴影/描边效果，增强可读性
    shadow_color = "black"
    text_color = "white"  # 白色字体
    shadow_offset = 3
    
    # 绘制阴影（四个方向）
    for offset_x, offset_y in [(-shadow_offset, -shadow_offset), 
                                (shadow_offset, -shadow_offset),
                                (-shadow_offset, shadow_offset), 
                                (shadow_offset, shadow_offset)]:
        draw.text((x + offset_x, y + offset_y), date_text, font=font, fill=shadow_color)
    
    # 绘制主文字
    draw.text((x, y), date_text, font=font, fill=text_color)
    
    print(f"文字位置: ({x}, {y})")
    print(f"文字大小: {text_width} x {text_height}")
    
    # 保存图片
    if output_path is None:
        # 如果没有指定输出路径，创建一个带日期后缀的新文件
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_带日期{ext}"
    
    image.save(output_path)
    print(f"✓ 图片已保存: {output_path}")
    
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="在图片上添加当天日期")
    parser.add_argument("image", help="输入图片路径")
    parser.add_argument("-o", "--output", help="输出图片路径（可选，默认在原文件名后添加'_带日期'）")
    parser.add_argument("-f", "--format", default="%Y年%m月%d日", 
                        help="日期格式（默认：年月日）")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"错误: 图片文件不存在: {args.image}")
        sys.exit(1)
    
    add_date_to_image(args.image, args.output, args.format)
