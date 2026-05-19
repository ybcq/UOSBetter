import os
import shutil
import subprocess
import sys
import tempfile

def extract_ypk(ypk_file_path):
    """
    解包 YPK 文件到临时目录
    返回临时目录路径，如果失败返回None
    """
    temp_dir = None
    original_dir = os.getcwd()
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="ypk_extract_")
        print(f"创建临时目录：{temp_dir}")

        # 复制 YPK 文件到临时目录
        ypk_filename = os.path.basename(ypk_file_path)
        temp_ypk_path = os.path.join(temp_dir, ypk_filename)
        shutil.copy2(ypk_file_path, temp_ypk_path)

        # 切换到临时目录进行解压
        os.chdir(temp_dir)

        # 解压 YPK 文件
        print("解压 YPK 文件...")
        subprocess.run(["tar", "xvf", ypk_filename], check=True, capture_output=True)

        # 解压 pkgdata
        print("解压 pkgdata...")
        result = os.popen("xz -d -c pkgdata|cpio -idu")
        print(result.read())

        # 解压 pkginfo
        print("解压 pkginfo...")
        subprocess.run(["tar", "xvf", "pkginfo"], check=True, capture_output=True)

        print("解包成功！")
        
        # 恢复原始工作目录
        os.chdir(original_dir)
        
        return temp_dir
        
    except subprocess.CalledProcessError as e:
        print(f"解包失败：{e}")
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.chdir(original_dir)
        return None
    except Exception as e:
        print(f"发生错误：{e}")
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.chdir(original_dir)
        return None

def should_exclude_file(file_path, file_name):
    """
    检查文件或目录是否应该被排除
    排除规则：
    1. pk开头的文件
    2. 路径中含有dbus或polkit的文件或文件夹
    """
    # 排除pk开头的文件
    if file_name.startswith('pk'):
        return True
    
    # 排除路径中含有dbus或polkit的文件或文件夹
    lower_path = file_path.lower()
    if 'dbus' in lower_path or 'polkit' in lower_path:
        return True
    
    return False

def merge_directories(source_dir, target_dir):
    """
    将源目录合并到目标目录，排除危险文件
    """
    try:
        # 确保目标目录存在
        os.makedirs(target_dir, exist_ok=True)

        # 遍历源目录中的所有文件和子目录
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            target_item = os.path.join(target_dir, item)

            # 检查是否应该排除此文件/目录
            if should_exclude_file(source_item, item):
                print(f"跳过危险文件/目录：{source_item}")
                continue

            # 如果是文件，直接复制
            if os.path.isfile(source_item):
                shutil.copy2(source_item, target_item)
            # 如果是目录，递归合并
            elif os.path.isdir(source_item):
                merge_directories(source_item, target_item)

        print(f"合并目录成功：{source_dir} -> {target_dir}")
        return True
    except Exception as e:
        print(f"合并目录失败：{e}")
        return False

def install_ypk(ypk_file_path):
    """
    安装 YPK 文件
    """
    temp_dir = None
    try:
        # 解包 YPK 文件到临时目录
        temp_dir = extract_ypk(ypk_file_path)
        if not temp_dir:
            return False

        # 定义要合并的目录
        directories_to_merge = ["usr", "var", "opt", "tmp", "etc"]

        # 合并每个目录到系统对应目录
        for directory in directories_to_merge:
            source_dir = os.path.join(temp_dir, directory)
            
            # 特殊处理 usr 目录：将内容复制到 /usr/local/ 而不是 /
            if directory == "usr":
                target_dir = "/usr/local"
            elif directory == "etc":
                target_dir = "/usr/local/etc"
            else:
                target_dir = os.path.join("/", directory)

            if os.path.exists(source_dir):
                merge_directories(source_dir, target_dir)

        print("YPK 文件安装成功！")
        return True
    except Exception as e:
        print(f"安装失败：{e}")
        return False
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            print(f"清理临时目录：{temp_dir}")
            shutil.rmtree(temp_dir)

def install_ypk_safe(ypk_file_path):
    """
    使用虚拟环境方案安全安装 YPK 文件
    将软件安装到 ~/.local/share/apps/{appname} 独立目录中
    """
    temp_dir = None
    try:
        # 解包 YPK 文件到临时目录
        temp_dir = extract_ypk(ypk_file_path)
        if not temp_dir:
            return False

        # 读取 control.xml 获取软件名称
        control_xml_path = os.path.join(temp_dir, "control.xml")
        if not os.path.exists(control_xml_path):
            print("错误：找不到 control.xml 文件")
            return False

        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(control_xml_path)
            root = tree.getroot()
            appname = root.get("name")
            if not appname:
                print("错误：无法从 control.xml 中获取软件名称")
                return False
        except Exception as e:
            print(f"解析 control.xml 失败：{e}")
            return False

        print(f"软件名称：{appname}")

        # 创建独立安装目录
        home_dir = os.path.expanduser("~")
        app_install_dir = os.path.join(home_dir, ".local", "share", "apps", appname)
        os.makedirs(app_install_dir, exist_ok=True)
        print(f"创建安装目录：{app_install_dir}")

        # 复制解压后的文件到安装目录
        for item in os.listdir(temp_dir):
            source_item = os.path.join(temp_dir, item)
            target_item = os.path.join(app_install_dir, item)
            if os.path.isdir(source_item):
                shutil.copytree(source_item, target_item, dirs_exist_ok=True)
            else:
                shutil.copy2(source_item, target_item)
        print("文件复制完成")

        # 编写启动脚本
        launch_script_content = f'''#!/bin/bash
# 软件安装目录
APP_DIR="{app_install_dir}"

# 设置库文件搜索路径：优先使用软件自带的库
export LD_LIBRARY_PATH="$APP_DIR/usr/lib:$LD_LIBRARY_PATH"

# 设置数据文件搜索路径（用于图标、桌面入口等）
export XDG_DATA_DIRS="$APP_DIR/usr/share:$XDG_DATA_DIRS"

# 设置可执行文件路径（如果软件需要调用自身的其他程序）
export PATH="$APP_DIR/usr/bin:$PATH"

# 启动主程序
exec "$APP_DIR/usr/bin/{appname}" "$@"
'''

        launch_script_path = os.path.join(home_dir, ".local", "share", "apps", f"{appname}.sh")
        with open(launch_script_path, "w") as f:
            f.write(launch_script_content)
        os.chmod(launch_script_path, 0o755)
        print(f"创建启动脚本：{launch_script_path}")

        # 处理图标文件
        icons_dir = os.path.join(app_install_dir, "usr", "share", "icons")
        target_icons_dir = os.path.join(home_dir, ".local", "share", "icons", "hicolor", "scalable", "apps")
        os.makedirs(target_icons_dir, exist_ok=True)

        icon_found = False
        if os.path.exists(icons_dir):
            for root, dirs, files in os.walk(icons_dir):
                for file in files:
                    if file.endswith(('.png', '.svg', '.svgz')):
                        source_icon = os.path.join(root, file)
                        target_icon = os.path.join(target_icons_dir, file)
                        shutil.copy2(source_icon, target_icon)
                        icon_found = True
                        print(f"复制图标：{file}")

        # 处理桌面文件
        desktop_files_dir = os.path.join(app_install_dir, "usr", "share", "applications")
        target_applications_dir = os.path.join(home_dir, ".local", "share", "applications")
        os.makedirs(target_applications_dir, exist_ok=True)

        desktop_file_found = False
        if os.path.exists(desktop_files_dir):
            for file in os.listdir(desktop_files_dir):
                if file.endswith('.desktop'):
                    source_desktop = os.path.join(desktop_files_dir, file)
                    target_desktop = os.path.join(target_applications_dir, file)
                    
                    # 读取并修改桌面文件
                    with open(source_desktop, 'r') as f:
                        content = f.read()
                    
                    # 替换执行路径为我们的启动脚本
                    import re
                    content = re.sub(r'^Exec=.*$', f'Exec={launch_script_path}', content, flags=re.MULTILINE)
                    
                    # 写入目标位置
                    with open(target_desktop, 'w') as f:
                        f.write(content)
                    
                    os.chmod(target_desktop, 0o755)
                    desktop_file_found = True
                    print(f"创建桌面文件：{file}")

        # 如果没有找到桌面文件，创建一个默认的
        if not desktop_file_found:
            default_desktop_content = f'''[Desktop Entry]
Name={appname}
Comment=YPK Application
Exec={launch_script_path}
Icon={appname}
Terminal=false
Type=Application
Categories=Utility;
'''
            default_desktop_path = os.path.join(target_applications_dir, f"{appname}.desktop")
            with open(default_desktop_path, 'w') as f:
                f.write(default_desktop_content)
            os.chmod(default_desktop_path, 0o755)
            print(f"创建默认桌面文件：{default_desktop_path}")

        # 复制到桌面（如果存在桌面目录）
        desktop_dir = os.path.join(home_dir, "Desktop")
        if os.path.exists(desktop_dir):
            desktop_target = os.path.join(desktop_dir, f"{appname}.desktop")
            if os.path.exists(target_applications_dir):
                # 从applications目录复制
                for file in os.listdir(target_applications_dir):
                    if file.endswith('.desktop'):
                        source = os.path.join(target_applications_dir, file)
                        shutil.copy2(source, desktop_target)
                        os.chmod(desktop_target, 0o755)
                        print(f"复制到桌面：{desktop_target}")
                        break

        print(f"YPK 文件安全安装成功！软件名称：{appname}")
        print(f"安装位置：{app_install_dir}")
        print(f"启动脚本：{launch_script_path}")

        return True

    except Exception as e:
        print(f"安全安装失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            print(f"清理临时目录：{temp_dir}")
            shutil.rmtree(temp_dir)

def get_installed_files(source_dir, base_dir=""):
    """
    递归获取源目录中的所有文件，映射到系统路径
    """
    files_to_delete = []
    
    try:
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            relative_path = os.path.join(base_dir, item)
            
            # 检查是否应该排除此文件/目录
            if should_exclude_file(source_item, item):
                print(f"跳过危险文件/目录：{source_item}")
                continue
            
            # 确定目标路径
            if base_dir == "usr":
                target_path = os.path.join("/usr/local", item)
            elif base_dir == "etc":
                target_path = os.path.join("/usr/local/etc", item)
            elif base_dir == "":
                # 顶层目录
                if item in ["usr", "var", "opt", "tmp", "etc"]:
                    if item == "usr":
                        target_path = "/usr/local"
                    elif item == "etc":
                        target_path = "/usr/local/etc"
                    else:
                        target_path = os.path.join("/", item)
                else:
                    continue  # 跳过其他顶层文件
            else:
                target_path = os.path.join("/", relative_path)
            
            if os.path.isfile(source_item):
                files_to_delete.append(("file", target_path))
            elif os.path.isdir(source_item):
                files_to_delete.append(("dir", target_path))
                # 递归处理子目录
                files_to_delete.extend(get_installed_files(source_item, relative_path))
                
    except Exception as e:
        print(f"获取文件列表失败：{e}")
    
    return files_to_delete

def is_critical_file(file_path):
    """
    检查是否为关键文件，避免删除系统关键文件
    """
    critical_patterns = [
        '/bin/', '/sbin/', '/lib/', '/lib64/',
        '/usr/bin/', '/usr/sbin/', '/usr/lib/', '/usr/lib64/',
        '/etc/passwd', '/etc/shadow', '/etc/group',
        '/etc/fstab', '/etc/hosts',
    ]
    
    for pattern in critical_patterns:
        if file_path.startswith(pattern):
            return True
    
    return False

def uninstall_ypk(ypk_file_path):
    """
    卸载 YPK 文件（LOCAL方案）
    根据解压后的YPK文件内容确定要删除的文件
    """
    temp_dir = None
    
    try:
        print(f"开始卸载：{ypk_file_path}")
        
        # 解包 YPK 文件到临时目录
        temp_dir = extract_ypk(ypk_file_path)
        if not temp_dir:
            print("解压失败，无法进行卸载")
            return False
        
        # 获取需要删除的文件列表
        files_to_delete = get_installed_files(temp_dir)
        
        if not files_to_delete:
            print("没有找到需要删除的文件")
            return True
        
        print(f"找到 {len(files_to_delete)} 个文件/目录需要删除")
        
        # 按照从深到浅的顺序排序（先删除文件，再删除目录）
        files_to_delete.sort(key=lambda x: (x[0] != 'file', len(x[1])), reverse=True)
        
        deleted_count = 0
        skipped_count = 0
        
        # 删除文件和目录
        for file_type, file_path in files_to_delete:
            if not os.path.exists(file_path):
                print(f"文件不存在，跳过：{file_path}")
                skipped_count += 1
                continue
            
            if is_critical_file(file_path):
                print(f"跳过关键文件：{file_path}")
                skipped_count += 1
                continue
            
            try:
                if file_type == "file":
                    os.remove(file_path)
                    print(f"删除文件：{file_path}")
                else:  # directory
                    # 只删除空目录，避免误删其他软件的文件
                    if not os.listdir(file_path):
                        os.rmdir(file_path)
                        print(f"删除空目录：{file_path}")
                    else:
                        print(f"跳过非空目录：{file_path}")
                        skipped_count += 1
                        continue
                
                deleted_count += 1
                
            except Exception as e:
                print(f"删除失败：{file_path} - {e}")
                skipped_count += 1
        
        print(f"卸载完成！删除了 {deleted_count} 个文件，跳过 {skipped_count} 个文件")
        return True
        
    except Exception as e:
        print(f"卸载失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            print(f"清理临时目录：{temp_dir}")
            shutil.rmtree(temp_dir)

def uninstall_ypk_safe(ypk_file_path):
    """
    卸载 YPK 文件（虚拟环境方案）
    删除对应文件夹、图标和快捷方式
    """
    temp_dir = None
    
    try:
        print(f"开始安全卸载：{ypk_file_path}")
        
        # 解包 YPK 文件到临时目录获取软件名称
        temp_dir = extract_ypk(ypk_file_path)
        if not temp_dir:
            print("解压失败，无法进行卸载")
            return False
        
        # 读取 control.xml 获取软件名称
        control_xml_path = os.path.join(temp_dir, "control.xml")
        if not os.path.exists(control_xml_path):
            print("错误：找不到 control.xml 文件")
            return False

        import xml.etree.ElementTree as ET
        try:
            tree = ET.parse(control_xml_path)
            root = tree.getroot()
            appname = root.get("name")
            if not appname:
                print("错误：无法从 control.xml 中获取软件名称")
                return False
        except Exception as e:
            print(f"解析 control.xml 失败：{e}")
            return False

        print(f"软件名称：{appname}")

        home_dir = os.path.expanduser("~")
        deleted_items = []
        
        # 1. 删除安装目录
        app_install_dir = os.path.join(home_dir, ".local", "share", "apps", appname)
        if os.path.exists(app_install_dir):
            shutil.rmtree(app_install_dir)
            print(f"删除安装目录：{app_install_dir}")
            deleted_items.append(app_install_dir)
        
        # 2. 删除启动脚本
        launch_script_path = os.path.join(home_dir, ".local", "share", "apps", f"{appname}.sh")
        if os.path.exists(launch_script_path):
            os.remove(launch_script_path)
            print(f"删除启动脚本：{launch_script_path}")
            deleted_items.append(launch_script_path)
        
        # 3. 删除图标文件
        icons_dir = os.path.join(home_dir, ".local", "share", "icons", "hicolor", "scalable", "apps")
        if os.path.exists(icons_dir):
            for file in os.listdir(icons_dir):
                if file.startswith(appname):
                    icon_path = os.path.join(icons_dir, file)
                    os.remove(icon_path)
                    print(f"删除图标：{icon_path}")
                    deleted_items.append(icon_path)
        
        # 4. 删除开始菜单快捷方式
        applications_dir = os.path.join(home_dir, ".local", "share", "applications")
        if os.path.exists(applications_dir):
            for file in os.listdir(applications_dir):
                if file.startswith(appname) and file.endswith('.desktop'):
                    desktop_path = os.path.join(applications_dir, file)
                    os.remove(desktop_path)
                    print(f"删除开始菜单快捷方式：{desktop_path}")
                    deleted_items.append(desktop_path)
        
        # 5. 删除桌面快捷方式
        desktop_dir = os.path.join(home_dir, "Desktop")
        if os.path.exists(desktop_dir):
            for file in os.listdir(desktop_dir):
                if file.startswith(appname) and file.endswith('.desktop'):
                    desktop_shortcut = os.path.join(desktop_dir, file)
                    os.remove(desktop_shortcut)
                    print(f"删除桌面快捷方式：{desktop_shortcut}")
                    deleted_items.append(desktop_shortcut)
        
        print(f"安全卸载完成！共删除 {len(deleted_items)} 个项目")
        print(f"软件名称：{appname}")
        
        return True
        
    except Exception as e:
        print(f"安全卸载失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            print(f"清理临时目录：{temp_dir}")
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python InstallYPK.py <ypk_file_path> [install|uninstall|uninstall_safe]")
        print("默认操作：install")
        sys.exit(1)

    ypk_file_path = sys.argv[1]
    action = sys.argv[2] if len(sys.argv) > 2 else "install"

    if action == "install":
        install_ypk(ypk_file_path)
    elif action == "uninstall":
        uninstall_ypk(ypk_file_path)
    elif action == "uninstall_safe":
        uninstall_ypk_safe(ypk_file_path)
    else:
        print(f"未知操作：{action}")
        print("支持的操作：install, uninstall, uninstall_safe")
        sys.exit(1)