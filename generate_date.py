#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成年月日文本工具
"""

from datetime import datetime

# 获取当前日期
now = datetime.now()

# 生成日期文本
date_text = f"{now.year}年{now.month}月{now.day}日"

# 写入txt文件
output_file = ".\output_video\date.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(date_text)

print(f"✓ 日期已生成并保存到: {output_file}")
print(f"内容: {date_text}")
