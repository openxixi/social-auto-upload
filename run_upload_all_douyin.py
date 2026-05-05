#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索所有 social-auto-upload 开头的文件夹并执行上传脚本
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    # 获取上级目录
    parent_dir = Path('..').resolve()
    
    print(f"搜索目录: {parent_dir}")
    print("=" * 60)
    
    # 搜索所有以 social-auto-upload 开头的文件夹
    folders = []
    for item in parent_dir.iterdir():
        if item.is_dir() and item.name.startswith('social-auto-upload'):
            folders.append(item)
    
    if not folders:
        print("未找到任何 social-auto-upload 开头的文件夹")
        return 1
    
    # 排序
    folders.sort(key=lambda x: x.name)
    
    print(f"找到 {len(folders)} 个文件夹:\n")
    for i, folder in enumerate(folders, 1):
        print(f"  {i}. {folder.name}")
    
    print("\n" + "=" * 60)
    
    # 遍历每个文件夹并执行脚本
    success_count = 0
    failed_count = 0
    
    for i, folder in enumerate(folders, 1):
        print(f"\n[{i}/{len(folders)}] 处理: {folder.name}")
        print("-" * 60)
        
        script_path = folder / 'upload_video_to_douyin.py'
        
        if not script_path.exists():
            print(f"✗ 跳过: 脚本不存在 ({script_path})")
            failed_count += 1
            continue
        
        try:
            # 切换到目标目录并执行脚本
            print(f"执行: cd {folder} && python upload_video_to_douyin.py")
            
            result = subprocess.run(
                ['python', 'upload_video_to_douyin.py'],
                cwd=str(folder),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ 成功")
                print(result.stdout)
                success_count += 1
            else:
                print(f"✗ 失败 (返回码: {result.returncode})")
                print(f"错误信息:\n{result.stderr}")
                failed_count += 1
                
        except Exception as e:
            print(f"✗ 异常: {e}")
            failed_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print(f"执行完成！")
    print(f"  总计: {len(folders)} 个文件夹")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print("=" * 60)
    
    return 0 if failed_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
