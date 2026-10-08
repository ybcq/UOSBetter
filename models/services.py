#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统服务管理模块
systemd 服务创建、启动、日志查看等
"""
import shutil
import shutil

import os
import sys
import subprocess
import tempfile
import pwd
import grp

from models.utils import get_real_home
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


def create_service(params):
    """
    创建 systemd 服务
    
    Args:
        params: {
            name: str,
            command: str,
            restart: str
        }
    
    Returns:
        (success, message)
    """
    service_name = params.get('name', '')
    command = params.get('command', '')
    restart_interval = params.get('restart', '5')
    
    if not service_name or not command:
        return False, "服务名称和执行命令不能为空"
    
    # 获取当前用户和组
    import pwd
    import grp
    
    username = os.environ.get('SUDO_USER', os.getlogin())
    try:
        user_info = pwd.getpwnam(username)
        group_info = grp.getgrgid(user_info.pw_gid)
        user = user_info.pw_name
        group = group_info.gr_name
    except Exception:
        return False, "无法获取用户信息"
    
    working_directory = os.path.dirname(os.path.abspath(command))
    
    service_content = f"""[Unit]
Description={service_name} Application
After=network.target

[Service]
User={user}
Group={group}
WorkingDirectory={working_directory}
ExecStart={command}
Restart=always
RestartSec={restart_interval}
SyslogIdentifier={service_name}
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target
"""
    
    service_file = f"/etc/systemd/system/{service_name}.service"
    
    try:
        if is_root():
            with open(service_file, 'w') as f:
                f.write(service_content)
        else:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as tf:
                tf.write(service_content)
                temp_path = tf.name
            subprocess.run(['pkexec', 'cp', temp_path, service_file], check=False)
            os.unlink(temp_path)
        
        os.chmod(service_file, 0o644)
        _print(f"✓ 服务已创建: {service_file}")
        return True, f"服务已创建: {service_file}"
    except Exception as e:
        _print(f"✗ 创建服务失败: {e}")
        return False, f"创建服务失败: {e}"


def _find_terminal():
    """查找可用的终端模拟器"""
    terminals = [
        'x-terminal-emulator', 'gnome-terminal', 'konsole',
        'xfce4-terminal', 'deepin-terminal', 'mate-terminal',
        'lxterminal', 'alacritty', 'kitty', 'xterm'
    ]
    for term in terminals:
        if shutil.which(term):
            return term
    return 'xterm'


def edit_service_file(service_name):
    """编辑服务文件"""
    if not service_name:
        return False, "服务名称不能为空"
    
    service_file = f"/etc/systemd/system/{service_name}.service"
    
    if not os.path.exists(service_file):
        _print(f"✗ 服务文件不存在: {service_file}")
        return False, f"服务文件不存在: {service_file}"
    
    try:
        terminal = _find_terminal()
        editor = os.environ.get('EDITOR', 'nano')
        if terminal in ('gnome-terminal', 'konsole', 'xfce4-terminal', 'mate-terminal', 'lxterminal', 'alacritty', 'kitty'):
            subprocess.Popen([terminal, '-e', f'{editor} {service_file}'])
        else:
            subprocess.Popen([terminal, '-e', f'{editor} {service_file}'])
        _print(f"✓ 已打开编辑器 ({editor})")
        return True, f"已打开编辑器 ({editor})"
    except Exception as e:
        _print(f"✗ 打开编辑器失败: {e}")
        return False, f"打开编辑器失败: {e}"


def start_service(service_name):
    """
    启动服务并设置开机自启
    """
    if not service_name:
        return False, "服务名称不能为空"
    
    service_file = f"/etc/systemd/system/{service_name}.service"
    if not os.path.exists(service_file):
        return False, f"服务文件不存在: {service_file}，请先创建服务"
    
    try:
        _execute("systemctl daemon-reload")
        _execute(f"systemctl start {service_name}")
        _execute(f"systemctl enable {service_name}")
        _print(f"✓ 服务 {service_name} 已启动并设置为开机自启")
        return True, f"服务 {service_name} 已启动并设置为开机自启"
    except Exception as e:
        _print(f"✗ 启动服务失败: {e}")
        return False, f"启动服务失败: {e}"


def read_service_log(service_name):
    """读取服务日志"""
    if not service_name:
        return False, "服务名称不能为空"
    
    try:
        terminal = _find_terminal()
        subprocess.Popen([terminal, '-e', f'journalctl -u {service_name} -f'])
        _print(f"✓ 已打开服务日志 ({terminal})")
        return True, f"已打开服务日志 ({terminal})"
    except Exception as e:
        _print(f"✗ 打开日志失败: {e}")
        return False, f"打开日志失败: {e}"


def manage_services():
    """打开系统服务管理器"""
    try:
        terminal = _find_terminal()
        # Run systemctl and then wait for user to press Enter before closing
        cmd = "sh -c 'systemctl; echo \"Press Enter to close...\" && read line'"
        subprocess.Popen([terminal, '-e', cmd])
        _print(f"✓ 已打开服务管理器 ({terminal})")
        return True, f"已打开服务管理器 ({terminal})"
    except Exception as e:
        _print(f"✗ 打开服务管理器失败: {e}")
        return False, f"打开服务管理器失败: {e}"
def get_running_services():
    """获取运行中的用户服务列表"""
    try:
        result = subprocess.run(
            ['systemctl', '--user', 'list-units', '--type=service', '--state=running', '--no-pager'],
            capture_output=True, text=True, check=False
        )
        return result.stdout
    except Exception as e:
        return str(e)
