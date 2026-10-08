#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限提升模块
使用 pkexec 进行临时权限提升，替代全局 sudo
"""

import os
import subprocess
import shutil

PKEXEC_AVAILABLE = shutil.which('pkexec') is not None


def is_root():
    """检查当前是否以 root 权限运行"""
    return os.geteuid() == 0


def run_with_privilege(command, shell=True, capture_output=True):
    """
    使用 pkexec 提升权限执行命令
    
    Args:
        command: 要执行的命令（字符串或列表）
        shell: 是否使用 shell 执行
        capture_output: 是否捕获输出
    
    Returns:
        (success, output): 是否成功和输出内容
    """
    if is_root():
        # 已经是 root，直接执行
        try:
            result = subprocess.run(
                command, shell=shell, capture_output=capture_output,
                text=True, check=False
            )
            output = result.stdout.strip() if capture_output else ""
            if result.returncode != 0:
                err = result.stderr.strip() if capture_output else ""
                return False, f"{output}\n{err}".strip()
            return True, output
        except Exception as e:
            return False, str(e)
    
    if not PKEXEC_AVAILABLE:
        return False, "系统中未找到 pkexec，无法提升权限。请安装 polkit 或手动使用 sudo。"
    
    # 使用 pkexec 提升权限
    try:
        if isinstance(command, list):
            cmd = ['pkexec'] + command
        else:
            cmd = ['pkexec', 'bash', '-c', command]
        
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, check=False
        )
        output = result.stdout.strip() if capture_output else ""
        if result.returncode != 0:
            err = result.stderr.strip() if capture_output else ""
            return False, f"{output}\n{err}".strip()
        return True, output
    except Exception as e:
        return False, str(e)


def run_script_with_privilege(script_path, interpreter='bash'):
    """
    以提升的权限运行脚本
    
    Args:
        script_path: 脚本路径
        interpreter: 解释器（bash/sh/python3 等）
    """
    if not os.path.exists(script_path):
        return False, f"脚本不存在: {script_path}"
    
    # 设置执行权限
    os.chmod(script_path, 0o755)
    
    if is_root():
        cmd = [interpreter, script_path]
    else:
        cmd = ['pkexec', interpreter, script_path]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            return False, f"{output}\n{err}".strip()
        return True, output
    except Exception as e:
        return False, str(e)


def require_privilege():
    """
    检查是否有权限，如果没有则尝试提升
    返回 (has_privilege, message)
    """
    if is_root():
        return True, ""
    if PKEXEC_AVAILABLE:
        return False, "需要管理员权限"
    return False, "需要管理员权限，且未找到 pkexec"
