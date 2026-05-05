#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重复执行目录复制命令
"""

import sys
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description='重复执行 cp 命令 N 次')
    parser.add_argument('N', type=int, help='执行次数')
    
    args = parser.parse_args()
    
    if args.N <= 0:
        print("错误: N 必须大于 0")
        return 1
    
    print(f"将执行 cp 命令 {args.N} 次...")
    
    for i in range(args.N):
        print(f"\n[{i+1}/{args.N}] 执行: cp -r ../social-auto-upload ../social-auto-upload_{i+1}")
        
        try:
            result = subprocess.run(
                ['cp', '-r', '../social-auto-upload', f'../social-auto-upload_{i+1}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✓ 成功")
            else:
                print(f"✗ 失败: {result.stderr}")
                
        except Exception as e:
            print(f"✗ 错误: {e}")
    
    print(f"\n完成！共执行 {args.N} 次")
    return 0


if __name__ == '__main__':
    sys.exit(main())
