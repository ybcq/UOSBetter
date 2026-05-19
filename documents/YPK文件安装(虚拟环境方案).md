# YPK文件安装（虚拟环境方案）

## 方案概述
本方案通过创建独立的虚拟环境来安装YPK软件包，避免与系统文件冲突，实现软件的沙盒化运行。

## 安装步骤

### 1. 解压YPK文件
- **说明**：此步骤在 `InstallYPK.py` 中已实现
- **操作**：解压YPK包，获取 pkgdata 和 pkginfo 内容

### 2. 获取软件名称
- **说明**：从 control.xml 中读取软件包名称
- **位置**：`control.xml` 文件
- **示例**：
  ```xml
  <Package name="appname">
  ```
- **结果**：获得软件名 `{appname}`，同时也是主程序名（位于 usr/bin 文件夹中）

### 3. 创建独立目录
- **目标路径**：`~/.local/share/apps/{appname}/`
- **操作**：将解压后的YPK文件内容复制到此目录
- **作用**：为每个软件创建独立的运行环境

### 4. 编写启动脚本
- **文件名**：`{appname}.sh`
- **位置**：在软件目录根目录
- **功能**：设置环境变量并启动程序

#### 启动脚本示例
```bash
#!/bin/bash
# 软件安装目录
APP_DIR="$HOME/.local/share/apps/{appname}"

# 设置库文件搜索路径：优先使用软件自带的库
export LD_LIBRARY_PATH="$APP_DIR/usr/lib:$LD_LIBRARY_PATH"

# 设置数据文件搜索路径（用于图标、桌面入口等）
export XDG_DATA_DIRS="$APP_DIR/usr/share:$XDG_DATA_DIRS"

# 设置可执行文件路径（如果软件需要调用自身的其他程序）
export PATH="$APP_DIR/usr/bin:$PATH"

# 启动主程序（假设主程序在 usr/bin 下）
exec "$APP_DIR/usr/bin/{appname}" "$@"
```

- **赋予执行权限**：`chmod +x {appname}.sh`

### 5. 处理图标文件
- **源路径**：解压后的 `usr/share/icons/` 目录
- **文件类型**：`.svg` 或 `.png` 文件
- **搜索范围**：可能不在该层目录，需要递归查找
- **目标路径**：`~/.local/share/icons/hicolor/scalable/apps/`
- **操作**：复制找到的图标文件到目标路径

### 6. 创建桌面快捷方式
- **源文件**：`usr/share/applications/` 目录下的 `.desktop` 文件
- **修改内容**：
  - 更新 `Exec` 行，指向实际的启动脚本 `{appname}.sh`
  - 确保图标路径正确
- **目标位置**：
  - 用户桌面：`~/Desktop/`
  - 应用菜单：`~/.local/share/applications/`
- **权限设置**：`chmod +x {desktop_file}`
- **特殊情况**：如果没有 `.desktop` 文件，需要自行创建

#### 桌面文件示例
```ini
[Desktop Entry]
Name={appname}
Comment=Application description
Exec=~/.local/share/apps/{appname}.sh
Icon={appname}
Terminal=false
Type=Application
Categories=Utility;
```

## 完整流程总结
1. 解压YPK包
2. 读取软件名称
3. 创建独立安装目录
4. 编写并配置启动脚本
5. 处理和安装图标
6. 创建和配置桌面快捷方式
7. 测试软件运行

## 优势
- **隔离性**：软件互不干扰
- **安全性**：不影响系统文件
- **便携性**：易于备份和迁移
- **兼容性**：避免库冲突问题

## 注意事项
- 确保所有路径使用绝对路径
- 检查依赖库是否完整
- 测试软件在虚拟环境中的运行状态
- 注意权限设置，确保脚本可执行

