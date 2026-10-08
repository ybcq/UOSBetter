#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
软件包管理模块
YPK 和 TAR 格式软件的安装与卸载
"""

import os
import sys
import shutil
import tempfile
import tarfile
import re

from models.utils import get_real_home, DEFAULT_APPIMAGE_DIR, DEFAULT_YPK_APP_DIR
from models.privilege import run_with_privilege, is_root


def _execute(cmd, shell=True, use_privilege=True):
    """执行系统命令"""
    display_cmd = cmd if isinstance(cmd, str) else ' '.join(cmd)
    _print(f">>> 执行命令: {display_cmd}")
    
    if use_privilege and not is_root():
        success, output = run_with_privilege(cmd, shell=shell)
    else:
        try:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, check=False)
            output = result.stdout.strip()
            if result.returncode != 0:
                err = result.stderr.strip()
                output = f"{output}\n{err}".strip()
            success = result.returncode == 0
        except Exception as e:
            success = False
            output = str(e)
    
    result_preview = output.strip() if output.strip() else "(无输出)"
    _print(f"<<< 返回结果: {result_preview}")
    
    return success, output


def _print(msg):
    print(msg)


def install_package(params):
    """
    安装软件包（YPK 或 TAR）
    
    Args:
        params: {
            path: str,
            isolate: bool
        }
    
    Returns:
        bool: 是否成功
    """
    package_path = params.get('path', '')
    isolate = params.get('isolate', True)
    
    if not package_path or not os.path.exists(package_path):
        _print(f"✗ 文件不存在: {package_path}")
        return False
    
    _print(f"开始安装: {package_path}")
    
    try:
        if package_path.lower().endswith('.ypk'):
            _print("检测到 YPK 格式软件包")
            from models.InstallYPK import install_ypk, install_ypk_safe
            if isolate:
                _print("使用隔离模式（虚拟环境）安装")
                result = install_ypk_safe(package_path)
            else:
                _print("使用 LOCAL 模式安装")
                result = install_ypk(package_path)
        elif package_path.lower().endswith(('.tar', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2')):
            _print("检测到 TAR 格式软件包")
            from models.InstallTAR import install_tar_archive
            result = install_tar_archive(package_path)
        else:
            _print("✗ 不支持的文件格式")
            return False
        
        if result:
            _print("✓ 安装成功")
        else:
            _print("✗ 安装失败")
        return result
        
    except Exception as e:
        _print(f"✗ 安装过程出错: {e}")
        return False


def uninstall_package(params):
    """
    卸载软件包（仅 YPK）
    
    Args:
        params: {
            path: str,
            isolate: bool
        }
    
    Returns:
        bool: 是否成功
    """
    package_path = params.get('path', '')
    isolate = params.get('isolate', True)
    
    if not package_path or not os.path.exists(package_path):
        _print(f"✗ 文件不存在: {package_path}")
        return False
    
    if not package_path.lower().endswith('.ypk'):
        _print("✗ 仅支持 YPK 格式软件包的卸载")
        return False
    
    _print(f"开始卸载: {package_path}")
    
    try:
        from models.InstallYPK import uninstall_ypk, uninstall_ypk_safe
        if isolate:
            _print("使用隔离模式（虚拟环境）卸载")
            result = uninstall_ypk_safe(package_path)
        else:
            _print("使用 LOCAL 模式卸载")
            result = uninstall_ypk(package_path)
        
        if result:
            _print("✓ 卸载成功")
        else:
            _print("✗ 卸载失败")
        return result
        
    except Exception as e:
        _print(f"✗ 卸载过程出错: {e}")
        return False


def get_package_info(params):
    """
    获取软件包信息
    
    Args:
        params: {
            path: str
        }
    
    Returns:
        dict: 包信息
    """
    package_path = params.get('path', '')
    
    if not package_path or not os.path.exists(package_path):
        return {"error": "文件不存在"}
    
    info = {
        "path": package_path,
        "filename": os.path.basename(package_path),
        "size": os.path.getsize(package_path),
        "format": "",
    }
    
    if package_path.lower().endswith('.ypk'):
        info["format"] = "YPK"
        try:
            from models.InstallYPK import extract_ypk
            import xml.etree.ElementTree as ET
            temp_dir = extract_ypk(package_path)
            if temp_dir:
                control_path = os.path.join(temp_dir, 'control.xml')
                if os.path.exists(control_path):
                    tree = ET.parse(control_path)
                    root = tree.getroot()
                    info["name"] = root.get("name", "Unknown")
                    info["version"] = root.get("version", "Unknown")
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            info["parse_error"] = str(e)
    elif package_path.lower().endswith(('.tar', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2')):
        info["format"] = "TAR"
        try:
            with tarfile.open(package_path, 'r:*') as tar:
                members = tar.getmembers()
                info["file_count"] = len(members)
        except Exception as e:
            info["parse_error"] = str(e)
    
    return info
