import os
import sys
from PIL import Image, ImageDraw, ImageFont
import argparse

# 设置标准输出编码为 UTF-8，解决 Windows 控制台编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def add_text_to_image(image_path, text, output_path=None, 
                     position='top-left', 
                     font_size_ratio=0.052,
                     text_color='white',
                     shadow_color='black',
                     shadow_offset=4,
                     margin_x=0.025,
                     margin_y=0.025):
    """
    在图片上添加文字
    
    Args:
        image_path: 输入图片路径
        text: 要添加的文字内容
        output_path: 输出图片路径（如果为None，则在原文件名后添加'_带文字'）
        position: 文字位置，可选值：
                  'top-left' (默认，左上角)
                  'bottom-right' (右下角)
                  'bottom-left' (左下角)
                  'top-right' (右上角)
                  'center' (居中)
                  或者自定义坐标元组 (x_ratio, y_ratio)，如 (0.5, 0.5) 表示中心
        font_size_ratio: 字体大小占图片高度的比例（默认0.052即5.2%）
        text_color: 文字颜色（默认白色）
        shadow_color: 阴影颜色（默认黑色）
        shadow_offset: 阴影偏移量（默认4像素）
        margin_x: 水平边距占图片宽度的比例（默认0.025即2.5%）
        margin_y: 垂直边距占图片高度的比例（默认0.025即2.5%）
    """
    print(f"正在处理图片: {image_path}")
    print(f"添加文字: {text}")
    
    # 打开图片
    image = Image.open(image_path)
    width, height = image.size
    print(f"图片尺寸: {width} x {height}")
    
    # 创建绘图对象
    draw = ImageDraw.Draw(image)
    
    # 设置字体和大小
    font_size = int(height * font_size_ratio)
    
    try:
        # 根据操作系统选择字体路径
        import platform
        
        if platform.system() == 'Windows':
            font_paths = [
                "C:/Windows/Fonts/simhei.ttf",  # 黑体（优先，粗体效果）
                "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑粗体
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
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
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 计算文字位置
    margin_x_px = int(width * margin_x)
    margin_y_px = int(height * margin_y)
    
    if isinstance(position, tuple):
        # 自定义位置（比例）
        x = int(width * position[0] - text_width / 2)
        y = int(height * position[1] - text_height / 2)
    elif position == 'bottom-right':
        x = width - text_width - margin_x_px
        y = height - text_height - margin_y_px
    elif position == 'bottom-left':
        x = margin_x_px
        y = height - text_height - margin_y_px
    elif position == 'top-right':
        x = width - text_width - margin_x_px
        y = margin_y_px
    elif position == 'top-left':
        x = margin_x_px
        y = margin_y_px
    elif position == 'center':
        x = (width - text_width) // 2
        y = (height - text_height) // 2
    else:
        print(f"警告: 未知位置 '{position}'，使用默认位置 bottom-right")
        x = width - text_width - margin_x_px
        y = height - text_height - margin_y_px
    
    # 绘制阴影（四个方向）
    for offset_x, offset_y in [(-shadow_offset, -shadow_offset), 
                                (shadow_offset, -shadow_offset),
                                (-shadow_offset, shadow_offset), 
                                (shadow_offset, shadow_offset)]:
        draw.text((x + offset_x, y + offset_y), text, font=font, fill=shadow_color)
    
    # 绘制主文字
    draw.text((x, y), text, font=font, fill=text_color)
    
    print(f"文字位置: ({x}, {y})")
    print(f"文字大小: {text_width} x {text_height}")
    print(f"字体颜色: {text_color}")
    
    # 保存图片
    if output_path is None:
        # 如果没有指定输出路径，创建一个带文字后缀的新文件
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_带文字{ext}"
    
    image.save(output_path)
    print(f"✓ 图片已保存: {output_path}")
    
    return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="在图片上添加文字",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
位置参数说明:
  bottom-right  : 右下角（默认）
  bottom-left   : 左下角
  top-right     : 右上角
  top-left      : 左上角
  center        : 居中
  x,y           : 自定义位置，如 0.5,0.5 表示中心（取值0-1）

使用示例:
  %(prog)s input.jpg "你好世界"
  %(prog)s input.jpg "测试文字" -p top-left
  %(prog)s input.jpg "居中文字" -p center -c "#FFD700"
  %(prog)s input.jpg "自定义位置" -p 0.5,0.8 -s 0.05
        """
    )
    
    parser.add_argument("image", help="输入图片路径")
    parser.add_argument("text", help="要添加的文字内容")
    parser.add_argument("-o", "--output", help="输出图片路径（可选，默认在原文件名后添加'_带文字'）")
    parser.add_argument("-p", "--position", default="top-left", 
                        help="文字位置（默认：top-left），可选：top-left, top-right, bottom-left, bottom-right, center 或自定义 x,y")
    parser.add_argument("-s", "--font-size", type=float, default=0.06,
                        help="字体大小比例（默认：0.06 即图片高度的6%）")
    parser.add_argument("-c", "--color", default="white",
                        help="文字颜色（默认：white），支持颜色名称或十六进制如 #FFD700")
    parser.add_argument("--shadow-color", default="black",
                        help="阴影颜色（默认：black）")
    parser.add_argument("--shadow-offset", type=int, default=4,
                        help="阴影偏移量（默认：4）")
    parser.add_argument("--margin-x", type=float, default=0.155,
                        help="水平边距比例（默认：0.025 即2.5%）")
    parser.add_argument("--margin-y", type=float, default=0.085,
                        help="垂直边距比例（默认：0.025 即2.5%）")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"错误: 图片文件不存在: {args.image}")
        sys.exit(1)
    
    # 解析位置参数
    position = args.position
    if ',' in position:
        try:
            x, y = map(float, position.split(','))
            position = (x, y)
        except ValueError:
            print(f"错误: 无效的位置格式: {args.position}")
            sys.exit(1)
    
    add_text_to_image(
        args.image, 
        args.text,
        args.output,
        position=position,
        font_size_ratio=args.font_size,
        text_color=args.color,
        shadow_color=args.shadow_color,
        shadow_offset=args.shadow_offset,
        margin_x=args.margin_x,
        margin_y=args.margin_y
    )
