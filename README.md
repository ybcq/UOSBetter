# UOS系统优化大师 (UOSBetter)

<div align="center">

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-UOS%20%7C%20Ubuntu%20%7C%20Debian-red.svg)

一款专为 UOS (UnionTech OS) 和其他 Debian 系 Linux 发行版设计的系统优化工具，提供图形化界面，让系统配置、软件安装和管理任务更加简单便捷。

**作者：御坂初琴**

</div>

## ✨ 功能特性

### 🔒 安全与组件
- **内核版本管理**：锁定/解锁内核版本，防止误操作导致系统不稳定
- **软件源管理**：一键更新应用版本列表
- **文件关联设置**：
  - 双击直接打开 `.exe` 文件（基于 Deepin-Wine）
  - 双击直接安装 `.apk` 文件（基于 UEngine）
- **文件管理器增强**：安装带目录树的 Nemo 文件管理器
- **多屏支持**：安装副屏应用（SpaceDesk）
- **键鼠共享**：安装 Barrier 实现多电脑共享键鼠
- **游戏支持**：安装 Steam 便携版，解决缺库问题

### 🏪 应用商店
- **星火应用商店**：一键安装星火应用商店
- **PIP源优化**：自动切换为清华大学镜像源
- **Flatpak商店**：添加 Flatpak 应用商店快捷方式
- **AppImage商店**：安装 AppImagePool 应用商店

### 🎨 美化定制
- **Windows主题**：安装 Windows 11 风格主题
- **Windows字体**：安装微软雅黑等常用字体
- **亮度调节**：安装遮罩亮度调节工具

### 🖥️ 桌面与菜单
- **快捷方式创建**：轻松创建桌面和应用程序菜单快捷方式
- **右键菜单定制**：自定义文件和文件夹的右键菜单项
- **图标管理**：管理系统和用户级应用图标

### ⚙️ 系统服务
- **开机自启服务**：创建和管理 systemd 系统服务
- **服务管理**：启动、停止、查看服务日志
- **服务编辑**：手动编辑服务配置文件

### 📦 软件包管理
- **YPK 包管理**：支持 YPK 格式软件的安装和卸载（LOCAL/虚拟环境双模式）
- **TAR 包管理**：支持 TAR、TAR.GZ、TAR.BZ2 格式软件的智能安装
- **GitHub Releases下载**：支持从 GitHub releases 在线下载软件，带进度显示

## 📋 系统要求

- **操作系统**：UOS 20 / Deepin 20 / Ubuntu / Debian / GXDE / AnduinOS / Raspbian 等 Debian 系发行版
- **Python版本**：Python 3.6 或更高版本
- **权限要求**：需要管理员权限（sudo）运行以使用完整功能
- **依赖库**：PySimpleGUI、requests

## 🚀 快速开始

### 环境准备

```bash
# 克隆或下载项目
cd /path/to/UOSBetter

# 创建并激活虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### 安装依赖

```bash
pip install pysimplegui-4-foss requests
```

### 运行程序

```bash
# 使用管理员权限运行以使用完整功能
sudo python3 UOSBetter.py
```

### 添加桌面图标

在程序主界面点击「添加UOS优化大师桌面图标」按钮，即可在桌面和应用程序菜单中创建快捷方式。

## 📖 使用说明

### 安全优化与组件

1. **锁定内核版本**：防止系统更新时自动更换内核，适合需要稳定环境的用户
2. **设置.exe文件关联**：点击后，找一个exe文件右键选择默认程序，找到Deepin-Wine即可
3. **安装Steam便携版**：解决UOS安装Steam时各种缺库弹窗问题

### 桌面与菜单

1. **创建快捷方式**：
   - 填写图标名称
   - 选择程序路径
   - 选择图标（支持系统图标）
   - 选择目标位置（桌面/应用程序菜单）
   - 点击「创建」

2. **创建右键菜单**：
   - 填写菜单名称
   - 填写执行命令
   - 选择菜单类型（文件/文件夹）
   - 选择作用范围（当前用户/所有用户）

### 系统级自启服务

1. **创建服务**：
   - 填写服务名称
   - 填写执行命令
   - 设置重启间隔
   - 点击「创建」

2. **管理服务**：
   - 点击「手动启动服务」启动并设置开机自启
   - 点击「读取日志」查看服务运行日志

### 软件包管理

#### YPK 包管理
```bash
# 安装 YPK 包
python3 models/InstallYPK.py package.ypk

# LOCAL 模式卸载
python3 models/InstallYPK.py package.ypk uninstall

# 虚拟环境模式卸载
python3 models/InstallYPK.py package.ypk uninstall_safe
```

#### TAR 包管理
```bash
# 安装 TAR 包
python3 models/InstallTAR.py software.tar.gz
```

#### GitHub Releases 下载
- 支持从 GitHub releases 在线下载最新版软件
- 实时显示下载进度
- 自动创建桌面和开始菜单图标

## 📁 项目结构

```
UOSBetter/
├── UOSBetter.py              # 主程序文件，GUI界面和事件处理
├── README.md                 # 项目说明文档
├── models/                   # 核心功能模块
│   ├── InstallYPK.py        # YPK 软件包安装/卸载
│   ├── InstallTAR.py        # TAR 软件包安装
│   ├── GetRelease.py        # GitHub releases 下载管理
│   └── PySimpleGUI.py       # GUI 库本地副本
├── documents/               # 项目文档
│   ├── YPK文件结构解析.md
│   ├── YPK文件安装(虚拟环境方案).md
│   ├── YPK文件安装(LOCAL方案).md
│   └── TAR文件安装(复合方案).md
├── data/                    # 数据文件
│   ├── apks/                # APK应用包
│   │   └── SpaceDesk.apk
│   ├── appImages/           # AppImage应用
│   │   └── AppImagePool.AppImage
│   ├── desktops/            # 桌面快捷方式
│   │   ├── appimage.desktop
│   │   ├── flathub.desktop
│   │   └── steam.desktop
│   ├── scripts/             # 安装脚本
│   │   ├── APT-Deepin20.sh
│   │   ├── APT-TsingHua.sh
│   │   ├── APT-UOS20.sh
│   │   └── Deepin-Wine.sh
│   └── themes/              # 主题文件
│       └── win11theme.tar
├── .venv/                   # Python 虚拟环境
└── bak/                     # 备份文件目录
```

## 🔧 核心模块详解

### InstallYPK.py - YPK 包管理器
- **功能**：处理 YPK (Ylmf OS Package) 格式软件的安装和卸载
- **安装模式**：
  - **LOCAL 模式**：安装到 `/usr/local/` 等系统目录，需要 root 权限
  - **虚拟环境模式**：安装到 `~/.local/share/apps/{appname}/`，用户权限即可
- **安全特性**：临时目录隔离、文件过滤、关键文件保护

### InstallTAR.py - TAR 包管理器
- **功能**：处理 TAR、TAR.GZ、TAR.BZ2 格式软件的安装
- **安装策略**：
  - **脚本安装模式**：检测到 `INSTALL` 文件时直接运行
  - **手动安装模式**：复制到 `/opt/` 并创建快捷方式
- **特性**：支持多层嵌套压缩包、自动创建快捷方式

### GetRelease.py - GitHub Releases 下载管理
- **功能**：从 GitHub releases 下载文件，支持进度显示
- **特性**：进度回调、错误恢复、断点续传、文件大小人性化显示

## 🔄 更新日志

### v1.0.0
- 首次发布
- 支持 Debian 系的其他系统（如 Ubuntu、GXDE、AnduinOS、Raspbian 等）
- 新增 YPK 和 TAR 软件包管理功能
- 新增 GitHub releases 在线下载功能
- 完善的虚拟环境支持和安全机制

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发规范
- 使用中文注释和文档字符串
- 函数命名采用小写加下划线
- 类命名采用大驼峰
- 完整的异常处理和错误日志

### 添加新功能
1. 在 `models/` 目录创建新的安装模块
2. 实现对应的功能函数
3. 在 `UOSBetter.py` 中导入和集成
4. 更新文档说明

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 注意事项

1. 部分功能需要管理员权限，请使用 `sudo` 运行程序
2. 锁定内核版本后可能无法更新显卡驱动，请根据需要谨慎使用
3. 安装Windows主题和字体后需要注销重新登录才能生效
4. 右键菜单功能需要重启文件管理器才能生效
5. YPK 包的虚拟环境模式更安全，LOCAL 模式系统集成度更高
6. 临时文件会自动清理，不用担心磁盘空间问题

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](../../issues)
- 查看项目文档：`documents/` 目录
- 运行日志：程序界面的实时日志输出

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ for UOS Community

</div>