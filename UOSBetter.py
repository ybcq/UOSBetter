import os
import subprocess
import shutil

try:
    import models.PySimpleGUI as sg
except ModuleNotFoundError:
    print("请先安装PySimpleGUI库，正在安装中...")
    print("如果安装失败，请手动安装：'pip install pysimplegui-4-foss'")
    subprocess.run(["pip", "install", "pysimplegui-4-foss"])
    import models.PySimpleGUI as sg

# 导入GetRelease模块
from models.GetRelease import download_file_with_progress, format_size

# 导入安装模块
from models.InstallYPK import install_ypk, install_ypk_safe, uninstall_ypk, uninstall_ypk_safe
from models.InstallTAR import install_tar_archive

# 如果不是Windows，则加载这两个库
if os.name != 'nt':
    import pwd
    import grp

APP_NAME = 'UOS系统优化大师'
APP_VERSION = '1.2.0'
UPDATE_LOG = """
修复了创建的图标启动目录为桌面的问题
主题中增加了压缩包和NEMO的图标
修改复制操作的原文件为绝对地址

V1.1.0
增加了TAR等格式的绿色软件的安装卸载功能
Steam改为在线获取，大幅缩小软件体积

V1.0.0
部分功能支持Debian系的其他系统
比如Ubuntu，GXDE，AnduinOS，Raspbian等
"""

# 设置主题
sg.theme('DarkGray')
sg.SetOptions(font=('Microsoft YaHei', 10))

# 第一标签页：安全与组件
tab1_layout = [
    [sg.Frame('安全', [
        [sg.Button('锁定内核版本', key='-LOCK_KERNEL-'), sg.Button('解锁内核版本', key='-UNLOCK_KERNEL-')],
        [sg.Text('锁定后防止失误替换内核库版本，但可能无法更新显卡驱动')],
        [sg.Button('更新应用版本列表', key='-UPDATE_PACKAGE_LIST-')],
        # [sg.Button('解锁双系统时NTFS硬盘读写限制', key='-UNLOCK_DISK-')]
    ], expand_x=True, expand_y=True),
    
    sg.Frame('组件', [
        [sg.Button('双击打开.exe文件', key='-SET_EXE_HANDLER-'),
         sg.Button('双击安装.apk文件', key='-SET_APK_HANDLER-')],
        [sg.Button('安装有目录树的文件管理器', key='-INSTALL_TREE_FM-'),
         sg.Button('替换为默认文件管理器', key='-SET_DEFAULT_FM-'),
         sg.Button('还原', key='-RESTORE_DEFAULT_FM-')],
        [sg.Button('安装副屏App', key='-INSTALL_MULTI_SCREEN-'),
         sg.Button('安装多台电脑用同一套键鼠操控', key='-INSTALL_SHARED_INPUT-')],
        [sg.Button('安装Steam便携版', key='-INSTALL_STEAM-'), sg.Text('可解决UOS安装Steam各种缺库弹窗，需联网')]
    ], expand_x=True, expand_y=True)],
    
    [sg.Frame('应用商店', [
        [sg.Button('安装星火应用商店', key='-INSTALL_SPARK_STORE-'),
         sg.Button('替换PIP为清华源', key='-SET_PIP_SOURCE-')],
        [sg.Button('添加Flat应用商店图标', key='-ADD_FLAT_STORE-'), sg.Button('安装AppImage应用商店', key='-ADD_APPIMAGE_STORE-'),
         sg.Text('使用便携版应用更安全')],
    ], expand_x=True, expand_y=True),
    
    sg.Frame('美化', [
        [sg.Button('安装Windows主题', key='-INSTALL_WIN_THEME-'),
         sg.Button('安装Windows字体', key='-INSTALL_WIN_FONTS-')],
        [sg.Button('安装遮罩亮度调节', key='-INSTALL_BRIGHTNESS-')],
    ], expand_x=True, expand_y=True)],
    
    # [sg.Frame('其他常用', [
        
    # ], expand_x=True), expand_y=True]
]

# 第二标签页布局
tab2_layout = [
    [sg.Frame('快捷方式', [
        [sg.Text("图标名称:"), sg.Input(key="-SC_NAME-", size=(30, 1))],
        [sg.Text("选择程序:"), sg.Input(key="-SC_EXEC-", size=(30, 1)), 
        sg.FileBrowse(button_text="浏览", target="-SC_EXEC-")],
        [sg.Text("软件图标:"), sg.Input(key="-SC_ICON-", size=(30, 1)), 
        sg.Button("浏览", key="-SC_ICON_BT-")],
        [sg.Text("启动参数:"), sg.Input(default_text="%U", key="-SC_ARGS-", size=(30, 1))],
        [sg.Checkbox("以管理员权限运行", key="-SC_SUDO-")],
        [sg.Text("目标位置:"),
        sg.Radio("桌面", "SC_LOCATION", default=True, key="-SC_DESKTOP-"),
        sg.Radio("应用程序菜单", "SC_LOCATION", key="-SC_APPLIST-")],
        [sg.Button("创建", key="-CREATE_ICON-"), sg.Button("管理应用图标", key="-MANAGE_APP_ICON-"), sg.Button("管理应用图标(系统)", key="-MANAGE_SYS_ICON-")]
    ], expand_x=True, expand_y=True),
    sg.Frame('右键菜单', [
        [sg.Text("菜单名称:"), sg.Input(key="-CM_NAME-", size=(30, 1))],
        [sg.Text("执行命令:"), sg.Input(key="-CM_COMMAND-", size=(30, 1)), 
        sg.FileBrowse(button_text="浏览", target="-CM_COMMAND-")],
        [sg.Text("图标路径:"), sg.Input(key="-CM_ICON-", size=(30, 1)), 
        sg.Button("浏览", key="-CM_ICON_BT-")],
        [sg.Text("菜单类型:"),
        sg.Radio("文件菜单", "CM_TYPE", default=True, key="-CM_FILE-"),
        sg.Radio("文件夹/背景菜单", "CM_TYPE", key="-CM_DIR-")],
        [sg.Text("目标位置:"),
        sg.Radio("仅当前用户", "CM_LOCATION", default=True, key="-CM_USER-"),
        sg.Radio("所有用户", "CM_LOCATION", key="-CM_SYSTEM-")],
        [sg.Button("创建", key="-CREATE_MENU-"), sg.Button("管理右键菜单", key="-MANAGE_CONTEXT_MENU-")]
    ], expand_x=True, expand_y=True)],
    
]

# 第三个标签页布局
tab3_layout = [
    [
        # 左侧大框
        sg.Frame('开机启动', [
            [sg.Text("服务名称:"), sg.Input(key="-SV_NAME-", size=(30, 1))],
            [sg.Text("执行命令:"), sg.Input(key="-SV_COMMAND-", size=(30, 1)),
             sg.FileBrowse(button_text="浏览", target="-SV_COMMAND-")],
            [sg.Text("重启间隔:"), sg.Input(default_text="0", key="-SV_RESTART-", size=(30, 1))],
            [sg.Button("创建", key="-CREATE_SERVICE-")],
            [sg.Button("手动编辑文件", key="-EDIT_SERVICE_FILE-"),
             sg.Button("手动启动服务", key="-START_SERVICE-"),
             sg.Button("读取日志", key="-READ_LOG-")],
            [sg.Button("管理开机启动", key="-MANAGE_SERVICE-")]
        ], expand_x=True, expand_y=True, size=(None, None)),
        
        # 右侧上下两个框
        sg.Column([
            # 上框
            [sg.Frame('便捷安装', [
                [sg.Text("支持YPK、TAR、TAR.GZ、TAR.BZ2格式安装")],
                [sg.Text("安装路径:"), sg.Input(key="-YPK_PATH-", size=(30, 1)), 
                 sg.FileBrowse(button_text="浏览", target="-YPK_PATH-")],
                [sg.Checkbox("隔离模式", key="-YPK_ISOLATE-", default=True)], 
                [sg.Button("安装", key="-INSTALL_YPK-"), sg.Button("卸载", key="-UNINSTALL_YPK-")]
            ], expand_x=True, expand_y=True)],
            
            # 下框
            [sg.Frame('其他功能', [
                [sg.Button("设置安卓应用打开样式", key="-SET_ANDROID_APP_STYLE-")],
                [sg.Text("其他尚在开发中...")],
            ], expand_x=True, expand_y=True)]
        ], expand_x=True, expand_y=True, vertical_alignment='top')
    ]
]

# 主窗口布局
layout = [
    # [sg.Text('UOS系统优化大师', font=('Arial', 16), justification='center', expand_x=True)],
    [sg.TabGroup([
        [sg.Tab('安全优化与组件', tab1_layout)],
        [sg.Tab('桌面与菜单', tab2_layout)],
        [sg.Tab('系统级自启服务', tab3_layout)]
    ], expand_x=True, expand_y=True)],
    [sg.Multiline(size=(100, 10), background_color='black', text_color='white', 
                  autoscroll=True, key='-LOG-', disabled=True, expand_x=True)],
    [sg.Button('关于', key='-ABOUT-'), sg.Button('添加UOS优化大师桌面图标', key='-ADD_DESKTOP_ICON-'),
     sg.Text('', expand_x=True),
     sg.Text('遮罩调节亮度'),
     sg.Slider(range=(30, 100), orientation='h', key='-BRIGHTNESS-', enable_events=True, default_value=65),
     sg.Button('设置', key='-SET_BRIGHTNESS-')
    ]
]

# 执行命令并实时显示输出
def execute_command(command):
    # 执行Linux命令并实时显示输出到日志窗口# 
    window['-LOG-'].print(f"执行命令: {command}")
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时读取输出
        for line in process.stdout:
            window['-LOG-'].print(line.strip())
            window.refresh()
        
        process.wait()
        if process.returncode == 0:
            window['-LOG-'].print("✓ 命令执行成功")
        else:
            window['-LOG-'].print(f"✗ 命令执行失败 (错误代码: {process.returncode})")
        
    except Exception as e:
        window['-LOG-'].print(f"执行命令出错: {str(e)}")

# 获取真正用户的home目录（解决sudo下~展开为/root的问题）
def get_real_home():
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        try:
            return pwd.getpwnam(sudo_user).pw_dir
        except KeyError:
            pass
    return os.path.expanduser('~')

# 获取桌面目录路径（支持中文"桌面"和英文"Desktop"）
def get_desktop_dir():
    home = get_real_home()
    desktop_cn = os.path.join(home, "桌面")
    desktop_en = os.path.join(home, "Desktop")
    
    # 优先使用存在的目录
    if os.path.exists(desktop_cn):
        return desktop_cn
    elif os.path.exists(desktop_en):
        return desktop_en
    else:
        # 如果都不存在，默认使用Desktop
        return desktop_en

# 创建目录$HOME/.local/share/apps/
os.makedirs(get_real_home() + '/.local/share/apps/', exist_ok=True)

# ====================== 安全与组件 ======================
# 锁定内核版本
def lock_kernel():
    window['-LOG-'].print('执行: 锁定内核版本')
    execute_command("apt-mark hold linux-image-* linux-headers-*")
    # 实际功能代码

# 解锁内核版本
def unlock_kernel():
    window['-LOG-'].print('执行: 解锁内核版本')
    execute_command("apt-mark unhold linux-image-* linux-headers-*")

# 更新软件版本列表
def update_package_list():
    window['-LOG-'].print('执行: 更新软件版本列表')
    execute_command("apt update")

# 解锁双系统硬盘读写限制
def unlock_disk_restriction():
    window['-LOG-'].print('执行: 解锁双系统硬盘读写限制')
    # chmod +x 
    execute_command("chmod +x data/scripts/UnlockDisk.sh")
    # 执行unlock_disk.sh脚本
    execute_command("bash data/scripts/UnlockDisk.sh")

# 设置双击打开.exe文件
def set_exe_handler():
    window['-LOG-'].print('执行: 设置双击打开.exe文件')
    # chmod +x
    execute_command("chmod +x data/scripts/Deepin-Wine.sh")
    # 执行install_wine.sh脚本
    execute_command("bash data/scripts/Deepin-Wine.sh")
    # 弹窗提示用户：找一个exe文件，右键，选择默认程序，找到Deepin-Wine，确定
    sg.popup("请找一个exe文件 -> 右键 -> 选择默认程序 -> 找到Deepin-Wine -> 确定", title="设置默认程序")

# 设置双击打开.apk文件
def set_apk_handler():
    window['-LOG-'].print('执行: 设置双击打开.apk文件')
    # 设计.apk的默认打开方式为UEngine
    execute_command("xdg-mime default uengine.desktop application/vnd.android.package-archive")

# 安装有目录树的文件管理器
def install_tree_file_manager():
    window['-LOG-'].print('执行: 安装有目录树的文件管理器')
    execute_command("apt install -y nemo")

# 替换nemo为默认文件管理器
def set_default_file_manager():
    window['-LOG-'].print('执行: 替换为默认文件管理器')
    execute_command("xdg-mime default nemo.desktop inode/directory")

# 还原默认文件管理器
def restore_default_file_manager():
    window['-LOG-'].print('执行: 还原默认文件管理器')
    execute_command("xdg-mime default dde-file-manager.desktop inode/directory")

# 安装星火应用商店
def install_spark_store():
    window['-LOG-'].print('执行: 安装星火应用商店')
    execute_command("apt install -y spark-store")

# 替换PIP为清华源
def set_pip_source():
    window['-LOG-'].print('执行: 替换PIP为清华源')
    execute_command("pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple")

# 添加Flat应用商店图标
def add_flat_store_icon():
    window['-LOG-'].print('执行: 添加Flat应用商店图标')
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    # 复制data/flatpak.desktop到用户本地applications/ 和 桌面
    script_dir = os.path.dirname(os.path.abspath(__file__))
    flatpak_desktop = os.path.join(script_dir, 'data', 'desktops', 'flatpak.desktop')
    execute_command(f"cp {flatpak_desktop} {home}/.local/share/applications/")
    execute_command(f"cp {flatpak_desktop} {desktop_dir}/")
    # chmod +x
    execute_command(f"chmod +x {home}/.local/share/applications/flatpak.desktop")
    execute_command(f"chmod +x {desktop_dir}/flatpak.desktop")

# 添加AppImage应用商店图标
def add_appimage_store_icon():
    window['-LOG-'].print('执行: 添加AppImage应用商店图标')
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    appimage_pool = os.path.join(script_dir, 'data', 'appImages', 'AppImagePool.AppImage')
    execute_command(f"cp {appimage_pool} {home}/.local/share/apps/")
    # chmod +x
    execute_command(f"chmod +x {home}/.local/share/apps/AppImagePool.AppImage")

    # 复制data/appimage.desktop到用户本地applications/ 和 桌面
    appimage_desktop = os.path.join(script_dir, 'data', 'desktops', 'appimage.desktop')
    execute_command(f"cp {appimage_desktop} {home}/.local/share/applications/")
    execute_command(f"cp {appimage_desktop} {desktop_dir}/")
    # chmod +x
    execute_command(f"chmod +x {home}/.local/share/applications/appimage.desktop")
    execute_command(f"chmod +x {desktop_dir}/appimage.desktop")

# 安装Windows主题
def install_win_theme():
    window['-LOG-'].print('执行: 安装Windows主题')
    # 使用绝对路径，避免从其他目录启动时找不到文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tar_path = os.path.join(script_dir, 'data', 'themes', 'win11theme.tar')
    target_dir = os.path.join(get_real_home(), '.local/share')
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    execute_command(f'tar -xvf "{tar_path}" -C "{target_dir}" 2>&1 | grep -v "SCHILY.fflags"')
    # 弹窗提示
    sg.Popup('请在控制中心 -> 个性化 -> 图标主题 选择 Light\n注销当前用户再登录生效', title='更换主题')

# 安装Windows字体
def install_win_fonts():
    window['-LOG-'].print('执行: 安装Windows字体')
    # 执行如下命令
    execute_command("apt install -y ttf-mscorefonts-installer")
    # 弹窗提示
    sg.Popup('请在控制中心 -> 个性化 -> 字体 -> 标准字体 选择 微软雅黑', title='更换字体')

# 安装遮罩亮度调节
def install_mask_brightness():
    window['-LOG-'].print('执行: 安装遮罩亮度调节')
    # 执行如下命令
    execute_command("apt install -y brightnessctl")
    # 弹窗提示
    sg.Popup('安装已完成，可通过右下方滚动条调节', title='遮罩亮度调节')

# 安装副屏App
def install_multi_screen_app():
    window['-LOG-'].print('执行: 安装副屏App')
    # 用系统默认方式打开SpaceDesk.apk
    execute_command("xdg-open data/apks/SpaceDesk.apk")

# 安装多电脑共享键鼠
def install_shared_input():
    window['-LOG-'].print('执行: 安装多电脑共享键鼠')
    # 安装Barrier
    execute_command("apt install -y barrier")
    # 打开Barrier配置界面
    execute_command("barrier")


def download_steam_appimage(output_path, progress_callback=None):
    """
    下载Steam AppImage最新版本
    
    Args:
        output_path: 输出文件路径
        progress_callback: 进度回调函数
        
    Returns:
        bool: 下载是否成功
    """
    # GitHub Steam AppImage 下载链接
    steam_url = "https://github.com/ivan-hc/Steam-appimage/releases/download/1.0.0.85-6%402026-05-01_1777622844/Steam-1.0.0.85-6-anylinux-x86_64.AppImage"
    
    return download_file_with_progress(steam_url, output_path, progress_callback=progress_callback)

# 安装Steam虚拟环境版
def install_steam():
    window['-LOG-'].print('执行: 安装Steam虚拟环境版')
    home = get_real_home()
    desktop_dir = get_desktop_dir()
    
    # 设置下载进度回调函数
    def steam_download_progress(downloaded, total, percent):
        downloaded_str = format_size(downloaded)
        total_str = format_size(total)
        window['-LOG-'].print(f'下载进度: {downloaded_str} / {total_str} ({percent:.2f}%)')
        window.refresh()
    
    # 下载Steam AppImage
    steam_target = f"{home}/.local/share/apps/Steam.AppImage"
    window['-LOG-'].print('开始从GitHub下载Steam AppImage...')
    
    success = download_steam_appimage(steam_target, progress_callback=steam_download_progress)
    
    if not success:
        window['-LOG-'].print('✗ Steam.AppImage下载失败')
        sg.popup_error('Steam AppImage下载失败！请检查网络连接。', title='错误')
        return
    
    window['-LOG-'].print('✓ Steam.AppImage下载成功')
    
    # chmod +x
    steam_path = f"{home}/.local/share/apps/Steam.AppImage"
    execute_command(f"chmod +x {steam_path}")

    # 为它创建桌面图标和开始菜单图标
    script_dir = os.path.dirname(os.path.abspath(__file__))
    steam_desktop = os.path.join(script_dir, 'data', 'desktops', 'steam.desktop')
    execute_command(f"cp {steam_desktop} {home}/.local/share/applications/")
    execute_command(f"cp {steam_desktop} {desktop_dir}/")

# 设置亮度按钮
def set_brightness():
    window['-LOG-'].print('执行: 设置亮度按钮')
    # 执行如下命令
    brightness = values['-BRIGHTNESS-']
    execute_command(f"brightnessctl set {brightness}%")

# 添加UOS优化大师桌面图标
def add_uosbetter_desktop_icon():
    window['-LOG-'].print('执行: 添加UOS优化大师桌面图标')
    
    # 获取当前脚本的绝对路径
    script_path = os.path.abspath(__file__)
    
    # 准备图标路径（使用系统默认图标或自定义图标）
    # 这里使用一个通用的应用图标
    icon_name = "preferences-system"
    
    # 构造.desktop内容
    desktop_content = f"""[Desktop Entry]
Name=UOS系统优化大师
Exec=sudo -E python3 {script_path}
Path={os.path.dirname(script_path)}
Icon={icon_name}
Terminal=true
Type=Application
Categories=Utility;System;
"""
    
    # 确定保存位置（桌面和开始菜单）
    desktop_path = os.path.join(get_desktop_dir(), "UOS系统优化大师.desktop")
    home = get_real_home()
    app_menu_path = os.path.join(home, ".local/share/applications/UOS系统优化大师.desktop")

    # 删除原有图标
    if os.path.exists(desktop_path):
        os.remove(desktop_path)
    if os.path.exists(app_menu_path):
        os.remove(app_menu_path)
    
    try:
        # 创建桌面图标
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        os.chmod(desktop_path, 0o755)
        window['-LOG-'].print(f"✓ 桌面图标已创建: {desktop_path}")
        
        # 创建开始菜单图标
        os.makedirs(os.path.dirname(app_menu_path), exist_ok=True)
        with open(app_menu_path, "w") as f:
            f.write(desktop_content)
        os.chmod(app_menu_path, 0o755)
        window['-LOG-'].print(f"✓ 开始菜单图标已创建: {app_menu_path}")
        
        sg.popup_ok("UOS优化大师图标 桌面和开始菜单已创建成功！", title="成功")
    except Exception as e:
        window['-LOG-'].print(f"✗ 图标创建失败: {str(e)}")
        sg.popup_error(f"UOS优化大师图标 创建失败: {str(e)}", title="错误")

# ------------------------ 服务与菜单 ------------------------
# 替换环境变量中的特殊字符，如~
def environment_substitute(value):
    if value and value.startswith("~"):
        return value.replace("~", get_real_home(), 1)
    return value

# 调用 zenity 文件选择对话框
def choose_file():
    cmd = [
        'zenity', '--file-selection',
        '--title=选择文件',          # 自定义标题
        '--file-filter=图标文件 (*.svg)|*.svg',  # 文件类型过滤
        '--filename=/usr/share/icons/hicolor/scalable/apps/'
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    if result.returncode == 0:
        file_path = result.stdout.strip()
        print("已选择文件:", file_path)
        return file_path
    else:
        print("取消选择")
        return None

# 处理系统图标选择
def handle_system_icon_selection(icon_path):
    # 系统图标目录
    system_icon_dir = "/usr/share/icons/hicolor/scalable/apps"
    
    if not icon_path:
        return  # 用户取消选择
    
    # 获取纯文件名（不含路径）
    icon_filename = os.path.basename(icon_path)
    # 移除扩展名
    icon_name = os.path.splitext(icon_filename)[0]
    
    # 目标图标目录（用户本地目录）
    local_icon_dir = os.path.join(get_real_home(), ".local/share/icons/hicolor/scalable/apps")
    
    # 如果不在系统目录，则复制到用户目录
    if not icon_path.startswith(system_icon_dir):
        try:
            os.makedirs(local_icon_dir, exist_ok=True)
            shutil.copy2(icon_path, os.path.join(local_icon_dir, icon_filename))
            # sg.popup_notify(f"图标已复制到本地目录: {local_icon_dir}")
            window['-LOG-'].print(f"图标已复制到本地目录: {local_icon_dir}")
        except Exception as e:
            sg.popup_error(f"复制图标失败: {str(e)}")
            return
    
    # 更新界面
    return icon_name

# 创建桌面快捷方式# 
def create_shortcut(values):
    name = values["-SC_NAME-"]
    exec_path = environment_substitute(values["-SC_EXEC-"])
    icon_path = values["-SC_ICON-"]
    icon_name = handle_system_icon_selection(icon_path) 
    sudo = values["-SC_SUDO-"]
    args = values["-SC_ARGS-"]
    
    if not name or not exec_path:
        sg.popup_error("名称和程序不能为空！", title="错误")
        return False

    # 处理Windows程序
    if exec_path.lower().endswith(".exe"):
        exec_prefix = "deepin-wine"
        exec_path = exec_path.replace("\\", "/")
    # 处理Python脚本
    elif exec_path.lower().endswith(".py"):
        exec_prefix = "python3"
    # 处理其他程序
    else:
        exec_prefix = ""
    
    if sudo:
        exec_prefix = "" + exec_prefix
    
    # 处理路径中的空格
    if " " in exec_path:
        exec_path = f'"{exec_path}"'

    # 构造.desktop内容
    desktop_content = f"""[Desktop Entry]
Name={name}
Exec={exec_prefix} {exec_path} {args}
Path={os.path.dirname(exec_path)}
Icon={icon_name}
Terminal=false
Type=Application
Categories=Utility;
"""

    # 确定保存位置
    if values["-SC_DESKTOP-"]:
        desktop_path = os.path.join(get_desktop_dir(), f"{name}.desktop")
    else:
        home = get_real_home()
        app_dir = os.path.join(home, ".local/share/applications")
        os.makedirs(app_dir, exist_ok=True)
        desktop_path = os.path.join(app_dir, f"{name}.desktop")
    
    try:
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        
        # subprocess.run(["chmod", "+x", desktop_path])
        # execute_command(f"chmod +x {desktop_path}")
        os.chmod(desktop_path, 0o755)
        
        return True, f"快捷方式已创建: {desktop_path}"
    except Exception as e:
        return False, f"创建快捷方式失败: {str(e)}"

# 创建右键菜单项
def create_context_menu(values):
    name = values["-CM_NAME-"]
    command = values["-CM_COMMAND-"]
    menu_type = "file" if values["-CM_FILE-"] else "directory"
    user_only = values["-CM_USER-"]
    icon_path = values["-CM_ICON-"]
    icon_name = handle_system_icon_selection(icon_path) 
    
    if not name or not command:
        sg.popup_error("名称和命令不能为空！", title="错误")
        return False

    # 确定目标目录
    if user_only:
        target_dir = os.path.join(get_real_home(), ".local/share/file-manager/actions")
    else:
        target_dir = "/usr/share/file-manager/actions"
        if os.geteuid() != 0:
            return False, "需要管理员权限！请使用SUDO前缀运行此程序。"

    # 创建目标目录
    os.makedirs(target_dir, exist_ok=True)

    # 生成文件名
    desktop_filename = name.lower().replace(" ", "-") + ".desktop"
    desktop_path = os.path.join(target_dir, desktop_filename)

    # 设置MimeTypes
    if menu_type == "file":
        mime_types = "text/plain;application/*;"
    else:
        mime_types = "inode/directory;"

    # 构造.desktop内容
    desktop_content = f"""[Desktop Entry]
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
        with open(desktop_path, "w") as f:
            f.write(desktop_content)
        
        # 刷新文件管理器
        execute_command(f"nautilus -q")
        execute_command(f"nautilus")
        
        return True, f"右键菜单项已创建: {desktop_path}"
    except Exception as e:
        return False, f"创建右键菜单失败: {str(e)}"

# 创建系统服务
def create_service(values): 
    service_name = values["-SV_NAME-"]
    command = values["-SV_COMMAND-"]
    restart_interval = values["-SV_RESTART-"] or "5"  # 默认5秒
    
    if not service_name or not command:
        return False, "服务名称和执行命令不能为空"
    
    # 获取当前用户和组（非root用户）
    username = os.environ.get('SUDO_USER', os.getlogin())
    try:
        user_info = pwd.getpwnam(username)
        group_info = grp.getgrgid(user_info.pw_gid)
        user = user_info.pw_name
        group = group_info.gr_name
    except Exception:
        return False, "无法获取用户信息"
    
    # 获取工作目录（命令所在目录）
    working_directory = os.path.dirname(os.path.abspath(command))
    
    # 服务文件内容
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
    
    # 服务文件路径
    service_file = f"/etc/systemd/system/{service_name}.service"
    
    try:
        # 写入服务文件
        with open(service_file, "w") as f:
            f.write(service_content)
        
        # 设置文件权限
        os.chmod(service_file, 0o644)
        
        return True, f"服务已创建: {service_file}"
    except Exception as e:
        return False, f"创建服务失败: {str(e)}"

# 编辑服务文件
def edit_service_file(service_name):
    
    if not service_name:
        sg.popup_error("请先输入服务名称", title="错误")
        return False
    
    service_file = f"/etc/systemd/system/{service_name}.service"
    
    if not os.path.exists(service_file):
        sg.popup_error(f"服务文件不存在: {service_file}", title="错误")
        return False
    
    try:
        subprocess.run(["xdg-open", service_file], check=True)
        return True
    except Exception as e:
        sg.popup_error(f"打开编辑器失败: {str(e)}", title="错误")
        return False

def start_service(service_name):
   
    if not service_name:
        sg.popup_error("请先输入服务名称", title="错误")
        return False
    
    try:
        # 重新加载守护进程
        # subprocess.run(["systemctl", "daemon-reload"], check=True)
        execute_command("systemctl daemon-reload")
        
        # 启动服务
        # subprocess.run(["systemctl", "start", service_name], check=True)
        execute_command(f"systemctl start {service_name}")
        
        # 启用开机自启
        # subprocess.run(["systemctl", "enable", service_name], check=True)
        execute_command(f"systemctl enable {service_name}")
        
        window["-LOG-"].print(f"服务 {service_name} 已启动并设置为开机自启")
        # sg.popup_ok(f"服务 {service_name} 已启动并设置为开机自启", title="成功")
        return True
    except subprocess.CalledProcessError as e:
        sg.popup_error(f"启动服务失败: {str(e)}", title="错误")
        return False

# 读取服务日志
def read_service_log(service_name):
    if not service_name:
        sg.popup_error("请先输入服务名称", title="错误")
        return False
    
    try:
        # 在新终端中打开日志
        subprocess.Popen([
            "x-terminal-emulator", 
            "-e", 
            f"journalctl -u {service_name} -f"
        ])
        # execute_command("x-terminal-emulator -e journalctl -u {} -f")
        return True
    except Exception as e:
        sg.popup_error(f"打开 {service_name} 服务日志失败: {str(e)}", title="错误")
        return False

# 管理服务
def manage_services():
    try:
        # 在新终端中打开服务管理器
        subprocess.Popen(["x-terminal-emulator", "-e", "systemctl"])
        # execute_command("x-terminal-emulator -e systemctl")
        return True
    except Exception as e:
        sg.popup_error(f"打开服务管理器失败: {str(e)}", title="错误")
        return False

# 设置Android应用风格
def set_android_app_style():
    # 管理员身份打开/usr/share/uengine/appetc/
    subprocess.Popen(["xdg-open", "/usr/share/uengine/appetc/"])

# 安装YPK或TAR包
def install_package():
    package_path = values["-YPK_PATH-"]
    isolate_mode = values["-YPK_ISOLATE-"]
    
    if not package_path:
        sg.popup_error("请选择要安装的软件包！", title="错误")
        return False
    
    if not os.path.exists(package_path):
        sg.popup_error(f"文件不存在：{package_path}", title="错误")
        return False
    
    window['-LOG-'].print(f"开始安装：{package_path}")
    
    try:
        # 判断文件类型
        if package_path.lower().endswith('.ypk'):
            window['-LOG-'].print("检测到YPK格式软件包")
            
            if isolate_mode:
                window['-LOG-'].print("使用隔离模式（虚拟环境）安装")
                result = install_ypk_safe(package_path)
            else:
                window['-LOG-'].print("使用LOCAL模式安装")
                result = install_ypk(package_path)
                
        elif package_path.lower().endswith(('.tar', '.tar.gz', '.tar.bz2', '.tgz', '.tbz2')):
            window['-LOG-'].print("检测到TAR格式软件包")
            result = install_tar_archive(package_path)
        else:
            sg.popup_error("不支持的文件格式！\n支持的格式：YPK、TAR、TAR.GZ、TAR.BZ2", title="错误")
            return False
        
        if result:
            sg.popup_ok("安装成功！", title="成功")
            window['-LOG-'].print("✓ 安装成功")
        else:
            sg.popup_error("安装失败！请查看日志详细信息。", title="错误")
            window['-LOG-'].print("✗ 安装失败")
            
        return result
        
    except Exception as e:
        error_msg = f"安装过程出错：{str(e)}"
        window['-LOG-'].print(f"✗ {error_msg}")
        sg.popup_error(error_msg, title="错误")
        return False

# 卸载YPK包
def uninstall_package():
    package_path = values["-YPK_PATH-"]
    isolate_mode = values["-YPK_ISOLATE-"]
    
    if not package_path:
        sg.popup_error("请选择要卸载的软件包！", title="错误")
        return False
    
    if not os.path.exists(package_path):
        sg.popup_error(f"文件不存在：{package_path}", title="错误")
        return False
    
    # 确认卸载操作
    if not package_path.lower().endswith('.ypk'):
        sg.popup_error("仅支持YPK格式软件包的卸载！\nTAR格式软件包请手动删除。", title="错误")
        return False
    
    confirm = sg.popup_yes_no(f"确定要卸载软件包吗？\n{package_path}", title="确认卸载")
    if confirm != "Yes":
        return False
    
    window['-LOG-'].print(f"开始卸载：{package_path}")
    
    try:
        if isolate_mode:
            window['-LOG-'].print("使用隔离模式（虚拟环境）卸载")
            result = uninstall_ypk_safe(package_path)
        else:
            window['-LOG-'].print("使用LOCAL模式卸载")
            result = uninstall_ypk(package_path)
        
        if result:
            sg.popup_ok("卸载成功！", title="成功")
            window['-LOG-'].print("✓ 卸载成功")
        else:
            sg.popup_error("卸载失败！请查看日志详细信息。", title="错误")
            window['-LOG-'].print("✗ 卸载失败")
            
        return result
        
    except Exception as e:
        error_msg = f"卸载过程出错：{str(e)}"
        window['-LOG-'].print(f"✗ {error_msg}")
        sg.popup_error(error_msg, title="错误")
        return False
    # execute_command("xdg-open /usr/share/uengine/appetc/")

def show_about_window(APP_NAME, APP_VERSION, UPDATE_LOG):
    # 显示关于窗口
    layout = [
        [sg.Text(APP_NAME, justification='c', font="微软雅黑 16")],
        [sg.Text(f'软件版本：{APP_VERSION} ', justification='c')],
        [sg.Text("更新日志：", justification='c')],
        [sg.Multiline(UPDATE_LOG.strip(), size=(50, 10), disabled=True)],
        [sg.Text("作者: 御坂初琴")],
        # [sg.Text("功能: 用例拼合与检查工具")],
        [sg.Text("Copyright © 2025 御坂初琴软件屋. All Rights Reserved")],
        # [sg.Text("使用PySimpleGUI和openpyxl开发")],
        # [sg.Button("GitHub", key="-GITHUB-")],
        [sg.Button("关闭", key="-CLOSE-")]
    ]
    
    about_window = sg.Window("关于", layout, modal=True)
    
    while True:
        event, values = about_window.read()
        if event == "-GITHUB-":
            # webbrowser.open("https://github.com/yourusername/your-repo")
            pass
        elif event == "-CLOSE-" or event == sg.WIN_CLOSED:
            break
            
    about_window.close()

# 验证管理员权限
if os.name != 'nt':
    if os.geteuid() != 0:
        sg.popup("请用 'sudo python3 UOSBetter.py' 命令打开\n否则大部分功能受限", title="权限提示")

# 创建窗口
window = sg.Window(APP_NAME + ' ' + APP_VERSION, layout, resizable=False, finalize=True)

# 事件循环
while True:
    event, values = window.read()
   
    if event in (sg.WIN_CLOSED, "-EXIT-"):
        break

    # ====================== 安全与组件 ======================
    # 安全区域
    elif event == '-LOCK_KERNEL-':
        lock_kernel()
    elif event == '-UNLOCK_KERNEL-':
        unlock_kernel()
    elif event == '-UNLOCK_DISK-':
        unlock_disk_restriction()
    elif event == '-UPDATE_PACKAGE_LIST-':
        update_package_list()
    
    # 组件区域
    elif event == '-SET_EXE_HANDLER-':
        set_exe_handler()
    elif event == '-SET_APK_HANDLER-':
        set_apk_handler()
    elif event == '-INSTALL_TREE_FM-':
        install_tree_file_manager()
    elif event == '-SET_DEFAULT_FM-':
        set_default_file_manager()
    elif event == '-RESTORE_DEFAULT_FM-':
        restore_default_file_manager()
    
    # 应用商店区域
    elif event == '-INSTALL_SPARK_STORE-':
        install_spark_store()
    elif event == '-SET_PIP_SOURCE-':
        set_pip_source()
    elif event == '-ADD_FLAT_STORE-':
        add_flat_store_icon()
    elif event == '-ADD_APPIMAGE_STORE-':
        add_appimage_store_icon()
    
    # 美化区域
    elif event == '-INSTALL_WIN_THEME-':
        install_win_theme()
    elif event == '-INSTALL_WIN_FONTS-':
        install_win_fonts()
    elif event == '-INSTALL_BRIGHTNESS-':
        install_mask_brightness()
    
    # 其他常用区域
    elif event == '-INSTALL_MULTI_SCREEN-':
        install_multi_screen_app()
    elif event == '-INSTALL_SHARED_INPUT-':
        install_shared_input()
    elif event == '-INSTALL_STEAM-':
        install_steam()
    
    # ====================== 服务与菜单 ======================            
    if event == "-CREATE_ICON-":
        # 获取当前激活的标签页
        success, message = create_shortcut(values)
            
        if success:
            # sg.popup_ok(message, title="成功")
            window["-LOG-"].print(message)
        else:
            # sg.popup_error(message, title="错误")
            window["-LOG-"].print(message)
    
    if event == "-CREATE_MENU-":
        success, message = create_context_menu(values)
            
        if success:
            # sg.popup_ok(message, title="成功")
            window["-LOG-"].print(message)
        else:
            # sg.popup_error(message, title="错误")
            window["-LOG-"].print(message)

    if event == "-SC_ICON_BT-":
        window['-SC_ICON-'].update(choose_file())
    
    if event == "-CM_ICON_BT-":
        window['-CM_ICON-'].update(choose_file())
    
    if event == "-MANAGE_APP_ICON-":
        if values["-SC_DESKTOP-"]:
            subprocess.Popen(["xdg-open", get_desktop_dir()])
        else:
            # 打开应用程序菜单所在的目录
            home = get_real_home()
            subprocess.Popen(["xdg-open", f"{home}/.local/share/applications"])
    
    if event == "-MANAGE_SYS_ICON-":
        # 打开系统菜单所在的目录
        subprocess.Popen(["xdg-open", "/usr/share/applications"])

    if event == "-MANAGE_CONTEXT_MENU-":
        # 打开右键菜单所在的目录
        execute_command(f"xdg-open {get_real_home()}/.local/share/file-manager/actions")
    
    # 服务标签页功能
    if event == "-CREATE_SERVICE-":
        success, message = create_service(values)
        
        if success:
            # 询问是否启动服务
            if sg.popup_yes_no("服务创建成功！是否立即启动并设置开机自启？", title="成功") == "Yes":
                service_name = values["-SV_NAME-"]
                start_service(service_name)
            else:
                window["-LOG-"].print(message)
                # sg.popup_ok(message, title="成功")
        else:
            sg.popup_error(message, title="错误")
    
    if event == "-EDIT_SERVICE_FILE-":
        service_name = values["-SV_NAME-"]
        edit_service_file(service_name)
    
    if event == "-START_SERVICE-":
        service_name = values["-SV_NAME-"]
        start_service(service_name)
    
    if event == "-READ_LOG-":
        service_name = values["-SV_NAME-"]
        read_service_log(service_name)
    
    if event == "-MANAGE_SERVICES-":
        manage_services()
    
    if event == "-SET_ANDROID_APP_STYLE-":
        set_android_app_style()
    
    # 便捷安装功能
    if event == '-INSTALL_YPK-':
        install_package()
    
    if event == '-UNINSTALL_YPK-':
        uninstall_package()
    
    # 示例：点击关于按钮
    if event == '-ABOUT-':
        show_about_window(APP_NAME, APP_VERSION, UPDATE_LOG)
    
    # 添加UOS优化大师桌面图标
    if event == '-ADD_DESKTOP_ICON-':
        add_uosbetter_desktop_icon()

    if event == '-SET_BRIGHTNESS-':
        set_brightness()
window.close()
