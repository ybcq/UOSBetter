#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import os
import sys

APP_NAME = 'UOS系统优化大师'
APP_VERSION = '2.0.0'
UPDATE_LOG = """
V2.0.0
- 全面重构为 Flask Web 应用，浏览器访问本地服务
- 左侧标签栏 + 右侧内容页布局
- 移除 PySimpleGUI 依赖
- 所有脚本功能改为 Python 实现
- 使用 pkexec 进行权限提升，无需全局 sudo
- AppImage 默认目录迁移至 ~/.local/share/UOSBetter/appimages/
- 桌面图标改为动态生成，删除 desktops 文件夹
- 实时日志流显示
- 重新规划标签页：系统安全、软件组件、应用商店、美化定制、桌面与菜单、服务与软件包

V1.5.0
- 修复带目录的文件管理器设置为默认文件管理器后，无法打开的问题
- 删除部分图标，提升在XFCE上的兼容性

V1.4.0
- 修改带目录的文件管理器为thunar
- 进一步补全Win11主题的图标，提升在XFCE上的兼容性

V1.3.0
- 修改带目录的文件管理器为PCManFM
- 增加挂载Wine的C盘为盘符功能
- 增加系统盘显示为Windows风格文件夹的功能
- 双击打开.exe文件支持选择安装Deepin-Wine或Wine
- 安装Wine时自动安装常用字体

V1.2.0
- 修复了创建的图标启动目录为桌面的问题
- 主题中增加了压缩包和NEMO的图标
- 修改复制操作的原文件为绝对地址

V1.1.0
- 增加了TAR等格式的绿色软件的安装卸载功能
- Steam改为在线获取，大幅缩小软件体积

V1.0.0
- 部分功能支持Debian系的其他系统
- 比如Ubuntu，GXDE，AnduinOS，Raspbian等
"""

# 路径定义
def get_real_home():
    """获取真正用户的 home 目录（解决 sudo 下 ~ 展开为 /root 的问题）"""
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        try:
            import pwd
            return pwd.getpwnam(sudo_user).pw_dir
        except KeyError:
            pass
    return os.path.expanduser('~')


def get_desktop_dir():
    """获取桌面目录路径（支持中文"桌面"和英文"Desktop"）"""
    home = get_real_home()
    desktop_cn = os.path.join(home, "桌面")
    desktop_en = os.path.join(home, "Desktop")
    
    if os.path.exists(desktop_cn):
        return desktop_cn
    elif os.path.exists(desktop_en):
        return desktop_en
    else:
        return desktop_en


def substitute_home(value):
    """替换路径中的 ~ 为实际 home 目录"""
    if value and value.startswith("~"):
        return value.replace("~", get_real_home(), 1)
    return value


def format_size(size_bytes):
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def ensure_dirs():
    """确保必要目录存在"""
    home = get_real_home()
    
    # AppImage 安装目录（新路径）
    appimage_dir = os.path.join(home, '.local', 'share', 'UOSBetter', 'appimages')
    os.makedirs(appimage_dir, exist_ok=True)
    
    # 应用菜单目录
    app_menu_dir = os.path.join(home, '.local', 'share', 'applications')
    os.makedirs(app_menu_dir, exist_ok=True)
    
    # 图标目录
    icon_dir = os.path.join(home, '.local', 'share', 'icons', 'hicolor', 'scalable', 'apps')
    os.makedirs(icon_dir, exist_ok=True)
    
    # YPK 虚拟环境目录（保留兼容）
    ypk_dir = os.path.join(home, '.local', 'share', 'apps')
    os.makedirs(ypk_dir, exist_ok=True)
    
    # 文件管理器右键菜单目录
    fm_actions_dir = os.path.join(home, '.local', 'share', 'file-manager', 'actions')
    os.makedirs(fm_actions_dir, exist_ok=True)


# 默认 AppImage 目录（2.0 新路径）
DEFAULT_APPIMAGE_DIR = os.path.join(get_real_home(), '.local', 'share', 'UOSBetter', 'appimages')
# 旧版 YPK 安装目录（兼容保留）
DEFAULT_YPK_APP_DIR = os.path.join(get_real_home(), '.local', 'share', 'apps')
