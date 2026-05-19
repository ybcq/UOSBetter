#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub下载模块
从GitHub releases下载文件，带进度显示
"""

import os
import requests
from urllib.parse import urlparse
from pathlib import Path

def download_file_with_progress(url, output_path, chunk_size=8192, progress_callback=None):
    """
    下载文件并显示进度
    
    Args:
        url: 下载URL
        output_path: 输出文件路径
        chunk_size: 下载块大小（字节）
        progress_callback: 进度回调函数，参数为(下载字节数, 总字节数, 进度百分比)
        
    Returns:
        bool: 下载是否成功
    """
    try:
        # 获取文件大小
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # 删除已存在的文件
        if os.path.exists(output_path):
            os.remove(output_path)
        
        # 下载文件
        downloaded = 0
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_percent = (downloaded / total_size * 100) if total_size > 0 else 0
                        progress_callback(downloaded, total_size, progress_percent)
        
        return True
        
    except Exception as e:
        print(f"下载失败: {str(e)}")
        # 删除未完成的下载文件
        if os.path.exists(output_path):
            os.remove(output_path)
        return False


def format_size(size_bytes):
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


if __name__ == "__main__":
    # 测试下载功能
    import sys
    
    def test_progress(downloaded, total, percent):
        downloaded_str = format_size(downloaded)
        total_str = format_size(total)
        sys.stdout.write(f"\r下载进度: {downloaded_str} / {total_str} ({percent:.2f}%)")
        sys.stdout.flush()
    
    print("开始下载Steam AppImage...")
    output_file = "./Steam.AppImage"
    
    success = download_steam_appimage(output_file, progress_callback=test_progress)
    
    if success:
        print("\n✓ 下载成功！")
        file_size = os.path.getsize(output_file)
        print(f"文件大小: {format_size(file_size)}")
    else:
        print("\n✗ 下载失败！")