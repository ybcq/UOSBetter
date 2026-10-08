#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UOSBetter 2.0 - Flask Web Application
主程序入口，提供 Web 界面和 API
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
import re
import time
import threading
import queue
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

# 屏蔽 Flask 自带请求日志，避免日志面板被淹没
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('flask').setLevel(logging.ERROR)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.utils import (
    get_real_home, get_desktop_dir, format_size, APP_NAME, APP_VERSION, UPDATE_LOG,
    ensure_dirs, substitute_home
)
from models.privilege import run_with_privilege, is_root, PKEXEC_AVAILABLE
from models.system import (
    lock_kernel, unlock_kernel, update_package_list,
    set_apt_source, set_exe_handler, set_exe_handler_with_wine, set_apk_handler,
    install_tree_file_manager, set_default_file_manager, restore_default_file_manager,
    set_wine_c, unset_wine_c, set_win_disk, unset_win_disk,
    install_win_theme, install_win_fonts, install_mask_brightness
)
from models.apps import (
    install_spark_store, set_pip_source,
    install_shared_input, install_multi_screen_app,
    download_steam_appimage, install_steam,
    add_flat_store_icon, add_appimage_store_icon
)
from models.desktop import (
    create_shortcut, create_context_menu,
    add_uosbetter_desktop_icon, get_installed_apps, get_installed_shortcuts
)
from models.services import (
    create_service, edit_service_file, start_service,
    read_service_log, manage_services, get_running_services
)
from models.packages import (
    install_package, uninstall_package, get_package_info
)

app = Flask(__name__)
app.secret_key = 'UOSBetter-2.0-Secret-Key'

# SSE 日志队列
log_queues = {}
log_lock = threading.Lock()


def get_client_id():
    """为每个 SSE 连接生成唯一 ID"""
    return f"client_{threading.current_thread().ident}_{int(time.time()*1000)}"


def broadcast_log(message):
    """向所有 SSE 客户端广播日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    formatted = f"[{timestamp}] {message}"
    with log_lock:
        for q in list(log_queues.values()):
            try:
                q.put(formatted)
            except Exception:
                pass


class LogCapture:
    """捕获业务 print 输出并广播，仅过滤 Flask/werkzeug 服务请求日志"""
    def __init__(self):
        self.messages = []
        self._lock = threading.Lock()
    
    def _should_filter(self, msg: str) -> bool:
        lower = msg.lower()
        # 只过滤 Flask/werkzeug 的 HTTP 请求日志
        if any(k in lower for k in [
            'werkzeug', ' Serving ', 'pin ', 'get /', 'post /', 'put /', 'delete /',
            'http/1.1', 'http/1.0',
        ]):
            return True
        # 过滤纯空白
        return not msg.strip()
    
    def write(self, msg):
        if self._should_filter(msg):
            return len(msg)
        text = msg.strip()
        if not text:
            return len(msg)
        # 按行拆分，逐行广播，确保完整输出每条日志
        for line in text.splitlines():
            if line:
                broadcast_log(line)
                with self._lock:
                    self.messages.append(line)
                    if len(self.messages) > 1000:
                        self.messages.pop(0)
        return len(msg)
    
    def flush(self):
        pass


# 全局日志捕获器
log_capture = LogCapture()
sys.stdout = log_capture
sys.stderr = log_capture


# ========== 文件/文件夹选择 API (使用 zenity) ==========
@app.route('/api/pick-file')
def api_pick_file():
    """使用 zenity 选择本地文件，返回完整路径"""
    if not shutil.which('zenity'):
        return jsonify({'success': False, 'message': '未找到 zenity，无法打开文件选择器', 'data': None})

    title = request.args.get('title', '选择文件')
    filt = request.args.get('filter', '')
    default = request.args.get('default', os.path.expanduser('~'))

    file_filter = '--file-filter=所有文件 (*.*)|*.*'
    if filt:
        exts = [e.strip().lower() for e in filt.split(',') if e.strip()]
        if exts:
            patterns = ' '.join(f'*{e}' for e in exts)
            file_filter = f'--file-filter={title} ({patterns})|{patterns}'

    cmd = [
        'zenity', '--file-selection',
        f'--title={title}',
        file_filter,
        f'--filename={default}'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        path = result.stdout.strip()
        if path:
            return jsonify({'success': True, 'message': '已选择', 'data': {'path': path}})
    return jsonify({'success': False, 'message': '未选择文件', 'data': None})


@app.route('/api/pick-folder')
def api_pick_folder():
    """使用 zenity 选择本地文件夹，返回完整路径"""
    if not shutil.which('zenity'):
        return jsonify({'success': False, 'message': '未找到 zenity，无法打开文件夹选择器', 'data': None})

    title = request.args.get('title', '选择文件夹')
    default = request.args.get('default', os.path.expanduser('~'))

    cmd = [
        'zenity', '--file-selection',
        f'--title={title}',
        '--directory',
        f'--filename={default}'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        path = result.stdout.strip()
        if path:
            return jsonify({'success': True, 'message': '已选择', 'data': {'path': path}})
    return jsonify({'success': False, 'message': '未选择文件夹', 'data': None})


@app.route('/api/pick-icon')
def api_pick_icon():
    """使用 zenity 选择图标文件，返回完整路径（参考旧版实现）"""
    if not shutil.which('zenity'):
        return jsonify({'success': False, 'message': '未找到 zenity，无法打开图标选择器', 'data': None})
    
    cmd = [
        'zenity', '--file-selection',
        '--title=选择图标文件',
        '--file-filter=图标文件 (*.svg *.png *.xpm *.ico)|*.svg *.png *.xpm *.ico',
        '--filename=/usr/share/icons/hicolor/scalable/apps/'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        path = result.stdout.strip()
        if path:
            return jsonify({'success': True, 'message': '已选择', 'data': {'path': path}})
    return jsonify({'success': False, 'message': '未选择图标', 'data': None})


# ========== 原有的文件浏览 API (保留以防其他地方使用) ==========
@app.route('/api/file-browse')
def file_browse():
    """文件选择 API（简易实现，返回常用目录列表）"""
    file_type = request.args.get('type', 'all')
    paths = []
    
    home = get_real_home()
    common_dirs = [
        home, os.path.join(home, 'Desktop'), os.path.join(home, 'Documents'),
        os.path.join(home, 'Downloads'), os.path.join(home, 'Pictures'),
        '/usr/bin', '/usr/local/bin', '/opt',
        os.path.join(home, '.local/share/apps'),
        os.path.join(home, '.local/share/applications'),
    ]
    
    for d in common_dirs:
        if os.path.isdir(d):
            try:
                for f in os.listdir(d)[:20]:
                    fp = os.path.join(d, f)
                    if os.path.isfile(fp):
                        paths.append({
                            "name": f,
                            "path": fp,
                            "size": os.path.getsize(fp)
                        })
                    elif os.path.isdir(fp):
                        paths.append({
                            "name": f + "/",
                            "path": fp,
                            "size": 0
                        })
            except PermissionError:
                pass
    
    return jsonify(paths)


@app.route('/api/icon-browse')
def icon_browse():
    """图标选择 API"""
    icons = []
    icon_dirs = [
        '/usr/share/icons/hicolor/scalable/apps',
        '/usr/share/icons',
        os.path.join(get_real_home(), '.local/share/icons/hicolor/scalable/apps'),
    ]
    
    for d in icon_dirs:
        if os.path.isdir(d):
            for root, dirs, files in os.walk(d):
                for f in files:
                    if f.endswith(('.svg', '.png', '.xpm')):
                        fp = os.path.join(root, f)
                        name = os.path.splitext(f)[0]
                        icons.append({"name": name, "path": fp})
    
    # 去重并限制数量
    seen = set()
    unique = []
    for icon in icons:
        if icon['name'] not in seen:
            seen.add(icon['name'])
            unique.append(icon)
    
    return jsonify(unique[:100])


@app.route('/')
def index():
    """主页"""
    return render_template('index.html', 
                          app_name=APP_NAME, 
                          app_version=APP_VERSION,
                          update_log=UPDATE_LOG)


@app.route('/api/tabs')
def get_tabs():
    """获取标签页配置"""
    tabs = [
        {"id": "system", "name": "系统安全", "icon": "shield-lock"},
        {"id": "apps", "name": "软件组件", "icon": "grid"},
        {"id": "stores", "name": "应用商店", "icon": "shop"},
        {"id": "themes", "name": "美化定制", "icon": "palette"},
        {"id": "desktop", "name": "桌面与菜单", "icon": "display"},
        {"id": "services", "name": "服务与软件包", "icon": "gear"},
        {"id": "about", "name": "关于", "icon": "info-circle"},
    ]
    return jsonify(tabs)


@app.route('/api/logs')
def stream_logs():
    """SSE 日志流"""
    client_id = get_client_id()
    
    def event_stream():
        q = queue.Queue()
        with log_lock:
            log_queues[client_id] = q
        
        # 发送初始历史日志（最近50条）
        history = log_capture.messages[-50:] if log_capture.messages else []
        for msg in history:
            if msg.strip():
                yield f"data: {msg.strip()}\n\n"
        
        try:
            while True:
                msg = q.get()
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            pass
        finally:
            with log_lock:
                log_queues.pop(client_id, None)
    
    return Response(stream_with_context(event_stream()), 
                    mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/action', methods=['POST'])
def handle_action():
    """统一动作处理接口"""
    data = request.json or {}
    action = data.get('action', '')
    params = data.get('params', {})
    
    result = {"success": False, "message": "", "data": None}
    
    try:
        # ==================== 系统安全 ====================
        if action == 'lock_kernel':
            ok = lock_kernel()
            result = {"success": ok, "message": "内核锁定成功" if ok else "内核锁定失败"}
        
        elif action == 'unlock_kernel':
            ok = unlock_kernel()
            result = {"success": ok, "message": "内核解锁成功" if ok else "内核解锁失败"}
        
        elif action == 'update_package_list':
            ok = update_package_list()
            result = {"success": ok, "message": "软件源列表已更新" if ok else "更新失败"}
        
        elif action == 'set_apt_source':
            source = params.get('source', '')
            ok = set_apt_source(source)
            result = {"success": ok, "message": f"已切换到{source}源" if ok else "切换源失败"}
        
        # ==================== 软件组件 ====================
        elif action == 'set_exe_handler':
            result = set_exe_handler()
        
        elif action == 'set_exe_handler_with_wine':
            wine_type = params.get('wine_type', 'deepin')
            ok = set_exe_handler_with_wine(wine_type)
            result = {"success": ok, "message": "Wine 安装成功" if ok else "安装失败"}
        
        elif action == 'set_apk_handler':
            ok = set_apk_handler()
            result = {"success": ok, "message": "APK 默认打开方式已设置" if ok else "设置失败"}
        
        elif action == 'install_tree_fm':
            fm_type = params.get('fm_type', 'thunar')
            ok = install_tree_file_manager(fm_type)
            result = {"success": ok, "message": f"{fm_type} 文件管理器安装成功" if ok else "安装失败"}
        
        elif action == 'set_default_fm':
            fm_type = params.get('fm_type', 'thunar')
            ok = set_default_file_manager(fm_type)
            result = {"success": ok, "message": f"{fm_type} 已设为默认文件管理器" if ok else "设置失败"}
        
        elif action == 'restore_default_fm':
            ok = restore_default_file_manager()
            result = {"success": ok, "message": "已还原默认文件管理器" if ok else "还原失败"}
        
        elif action == 'set_wine_c':
            ok = set_wine_c()
            result = {"success": ok, "message": "Wine C 盘挂载成功" if ok else "挂载失败"}
        
        elif action == 'unset_wine_c':
            ok = unset_wine_c()
            result = {"success": ok, "message": "Wine C 盘已卸载" if ok else "卸载失败"}
        
        elif action == 'set_win_disk':
            ok = set_win_disk()
            result = {"success": ok, "message": "Windows 风格磁盘挂载成功" if ok else "挂载失败"}
        
        elif action == 'unset_win_disk':
            ok = unset_win_disk()
            result = {"success": ok, "message": "Windows 风格磁盘已卸载" if ok else "卸载失败"}
        
        elif action == 'install_shared_input':
            ok = install_shared_input()
            result = {"success": ok, "message": "Barrier 安装成功" if ok else "安装失败"}
        
        elif action == 'install_multi_screen':
            ok = install_multi_screen_app()
            result = {"success": ok, "message": "已打开 SpaceDesk APK" if ok else "操作失败"}
        
        elif action == 'install_steam':
            def steam_progress(downloaded, total, percent):
                broadcast_log(f"下载进度: {format_size(downloaded)} / {format_size(total)} ({percent:.2f}%)")
            
            ok = install_steam(progress_callback=steam_progress)
            result = {"success": ok, "message": "Steam 安装成功" if ok else "Steam 安装失败"}
        
        # ==================== 应用商店 ====================
        elif action == 'install_spark_store':
            ok = install_spark_store()
            result = {"success": ok, "message": "星火应用商店安装成功" if ok else "安装失败"}
        
        elif action == 'set_pip_source':
            ok = set_pip_source()
            result = {"success": ok, "message": "PIP 源已切换为清华源" if ok else "切换失败"}
        
        elif action == 'add_flat_store':
            ok = add_flat_store_icon()
            result = {"success": ok, "message": "Flatpak 商店图标已添加" if ok else "添加失败"}
        
        elif action == 'add_appimage_store':
            ok = add_appimage_store_icon()
            result = {"success": ok, "message": "AppImage 商店图标已添加" if ok else "添加失败"}
        
        # ==================== 美化定制 ====================
        elif action == 'install_win_theme':
            ok = install_win_theme()
            result = {"success": ok, "message": "Windows 主题安装成功" if ok else "安装失败", "logout_required": ok}
        
        elif action == 'install_win_fonts':
            ok = install_win_fonts()
            result = {"success": ok, "message": "Windows 字体安装成功" if ok else "安装失败", "logout_required": ok}
        
        elif action == 'install_brightness':
            ok = install_mask_brightness()
            result = {"success": ok, "message": "亮度调节工具安装成功" if ok else "安装失败"}
        
        elif action == 'set_brightness':
            brightness = params.get('brightness', 65)
            from models.system import set_brightness as sb
            ok = sb(brightness)
            result = {"success": ok, "message": f"亮度已设置为 {brightness}%" if ok else "设置失败"}
        
        # ==================== 桌面与菜单 ====================
        elif action == 'create_shortcut':
            ok, msg = create_shortcut(params)
            result = {"success": ok, "message": msg}
        
        elif action == 'create_context_menu':
            ok, msg = create_context_menu(params)
            result = {"success": ok, "message": msg}
        
        elif action == 'manage_app_icons':
            location = params.get('location', 'desktop')
            path = get_desktop_dir() if location == 'desktop' else os.path.join(get_real_home(), '.local/share/applications')
            subprocess.Popen(['xdg-open', path])
            result = {"success": True, "message": f"已打开: {path}"}
        
        elif action == 'manage_sys_icons':
            subprocess.Popen(['xdg-open', '/usr/share/applications'])
            result = {"success": True, "message": "已打开系统图标目录"}
        
        elif action == 'manage_context_menus':
            subprocess.Popen(['xdg-open', os.path.join(get_real_home(), '.local/share/file-manager/actions')])
            result = {"success": True, "message": "已打开右键菜单目录"}
        
        elif action == 'list_shortcuts':
            shortcuts = get_installed_shortcuts()
            result = {"success": True, "data": shortcuts}
        
        # ==================== 服务与软件包 ====================
        elif action == 'create_service':
            ok, msg = create_service(params)
            result = {"success": ok, "message": msg}
        
        elif action == 'start_service':
            name = params.get('name', '')
            ok, msg = start_service(name)
            result = {"success": ok, "message": msg}
        
        elif action == 'edit_service':
            name = params.get('name', '')
            ok, msg = edit_service_file(name)
            result = {"success": ok, "message": msg}
        
        elif action == 'read_log':
            name = params.get('name', '')
            ok, msg = read_service_log(name)
            result = {"success": ok, "message": msg}
        
        elif action == 'manage_services':
            ok, msg = manage_services()
            result = {"success": ok, "message": msg}
        
        elif action == 'set_android_style':
            subprocess.Popen(['xdg-open', '/usr/share/uengine/appetc/'])
            result = {"success": True, "message": "已打开目录"}
        
        elif action == 'install_package':
            ok = install_package(params)
            result = {"success": ok, "message": "安装成功" if ok else "安装失败"}
        
        elif action == 'uninstall_package':
            ok = uninstall_package(params)
            result = {"success": ok, "message": "卸载成功" if ok else "卸载失败"}
        
        elif action == 'get_package_info':
            info = get_package_info(params)
            result = {"success": True, "data": info}
        
        elif action == 'add_desktop_icon':
            ok = add_uosbetter_desktop_icon()
            result = {"success": ok, "message": "桌面图标已创建" if ok else "创建失败"}
        
        elif action == 'set_android_style':
            subprocess.Popen(['xdg-open', '/usr/share/uengine/appetc/'])
            result = {"success": True, "message": "已打开目录"}
        
        elif action == 'get_running_services':
            services = get_running_services()
            result = {"success": True, "data": services}
        
        elif action == 'logout_user':
            # 发送注销命令
            try:
                # 尝试使用 systemctl 或 loginctl 注销当前用户
                subprocess.Popen(['loginctl', 'terminate-user', os.getenv('USER', '')])
                result = {"success": True, "message": "正在注销..."}
            except Exception as e:
                result = {"success": False, "message": f"注销失败: {str(e)}"}

        else:
            result = {"success": False, "message": f"未知动作: {action}"}
    
    except Exception as e:
        result = {"success": False, "message": f"执行出错: {str(e)}"}
        broadcast_log(f"✗ 执行出错: {str(e)}")
    
    return jsonify(result)


# 启动浏览器
def open_browser():
    subprocess.Popen(['xdg-open', 'http://127.0.0.1:55000'])


if __name__ == '__main__':
    # 确保必要目录存在
    ensure_dirs()
    
    print(f"已启动 {APP_NAME} {APP_VERSION}，端口号: 55000")
    # print(f"请在浏览器中访问: http://127.0.0.1:55000")
    
    # 拉起线程，3秒后启动浏览器
    threading.Timer(3.0, open_browser).start()
    
    # 启动 Flask
    app.run(host='127.0.0.1', port=55000, debug=True, threaded=True)