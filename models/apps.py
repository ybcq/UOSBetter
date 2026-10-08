#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用管理模块
包含应用商店、Wine、Steam、Barrier、SpaceDesk 等功能
"""

import os
import sys
import subprocess
import tempfile
import shutil

from models.utils import get_real_home, get_desktop_dir, format_size, DEFAULT_APPIMAGE_DIR
from models.privilege import run_with_privilege, is_root
from models.desktop import generate_desktop_content, write_desktop_file


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


# ==================== 应用商店 ====================

def install_spark_store():
    """安装星火应用商店"""
    _print("执行: 安装星火应用商店")
    ok, output = _execute("apt install -y spark-store")
    if ok:
        _print("✓ 星火应用商店安装成功")
    else:
        _print(f"✗ 安装失败: {output}")
    return ok


def set_pip_source(source='tsinghua'):
    """替换 PIP 源"""
    sources = {
        'tsinghua': 'https://pypi.tuna.tsinghua.edu.cn/simple',
        'aliyun': 'https://mirrors.aliyun.com/pypi/simple/',
        'douban': 'https://pypi.douban.com/simple/',
        'default': 'https://pypi.org/simple',
    }
    
    url = sources.get(source, sources['tsinghua'])
    _print(f"执行: 替换 PIP 源为 {source}")
    
    ok, output = _execute(f"pip config set global.index-url {url}")
    if ok:
        _print(f"✓ PIP 源已切换为: {url}")
    else:
        _print(f"✗ 切换失败: {output}")
    return ok


def add_flat_store_icon():
    """添加 Flatpak 应用商店图标"""
    _print("执行: 添加 Flatpak 应用商店图标")
    
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    
    # 动态生成 .desktop 内容
    content = generate_desktop_content(
        name="Flathub 应用商店",
        exec_cmd="xdg-open https://flathub.org/zh-Hans",
        icon="deepin-app-store",
        comment="浏览并安装 Flathub 应用",
        categories="Network;"
    )
    
    # 复制到本地应用目录和桌面
    app_menu_path = os.path.join(home, '.local', 'share', 'applications', 'flatpak.desktop')
    desktop_path = os.path.join(desktop_dir, 'flatpak.desktop')
    
    write_desktop_file(app_menu_path, content)
    write_desktop_file(desktop_path, content)
    
    _print("✓ Flatpak 商店图标已创建")
    return True


def add_appimage_store_icon():
    """添加 AppImage 应用商店图标"""
    _print("执行: 添加 AppImage 应用商店图标")
    
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    appimage_dir = DEFAULT_APPIMAGE_DIR
    
    # 复制 AppImagePool.AppImage 到新目录
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_appimage = os.path.join(script_dir, 'data', 'appImages', 'AppImagePool.AppImage')
    
    if os.path.exists(source_appimage):
        target_appimage = os.path.join(appimage_dir, 'AppImagePool.AppImage')
        shutil.copy2(source_appimage, target_appimage)
        os.chmod(target_appimage, 0o755)
        _print(f"✓ AppImage 已复制到: {target_appimage}")
    
    # 动态生成 .desktop 内容
    appimage_path = os.path.join(appimage_dir, 'AppImagePool.AppImage')
    content = generate_desktop_content(
        name="AppImage 应用商店",
        exec_cmd=appimage_path,
        icon="deepin-app-store",
        comment="浏览并下载 AppImage 应用",
        categories="Network;"
    )
    
    app_menu_path = os.path.join(home, '.local', 'share', 'applications', 'appimage.desktop')
    desktop_path = os.path.join(desktop_dir, 'appimage.desktop')
    
    write_desktop_file(app_menu_path, content)
    write_desktop_file(desktop_path, content)
    
    _print("✓ AppImage 商店图标已创建")
    return True


# ==================== 软件组件 ====================

def install_shared_input():
    """安装 Barrier（多电脑共享键鼠）"""
    _print("执行: 安装 Barrier")
    ok, output = _execute("apt install -y barrier")
    if ok:
        _print("✓ Barrier 安装成功，正在打开配置界面...")
        subprocess.Popen(['barrier'])
    else:
        _print(f"✗ 安装失败: {output}")
    return ok


def install_multi_screen_app():
    """安装副屏 App（SpaceDesk）"""
    _print("执行: 打开副屏应用安装包")
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    apk_path = os.path.join(script_dir, 'data', 'apks', 'SpaceDesk.apk')
    
    if os.path.exists(apk_path):
        subprocess.Popen(['xdg-open', apk_path])
        _print(f"✓ 已打开: {apk_path}")
        return True
    else:
        _print(f"✗ APK 文件不存在: {apk_path}")
        return False


# ==================== Steam ====================

def download_steam_appimage(output_path, progress_callback=None):
    """下载 Steam AppImage"""
    from models.GetRelease import download_file_with_progress
    
    steam_url = "https://github.com/ivan-hc/Steam-appimage/releases/download/1.0.0.85-6%402026-05-01_1777622844/Steam-1.0.0.85-6-anylinux-x86_64.AppImage"
    
    return download_file_with_progress(steam_url, output_path, progress_callback=progress_callback)


def install_steam(progress_callback=None):
    """安装 Steam 便携版"""
    _print("执行: 安装 Steam 便携版")
    
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    appimage_dir = DEFAULT_APPIMAGE_DIR
    steam_target = os.path.join(appimage_dir, 'Steam.AppImage')
    
    _print("开始从 GitHub 下载 Steam AppImage...")
    success = download_steam_appimage(steam_target, progress_callback=progress_callback)
    
    if not success:
        _print("✗ Steam AppImage 下载失败")
        return False
    
    _print("✓ Steam AppImage 下载成功")
    os.chmod(steam_target, 0o755)
    
    # 创建桌面图标和开始菜单图标
    content = generate_desktop_content(
        name="Steam",
        exec_cmd=steam_target,
        icon="steam",
        comment="Steam 游戏平台",
        categories="Game;"
    )
    
    app_menu_path = os.path.join(home, '.local', 'share', 'applications', 'steam.desktop')
    desktop_path = os.path.join(desktop_dir, 'steam.desktop')
    
    write_desktop_file(app_menu_path, content)
    write_desktop_file(desktop_path, content)
    
    _print("✓ Steam 安装完成")
    return True
