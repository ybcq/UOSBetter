#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steam.AppImage切割脚本
将Steam.AppImage文件切割成3份，便于上传到GitHub
"""

import os
import sys
import shutil

def split_appimage(input_file, output_prefix, num_parts=3):
    """
    将AppImage文件切割成指定数量的部分
    
    Args:
        input_file: 输入的AppImage文件路径
        output_prefix: 输出文件的前缀
        num_parts: 切割的份数
    """
    if not os.path.exists(input_file):
        print(f"错误: 输入文件不存在: {input_file}")
        return False
    
    # 获取文件大小
    file_size = os.path.getsize(input_file)
    part_size = file_size // num_parts
    
    print(f"文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")
    print(f"每份大小: {part_size} 字节 ({part_size / 1024 / 1024:.2f} MB)")
    
    # 删除已存在的分割文件
    for i in range(1, num_parts + 1):
        part_file = f"{output_prefix}_{i}"
        if os.path.exists(part_file):
            os.remove(part_file)
    
    # 执行切割
    with open(input_file, 'rb') as f_in:
        for part_num in range(1, num_parts + 1):
            part_file = f"{output_prefix}_{part_num}"
            bytes_to_read = part_size
            
            # 最后一份文件读取剩余的所有字节
            if part_num == num_parts:
                bytes_to_read = file_size - (part_num - 1) * part_size
            
            print(f"正在创建 {part_file}...")
            
            with open(part_file, 'wb') as f_out:
                # 读取指定大小的数据块
                bytes_read = 0
                chunk_size = 1024 * 1024  # 1MB的块大小
                
                while bytes_read < bytes_to_read:
                    chunk = f_in.read(min(chunk_size, bytes_to_read - bytes_read))
                    if not chunk:
                        break
                    f_out.write(chunk)
                    bytes_read += len(chunk)
    
    print(f"切割完成！已生成 {num_parts} 个文件:")
    for i in range(1, num_parts + 1):
        part_file = f"{output_prefix}_{i}"
        part_size = os.path.getsize(part_file)
        print(f"  {part_file}: {part_size} 字节 ({part_size / 1024 / 1024:.2f} MB)")
    
    return True

def merge_appimage(parts, output_file):
    """
    将分割的AppImage文件合并
    
    Args:
        parts: 分割文件列表
        output_file: 输出的合并文件
    """
    print(f"正在合并 {len(parts)} 个文件到 {output_file}...")
    
    # 删除已存在的输出文件
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # 按顺序合并文件
    with open(output_file, 'ab') as f_out:
        for part_file in parts:
            if not os.path.exists(part_file):
                print(f"警告: 文件不存在: {part_file}")
                continue
            
            print(f"正在合并 {part_file}...")
            with open(part_file, 'rb') as f_in:
                shutil.copyfileobj(f_in, f_out)
    
    # 验证合并后的文件大小
    original_size = sum(os.path.getsize(part) for part in parts if os.path.exists(part))
    merged_size = os.path.getsize(output_file)
    
    if original_size == merged_size:
        print(f"合并成功！输出文件: {output_file}")
        print(f"合并后大小: {merged_size} 字节 ({merged_size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print(f"合并失败！文件大小不匹配")
        print(f"预期大小: {original_size} 字节")
        print(f"实际大小: {merged_size} 字节")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  切割文件: python split_appimage.py split <input_file> <output_prefix> [num_parts]")
        print("  合并文件: python split_appimage.py merge <part1> <part2> <part3> <output_file>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "split":
        if len(sys.argv) < 4:
            print("切割用法: python split_appimage.py split <input_file> <output_prefix> [num_parts]")
            sys.exit(1)
        
        input_file = sys.argv[2]
        output_prefix = sys.argv[3]
        num_parts = int(sys.argv[4]) if len(sys.argv) > 4 else 3
        
        success = split_appimage(input_file, output_prefix, num_parts)
        if success:
            print("切割操作完成！")
        else:
            print("切割操作失败！")
    
    elif command == "merge":
        if len(sys.argv) < 5:
            print("合并用法: python split_appimage.py merge <part1> <part2> <part3> <output_file>")
            sys.exit(1)
        
        parts = sys.argv[2:-1]
        output_file = sys.argv[-1]
        
        success = merge_appimage(parts, output_file)
        if success:
            print("合并操作完成！")
        else:
            print("合并操作失败！")
    
    else:
        print(f"未知命令: {command}")
        sys.exit(1)