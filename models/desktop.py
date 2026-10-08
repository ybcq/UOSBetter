#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
桌面图标与菜单管理模块
动态创建 .desktop 文件，不再依赖 data/desktops/ 静态文件
"""

import os
import sys
import subprocess
import shutil

from models.utils import get_real_home, get_desktop_dir


def _execute(cmd, shell=True, use_privilege=True):
    from models.privilege import run_with_privilege, is_root
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


def generate_desktop_content(name, exec_cmd, icon, comment="", categories="Utility;", terminal="false", mime_type=""):
    """
    生成 .desktop 文件内容
    
    Args:
        name: 应用名称
        exec_cmd: 执行命令
        icon: 图标名称或路径
        comment: 描述
        categories: 分类
        terminal: 是否在终端运行
        mime_type: MIME 类型
    
    Returns:
        str: .desktop 文件内容
    """
    lines = [
        "[Desktop Entry]",
        f"Name={name}",
        f"Comment={comment}",
        f"Exec={exec_cmd}",
        f"Icon={icon}",
        f"Terminal={terminal}",
        "Type=Application",
        f"Categories={categories}",
    ]
    
    if mime_type:
        lines.append(f"MimeType={mime_type}")
    
    return "\n".join(lines) + "\n"


def write_desktop_file(file_path, content):
    """
    写入 .desktop 文件并设置权限
    
    Args:
        file_path: 目标路径
        content: 文件内容
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    os.chmod(file_path, 0o755)


def handle_system_icon_selection(icon_path):
    """
    处理系统图标选择
    如果图标不在系统目录，复制到用户本地目录
    
    Args:
        icon_path: 图标路径
    
    Returns:
        str: 图标名称（用于 .desktop 的 Icon 字段）
    """
    if not icon_path:
        return "application-x-executable"
    
    system_icon_dir = "/usr/share/icons/hicolor/scalable/apps"
    home = get_real_home()
    local_icon_dir = os.path.join(home, ".local", "share", "icons", "hicolor", "scalable", "apps")
    
    icon_filename = os.path.basename(icon_path)
    icon_name = os.path.splitext(icon_filename)[0]
    
    # 如果不在系统目录，复制到用户目录
    if not icon_path.startswith(system_icon_dir):
        try:
            os.makedirs(local_icon_dir, exist_ok=True)
            target_path = os.path.join(local_icon_dir, icon_filename)
            if not os.path.exists(target_path):
                shutil.copy2(icon_path, target_path)
                _print(f"图标已复制到本地目录: {target_path}")
        except Exception as e:
            _print(f"复制图标失败: {e}")
    
    return icon_name


def create_shortcut(params):
    """
    创建桌面快捷方式
    
    Args:
        params: {
            name: str,
            exec_path: str,
            icon_path: str,
            args: str,
            sudo: bool,
            location: 'desktop' | 'applist'
        }
    
    Returns:
        (success, message)
    """
    name = params.get('name', '')
    exec_path = params.get('exec_path', '')
    icon_path = params.get('icon_path', '')
    args = params.get('args', '%U')
    sudo = params.get('sudo', False)
    location = params.get('location', 'desktop')
    
    if not name or not exec_path:
        return False, "名称和程序路径不能为空"
    
    # 处理 Windows 程序
    if exec_path.lower().endswith(".exe"):
        exec_prefix = "deepin-wine"
        exec_path = exec_path.replace("\\", "/")
    elif exec_path.lower().endswith(".py"):
        exec_prefix = "python3"
    else:
        exec_prefix = ""
    
    if sudo:
        exec_prefix = "pkexec" if not exec_prefix else f"pkexec {exec_prefix}"
    
    # 处理路径中的空格
    if " " in exec_path and not exec_path.startswith('"'):
        exec_path = f'"{exec_path}"'
    
    exec_cmd = f"{exec_prefix} {exec_path} {args}".strip()
    
    # 处理图标
    icon_name = handle_system_icon_selection(icon_path)
    
    # 生成 .desktop 内容
    content = generate_desktop_content(
        name=name,
        exec_cmd=exec_cmd,
        icon=icon_name,
        terminal="false",
        categories="Utility;"
    )
    
    # 确定保存位置
    home = get_real_home()
    if location == 'desktop':
        desktop_path = os.path.join(get_desktop_dir(), f"{name}.desktop")
    else:
        app_dir = os.path.join(home, ".local", "share", "applications")
        os.makedirs(app_dir, exist_ok=True)
        desktop_path = os.path.join(app_dir, f"{name}.desktop")
    
    try:
        write_desktop_file(desktop_path, content)
        _print(f"✓ 快捷方式已创建: {desktop_path}")
        return True, f"快捷方式已创建: {desktop_path}"
    except Exception as e:
        _print(f"✗ 创建快捷方式失败: {e}")
        return False, f"创建快捷方式失败: {e}"


def create_context_menu(params):
    """
    创建右键菜单项
    
    Args:
        params: {
            name: str,
            command: str,
            icon_path: str,
            menu_type: 'file' | 'directory',
            location: 'user' | 'system'
        }
    
    Returns:
        (success, message)
    """
    name = params.get('name', '')
    command = params.get('command', '')
    icon_path = params.get('icon_path', '')
    menu_type = params.get('menu_type', 'file')
    location = params.get('location', 'user')
    
    if not name or not command:
        return False, "菜单名称和执行命令不能为空"
    
    home = get_real_home()
    
    if location == 'user':
        target_dir = os.path.join(home, ".local", "share", "file-manager", "actions")
    else:
        target_dir = "/usr/share/file-manager/actions"
        if not os.access(target_dir, os.W_OK):
            return False, "系统级菜单需要管理员权限，请使用 pkexec 提升"
    
    os.makedirs(target_dir, exist_ok=True)
    
    # 处理图标
    icon_name = handle_system_icon_selection(icon_path)
    
    # 设置 MimeTypes
    if menu_type == 'file':
        mime_types = "text/plain;application/*;"
    else:
        mime_types = "inode/directory;"
    
    # 生成文件名
    desktop_filename = name.lower().replace(" ", "-") + ".desktop"
    desktop_path = os.path.join(target_dir, desktop_filename)
    
    content = f"""[Desktop Entry]
Type=Action
Name={name}
Profiles=profile-zero;

[X-Action-Profile profile-zero]
MimeTypes={mime_types}
Name=Default profile
Exec={command} %F
Path={os.path.dirname(command)}
Icon={icon_name}
"""
    
    try:
        write_desktop_file(desktop_path, content)
        _print(f"✓ 右键菜单项已创建: {desktop_path}")
        
        # 刷新文件管理器
        subprocess.Popen(['nautilus', '-q'])
        subprocess.Popen(['nautilus'])
        
        return True, f"右键菜单项已创建: {desktop_path}"
    except Exception as e:
        _print(f"✗ 创建右键菜单失败: {e}")
        return False, f"创建右键菜单失败: {e}"


def add_uosbetter_desktop_icon():
    """添加 UOSBetter 自身的桌面图标"""
    _print("执行: 添加 UOSBetter 桌面图标")
    
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    script_path = os.path.abspath(__file__)
    # 回退到项目根目录的 UOSBetter.py 或 app.py
    script_dir = os.path.dirname(os.path.dirname(script_path))
    main_script = os.path.join(script_dir, 'UOSBetter.py')
    
    icon_name = "preferences-system"
    
    # 2.0 不再需要 sudo
    desktop_content = f"""[Desktop Entry]
Name=UOS系统优化大师
Exec=python3 {main_script}
Path={os.path.dirname(main_script)}
Icon={icon_name}
Terminal=true
Type=Application
Categories=Utility;System;
"""
    
    desktop_path = os.path.join(desktop_dir, "UOS系统优化大师.desktop")
    app_menu_path = os.path.join(home, ".local", "share", "applications", "UOS系统优化大师.desktop")
    
    # 删除旧图标
    for p in [desktop_path, app_menu_path]:
        if os.path.exists(p):
            os.remove(p)
    
    try:
        write_desktop_file(desktop_path, desktop_content)
        write_desktop_file(app_menu_path, desktop_content)
        _print(f"✓ 桌面图标已创建: {desktop_path}")
        _print(f"✓ 开始菜单图标已创建: {app_menu_path}")
        return True
    except Exception as e:
        _print(f"✗ 图标创建失败: {e}")
        return False


def get_installed_apps():
    """获取已安装的应用列表（从 applications 目录扫描）"""
    home = get_real_home()
    apps_dir = os.path.join(home, '.local', 'share', 'applications')
    
    apps = []
    if os.path.isdir(apps_dir):
        for f in os.listdir(apps_dir):
            if f.endswith('.desktop'):
                path = os.path.join(apps_dir, f)
                try:
                    with open(path, 'r') as fh:
                        content = fh.read()
                    name = ""
                    for line in content.split('\n'):
                        if line.startswith('Name='):
                            name = line.split('=', 1)[1]
                            break
                    apps.append({"name": name or f, "file": f, "path": path})
                except Exception:
                    pass
    return apps


def get_installed_shortcuts():
    """获取已安装的快捷方式列表"""
    desktop_dir = get_desktop_dir()
    apps_dir = os.path.join(get_real_home(), '.local', 'share', 'applications')
    
    shortcuts = []
    
    for d in [desktop_dir, apps_dir]:
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith('.desktop'):
                    path = os.path.join(d, f)
                    try:
                        with open(path, 'r') as fh:
                            content = fh.read()
                        name = ""
                        exec_cmd = ""
                        for line in content.split('\n'):
                            if line.startswith('Name='):
                                name = line.split('=', 1)[1]
                            elif line.startswith('Exec='):
                                exec_cmd = line.split('=', 1)[1]
                        shortcuts.append({
                            "name": name or f,
                            "file": f,
                            "path": path,
                            "exec": exec_cmd
                        })
                    except Exception:
                        pass
    
    return shortcuts
