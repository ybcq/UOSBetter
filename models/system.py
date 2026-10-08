#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统管理模块
包含内核管理、软件源管理、磁盘挂载、亮度调节等功能
原 data/scripts/ 中的脚本功能已全部迁移至此
"""

import os
import sys
import subprocess
import tempfile
import shutil

from models.utils import get_real_home, get_desktop_dir, substitute_home
from models.privilege import run_with_privilege, is_root


def _execute(cmd, shell=True, use_privilege=True):
    """执行系统命令，返回是否成功"""
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
    
    # 输出结果（截断过长输出）
    result_preview = output.strip() if output.strip() else "(无输出)"
    _print(f"<<< 返回结果: {result_preview}")
    
    return success, output


def _print(msg):
    """输出日志到 stdout（会被 Flask 日志捕获器捕获）"""
    print(msg)


# ==================== 内核管理 ====================

def lock_kernel():
    """锁定内核版本，防止自动更新"""
    _print("执行: 锁定内核版本")
    ok, output = _execute("apt-mark hold linux-image-* linux-headers-*")
    if ok:
        _print("✓ 内核版本已锁定")
    else:
        _print(f"✗ 内核锁定失败: {output}")
    return ok


def unlock_kernel():
    """解锁内核版本"""
    _print("执行: 解锁内核版本")
    ok, output = _execute("apt-mark unhold linux-image-* linux-headers-*")
    if ok:
        _print("✓ 内核版本已解锁")
    else:
        _print(f"✗ 内核解锁失败: {output}")
    return ok


def update_package_list():
    """更新软件包列表"""
    _print("执行: 更新软件包列表")
    ok, output = _execute("apt update")
    if ok:
        _print("✓ 软件包列表已更新")
    else:
        _print(f"✗ 更新失败: {output}")
    return ok


# ==================== 软件源管理 ====================
# 原 APT-Deepin20.sh, APT-TsingHua.sh, APT-UOS20.sh

def set_apt_source(source):
    """
    设置 APT 软件源
    
    Args:
        source: 'deepin20' | 'tsinghua' | 'uos20'
    """
    sources = {
        'deepin20': 'deb https://community-packages.deepin.com/deepin apricot main contrib non-free',
        'tsinghua': 'deb https://mirrors.tuna.tsinghua.edu.cn/debian/ plum main contrib non-free',
        'uos20': 'deb https://home-packages.chinauos.com/home plum main contrib non-free',
    }
    
    if source not in sources:
        _print(f"✗ 未知的软件源: {source}")
        return False
    
    new_source = sources[source]
    sources_file = '/etc/apt/sources.list'
    backup_file = sources_file + '.bak'
    
    # 备份原始文件
    if not is_root():
        subprocess.run(['pkexec', 'cp', sources_file, backup_file], check=False)
    else:
        shutil.copy2(sources_file, backup_file)
    
    # 写入新源
    content = new_source + '\n'
    if is_root():
        with open(sources_file, 'w') as f:
            f.write(content)
    else:
        # 使用 pkexec 写入
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sources') as tf:
            tf.write(content)
            temp_path = tf.name
        
        try:
            subprocess.run(['pkexec', 'cp', temp_path, sources_file], check=False)
        finally:
            os.unlink(temp_path)
    
    _print(f"✓ 已切换到 {source} 源")
    _print(f"  内容: {new_source}")
    return True


# ==================== 文件关联 ====================
# 原 Deepin-Wine.sh, Wine.sh

def set_exe_handler():
    """设置双击打开 .exe 文件，让用户选择 Wine 版本"""
    _print("执行: 设置双击打开 .exe 文件")
    
    # 在 Web 版中，我们返回需要用户确认的信息
    # 实际安装操作会在前端确认后通过 API 调用
    
    # 检查是否已安装 Deepin-Wine
    try:
        result = subprocess.run(['dpkg', '-l', 'deepin-wine'], 
                              capture_output=True, text=True, check=False)
        deepin_installed = result.returncode == 0
    except Exception:
        deepin_installed = False
    
    try:
        result = subprocess.run(['dpkg', '-l', 'wine'], 
                              capture_output=True, text=True, check=False)
        wine_installed = result.returncode == 0
    except Exception:
        wine_installed = False
    
    return {
        "deepin_installed": deepin_installed,
        "wine_installed": wine_installed,
        "message": "请选择要安装的 Wine 版本"
    }


def install_deepin_wine():
    """安装 Deepin-Wine（内部函数）"""
    _print("开始安装 Deepin-Wine")
    
    commands = [
        "apt install -y deepin-wine",
        "apt install -y fonts-wine",
        "apt install -y winetricks",
    ]
    
    for cmd in commands:
        ok, output = _execute(cmd)
        if not ok:
            _print(f"✗ 安装失败: {output}")
            return False
    
    # 创建桌面文件
    home = get_real_home()
    desktop_content = """[Desktop Entry]
Categories=System;
Comment=用于打开EXE
Encoding=UTF-8
Exec=deepin-wine %U
Icon=deepin-wine-assist
MimeType=exe
Name=Deepin-Wine
StartupWMClass=Deepin-Wine
Terminal=false
Type=Application
X-Deepin-Vendor=user-custom
"""
    
    desktop_path = '/usr/share/applications/Deepin-Wine.desktop'
    if not is_root():
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.desktop') as tf:
            tf.write(desktop_content)
            temp_path = tf.name
        subprocess.run(['pkexec', 'cp', temp_path, desktop_path], check=False)
        os.unlink(temp_path)
    else:
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
    
    _print("✓ Deepin-Wine 安装成功")
    return True


def install_wine():
    """安装 Wine（内部函数）"""
    _print("开始安装 Wine")
    
    commands = [
        "apt install -y wine",
        "apt install -y fonts-wine",
        "apt install -y winetricks",
    ]
    
    for cmd in commands:
        ok, output = _execute(cmd)
        if not ok:
            _print(f"✗ 安装失败: {output}")
            return False
    
    # 创建桌面文件
    home = get_real_home()
    desktop_content = """[Desktop Entry]
Categories=System;
Comment=用于打开EXE
Encoding=UTF-8
Exec=wine %U
Icon=wine
MimeType=exe
Name=Wine
StartupWMClass=Wine
Terminal=false
Type=Application
"""
    
    desktop_path = '/usr/share/applications/Wine.desktop'
    if not is_root():
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.desktop') as tf:
            tf.write(desktop_content)
            temp_path = tf.name
        subprocess.run(['pkexec', 'cp', temp_path, desktop_path], check=False)
        os.unlink(temp_path)
    else:
        with open(desktop_path, 'w') as f:
            f.write(desktop_content)
    
    _print("✓ Wine 安装成功")
    return True


def set_exe_handler_with_wine(wine_type):
    """
    设置 .exe 处理器（实际执行安装）
    
    Args:
        wine_type: 'deepin' 或 'wine'
    """
    if wine_type == 'deepin':
        return install_deepin_wine()
    elif wine_type == 'wine':
        return install_wine()
    else:
        _print(f"✗ 未知 Wine 类型: {wine_type}")
        return False


def set_apk_handler():
    """设置 .apk 默认打开方式为 UEngine"""
    _print("执行: 设置双击打开 .apk 文件")
    ok, output = _execute("xdg-mime default uengine.desktop application/vnd.android.package-archive")
    if ok:
        _print("✓ APK 默认打开方式已设置")
    else:
        _print(f"✗ 设置失败: {output}")
    return ok


# ==================== 文件管理器 ====================

def install_tree_file_manager(fm_type='thunar'):
    """安装带目录树的文件管理器"""
    fm_map = {
        'thunar': 'thunar',
        'pcmanfm': 'pcmanfm',
        'nemo': 'nemo'
    }
    pkg = fm_map.get(fm_type, 'thunar')
    _print(f"执行: 安装 {pkg} 文件管理器")
    ok, output = _execute(f"apt install -y {pkg}")
    if ok:
        _print(f"✓ {pkg} 安装成功")
    else:
        _print(f"✗ 安装失败: {output}")
    return ok


def set_default_file_manager(fm_type='thunar'):
    """设置为默认文件管理器"""
    fm_map = {
        'thunar': 'Thunar.desktop',
        'pcmanfm': 'pcmanfm.desktop',
        'nemo': 'nemo.desktop'
    }
    desktop = fm_map.get(fm_type, 'Thunar.desktop')
    _print(f"执行: 设置为默认文件管理器 ({desktop})")
    ok, output = _execute(f"xdg-mime default {desktop} inode/directory")
    if ok:
        _print(f"✓ {desktop} 已设为默认文件管理器")
    else:
        _print(f"✗ 设置失败: {output}")
    return ok


def restore_default_file_manager():
    """还原默认文件管理器"""
    _print("执行: 还原默认文件管理器")
    ok, output = _execute("xdg-mime default dde-file-manager.desktop inode/directory")
    if ok:
        _print("✓ 已还原默认文件管理器")
    else:
        _print(f"✗ 还原失败: {output}")
    return ok


# ==================== 磁盘挂载 ====================
# 原 Wine-Disk.sh, Win-Like.sh

def set_wine_c():
    """挂载 Wine 的 C 盘为盘符"""
    _print("执行: 挂载 Wine C 盘")
    
    home = get_real_home()
    wine_c = os.path.join(home, '.wine', 'drive_c')
    mount_point = f"/media/{os.environ.get('SUDO_USER', os.getenv('USER'))}/Wine-C"
    
    if not os.path.exists(wine_c):
        _print(f"✗ 未找到 Wine C 盘: {wine_c}")
        _print("  请先运行 winecfg 或任意 Wine 程序初始化 Wine 环境")
        return False
    
    # 卸载旧的挂载
    _execute(f"umount {mount_point}", use_privilege=False)
    
    # 创建挂载点并挂载
    ok1, _ = _execute(f"mkdir -p {mount_point}")
    ok2, output = _execute(f"mount --bind {wine_c} {mount_point}")
    
    if ok1 or ok2:
        _print(f"✓ Wine C 盘挂载成功: {mount_point}")
        return True
    else:
        _print(f"✗ 挂载失败: {output}")
        return False


def unset_wine_c():
    """卸载 Wine C 盘"""
    _print("执行: 卸载 Wine C 盘")
    real_home = get_real_home()
    username = os.environ.get('SUDO_USER', os.getenv('USER'))
    mount_point = f"/media/{username}/Wine-C"
    
    ok, output = _execute(f"umount {mount_point}")
    if ok:
        _print("✓ Wine C 盘已卸载")
    else:
        _print(f"✗ 卸载失败: {output}")
    return ok


def set_win_disk():
    """挂载 Windows 风格系统盘盘符"""
    _print("执行: 挂载 Windows 风格磁盘")
    
    home = get_real_home()
    win_drive = os.path.join(home, '.local', 'share', 'UOSBetter', 'WinLike')
    mount_point = f"/media/{os.environ.get('SUDO_USER', os.getenv('USER'))}/WinLike"
    
    # 清理旧目录
    if os.path.exists(win_drive):
        shutil.rmtree(win_drive)
    os.makedirs(win_drive, exist_ok=True)
    
    # 创建软链接映射
    mappings = {
        'Users': '/home',
        'Program Files': '/usr',
        'Program Files (x86)': '/opt',
        'Windows': '/etc',
        'System32': '/usr/bin',
        '开始菜单（系统）': '/usr/share/applications',
    }
    
    for name, target in mappings.items():
        link_path = os.path.join(win_drive, name)
        if os.path.exists(link_path):
            os.remove(link_path)
        os.symlink(target, link_path)
    
    # 用户开始菜单
    user_apps = os.path.join(home, '.local', 'share', 'applications')
    if not os.path.exists(user_apps):
        os.makedirs(user_apps, exist_ok=True)
    user_menu_link = os.path.join(win_drive, '开始菜单（用户）')
    if os.path.exists(user_menu_link):
        os.remove(user_menu_link)
    os.symlink(user_apps, user_menu_link)
    
    _print(f"✓ 目录映射创建完成: {win_drive}")
    
    # 挂载为磁盘
    ok1, _ = _execute(f"umount {mount_point}", use_privilege=False)
    ok2, _ = _execute(f"mkdir -p {mount_point}")
    ok3, output = _execute(f"mount --bind {win_drive} {mount_point}")
    
    if ok3:
        _print(f"✓ Windows 风格磁盘挂载成功: {mount_point}")
        return True
    else:
        _print(f"✗ 挂载失败: {output}")
        return False


def unset_win_disk():
    """卸载 Windows 风格磁盘"""
    _print("执行: 卸载 Windows 风格磁盘")
    real_home = get_real_home()
    username = os.environ.get('SUDO_USER', os.getenv('USER'))
    mount_point = f"/media/{username}/WinLike"
    win_drive = os.path.join(real_home, '.local', 'share', 'UOSBetter', 'WinLike')
    
    ok1, _ = _execute(f"umount {mount_point}")
    
    if os.path.exists(win_drive):
        shutil.rmtree(win_drive)
        _print(f"✓ 已清理目录: {win_drive}")
    
    if ok1:
        _print("✓ Windows 风格磁盘已卸载并清理")
    else:
        _print("✗ 卸载失败")
    return ok1


# ==================== 美化 ====================

def install_win_theme():
    """安装 Windows 主题"""
    _print("执行: 安装 Windows 主题")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = os.path.dirname(script_dir)  # 回到项目根目录
    tar_path = os.path.join(script_dir, 'data', 'themes', 'win11theme.tar')
    target_dir = os.path.join(get_real_home(), '.local', 'share')
    
    if not os.path.exists(tar_path):
        _print(f"✗ 主题文件不存在: {tar_path}")
        return False
    
    os.makedirs(target_dir, exist_ok=True)
    ok, output = _execute(f'tar -xvf "{tar_path}" -C "{target_dir}"')
    if ok:
        _print("✓ Windows 主题安装成功")
        _print("  请在控制中心 -> 个性化 -> 图标主题 选择 Light")
        _print("  注销当前用户再登录生效")
    else:
        _print(f"✗ 主题安装失败: {output}")
    return ok


def install_win_fonts():
    """安装 Windows 字体"""
    _print("执行: 安装 Windows 字体")
    ok, output = _execute("apt install -y ttf-mscorefonts-installer")
    if ok:
        _print("✓ Windows 字体安装成功")
        _print("  请在控制中心 -> 个性化 -> 字体 -> 标准字体 选择 微软雅黑")
    else:
        _print(f"✗ 字体安装失败: {output}")
    return ok


def install_mask_brightness():
    """安装遮罩亮度调节"""
    _print("执行: 安装亮度调节工具")
    ok, output = _execute("apt install -y brightnessctl")
    if ok:
        _print("✓ 亮度调节工具安装成功")
    else:
        _print(f"✗ 安装失败: {output}")
    return ok


def set_brightness(level):
    """设置亮度"""
    _print(f"执行: 设置亮度 {level}%")
    ok, output = _execute(f"brightnessctl set {level}%")
    if not ok:
        _print(f"✗ 亮度设置失败: {output}")
    return ok
