import os
import shutil
import subprocess
import sys
import tempfile
import tarfile
import re
from pathlib import Path

def extract_archive(file_path, extract_to):
    """
    解压压缩文件到指定目录
    支持tar, tar.gz, tar.bz2等格式
    返回解压后的目录路径
    """
    try:
        if tarfile.is_tarfile(file_path):
            with tarfile.open(file_path, 'r:*') as tar:
                tar.extractall(path=extract_to)
            print(f"解压成功：{file_path} -> {extract_to}")
            return extract_to
        else:
            print(f"不支持的压缩格式：{file_path}")
            return None
    except Exception as e:
        print(f"解压失败：{e}")
        return None

def find_nested_archives(directory):
    """
    查找目录中的嵌套压缩包
    """
    nested_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            if tarfile.is_tarfile(file_path):
                nested_files.append(file_path)
    return nested_files

def extract_recursively(file_path, temp_base_dir):
    """
    递归解压，直到没有嵌套的压缩包
    返回最终的解压目录
    """
    current_extract_dir = temp_base_dir
    
    while True:
        print(f"当前解压目录：{current_extract_dir}")
        
        # 解压当前文件
        extract_result = extract_archive(file_path, current_extract_dir)
        if not extract_result:
            return None
        
        # 查找嵌套的压缩包
        nested_archives = find_nested_archives(current_extract_dir)
        
        if not nested_archives:
            print("没有发现嵌套压缩包，解压完成")
            return current_extract_dir
        
        print(f"发现嵌套压缩包：{len(nested_archives)} 个")
        
        # 如果有多个嵌套压缩包，取第一个继续解压
        file_path = nested_archives[0]
        print(f"继续解压嵌套包：{file_path}")
        
        # 创建新的解压目录
        new_extract_dir = os.path.join(temp_base_dir, f"extract_{len(nested_archives)}")
        os.makedirs(new_extract_dir, exist_ok=True)
        current_extract_dir = new_extract_dir

def find_install_files(directory):
    """
    查找INSTALL文件
    """
    install_files = []
    for item in os.listdir(directory):
        item_lower = item.lower()
        if item_lower == "install" or item_lower == "install.sh":
            install_files.append(os.path.join(directory, item))
    return install_files

def find_install_script_files(directory):
    """
    查找匹配*install*.sh模式的文件
    """
    install_scripts = []
    pattern = re.compile(r'install.*\.sh$', re.IGNORECASE)
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if pattern.match(file):
                install_scripts.append(os.path.join(root, file))
    
    return install_scripts

def find_other_shell_scripts(directory, exclude_files=None):
    """
    查找其他shell脚本文件（排除指定的文件）
    """
    if exclude_files is None:
        exclude_files = []
    
    shell_scripts = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.sh'):
                file_path = os.path.join(root, file)
                # 检查是否在排除列表中
                if file_path not in exclude_files:
                    shell_scripts.append(file_path)
    
    return shell_scripts

def run_script_as_root(script_path):
    """
    以root权限运行脚本
    """
    try:
        # 设置执行权限
        os.chmod(script_path, 0o755)
        print(f"运行安装脚本：{script_path}")
        
        # 使用sudo运行脚本
        result = subprocess.run(['sudo', script_path], check=True)
        print(f"脚本执行成功：{script_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"脚本执行失败：{e}")
        return False
    except Exception as e:
        print(f"运行脚本时发生错误：{e}")
        return False

def create_shortcuts(script_path, app_dir):
    """
    为shell脚本创建桌面快捷方式和开始菜单快捷方式
    """
    try:
        home_dir = os.path.expanduser("~")
        script_name = os.path.basename(script_path)
        app_name = os.path.splitext(script_name)[0]
        
        # 获取脚本所在的目录名作为应用名称
        dir_name = os.path.basename(app_dir)
        
        # 创建桌面快捷方式
        desktop_dir = os.path.join(home_dir, "Desktop")
        if os.path.exists(desktop_dir):
            desktop_shortcut = os.path.join(desktop_dir, f"{dir_name}-{app_name}.desktop")
            create_desktop_file(desktop_shortcut, script_path, dir_name, app_name)
        
        # 创建开始菜单快捷方式
        applications_dir = os.path.join(home_dir, ".local", "share", "applications")
        os.makedirs(applications_dir, exist_ok=True)
        menu_shortcut = os.path.join(applications_dir, f"{dir_name}-{app_name}.desktop")
        create_desktop_file(menu_shortcut, script_path, dir_name, app_name)
        
        print(f"创建快捷方式：{app_name}")
        return True
    except Exception as e:
        print(f"创建快捷方式失败：{e}")
        return False

def create_desktop_file(shortcut_path, script_path, app_name, script_name):
    """
    创建.desktop文件
    """
    content = f'''[Desktop Entry]
Name={app_name} - {script_name}
Comment=Launch {script_name}
Exec={script_path}
Icon=application-x-shellscript
Terminal=true
Type=Application
Categories=Utility;Application;
'''
    
    with open(shortcut_path, 'w') as f:
        f.write(content)
    
    os.chmod(shortcut_path, 0o755)
    print(f"创建桌面文件：{shortcut_path}")

def copy_to_opt(source_dir):
    """
    将解压后的文件夹复制到/opt/
    """
    try:
        # 获取源目录的名称
        dir_name = os.path.basename(source_dir)
        target_dir = os.path.join("/opt", dir_name)
        
        # 如果目标目录已存在，询问用户
        if os.path.exists(target_dir):
            print(f"目标目录已存在：{target_dir}")
            response = input("是否覆盖？(y/n): ")
            if response.lower() != 'y':
                print("取消复制操作")
                return None
        
        # 复制整个目录到/opt/
        print(f"复制目录到/opt/：{source_dir} -> {target_dir}")
        shutil.copytree(source_dir, target_dir)
        print(f"复制成功：{target_dir}")
        return target_dir
    except Exception as e:
        print(f"复制到/opt/失败：{e}")
        return None

def install_tar_archive(archive_path):
    """
    安装tar格式的软件包
    """
    temp_dir = None
    
    try:
        # 检查文件是否存在
        if not os.path.exists(archive_path):
            print(f"文件不存在：{archive_path}")
            return False
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="tar_install_")
        print(f"创建临时目录：{temp_dir}")
        
        # 递归解压，处理可能的嵌套压缩包
        final_extract_dir = extract_recursively(archive_path, temp_dir)
        if not final_extract_dir:
            print("解压失败")
            return False
        
        print(f"最终解压目录：{final_extract_dir}")
        
        # 查找INSTALL文件
        install_files = find_install_files(final_extract_dir)
        
        if install_files:
            print(f"找到INSTALL文件：{len(install_files)} 个")
            # 运行INSTALL脚本
            for install_file in install_files:
                if not run_script_as_root(install_file):
                    print(f"INSTALL脚本执行失败：{install_file}")
                    return False
            print("安装成功！")
            return True
        
        # 如果没有INSTALL文件，复制到/opt/
        print("未找到INSTALL文件，将复制到/opt/")
        opt_dir = copy_to_opt(final_extract_dir)
        if not opt_dir:
            print("复制到/opt/失败")
            return False
        
        # 查找并运行*install*.sh脚本
        install_scripts = find_install_script_files(opt_dir)
        if install_scripts:
            print(f"找到安装脚本：{len(install_scripts)} 个")
            for script in install_scripts:
                if not run_script_as_root(script):
                    print(f"安装脚本执行失败：{script}")
                    # 继续尝试其他脚本
        
        # 为其他.sh文件创建快捷方式
        other_scripts = find_other_shell_scripts(opt_dir, install_scripts)
        print(f"找到其他脚本文件：{len(other_scripts)} 个")
        
        for script in other_scripts:
            create_shortcuts(script, opt_dir)
        
        print("安装完成！")
        print(f"软件安装位置：{opt_dir}")
        return True
        
    except Exception as e:
        print(f"安装失败：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            print(f"清理临时目录：{temp_dir}")
            shutil.rmtree(temp_dir)

def main():
    if len(sys.argv) != 2:
        print("用法: python InstallTAR.py <archive_file>")
        print("支持的格式：tar, tar.gz, tar.bz2")
        sys.exit(1)
    
    archive_path = sys.argv[1]
    
    # 检查文件格式
    if not tarfile.is_tarfile(archive_path):
        print(f"错误：不支持的文件格式 - {archive_path}")
        print("支持的格式：tar, tar.gz, tar.bz2")
        sys.exit(1)
    
    print(f"开始安装：{archive_path}")
    result = install_tar_archive(archive_path)
    
    if result:
        print("安装成功！")
        sys.exit(0)
    else:
        print("安装失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()