# UOS系统优化大师 (UOSBetter)

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-UOS%20%7C%20Ubuntu%20%7C%20Debian-red.svg)

一款专为 UOS (UnionTech OS) 和其他 Debian 系 Linux 发行版设计的系统优化工具。
**2.0 版本全面重构为 Web 应用**，通过浏览器访问本地 Flask 服务，左侧标签栏 + 右侧内容页布局，操作更便捷。

**作者：御坂初琴**

</div>

## ✨ 2.0 新特性

- **Web 界面**：基于 Flask 的本地服务，浏览器访问 `http://127.0.0.1:55000`，告别原生 GUI 依赖
- **左侧标签栏**：系统安全、软件组件、应用商店、美化定制、桌面与菜单、服务与软件包
- **实时日志流**：SSE 推送，操作日志实时滚动显示
- **权限提升优化**：不再需要全局 sudo 启动，仅在需要管理员权限时临时唤醒 `pkexec`
- **脚本全部 Python 化**：原 shell 脚本功能已全部迁移到 `models/` 模块
- **图标动态生成**：删除 `data/desktops/` 静态文件，所有 `.desktop` 文件即时创建
- **离线可用**：所有静态资源（Bootstrap、图标）均本地化，无需网络连接即可使用完整功能
- **清晰反馈**：成功/失败操作均有对应颜色的模态框提示，成功为绿色检查图标，失败为红色警告图标
- **AppImage 目录迁移**：默认安装到 `~/.local/share/UOSBetter/appimages/`，避免权限问题

## 📋 系统要求

- **操作系统**：UOS 20 / Deepin 20 / Ubuntu / Debian / GXDE / AnduinOS / Raspbian 等 Debian 系发行版
- **Python版本**：Python 3.8 或更高版本
- **依赖库**：Flask, requests
- **权限**：首次运行需安装依赖，运行时一般无需 sudo

## 🚀 快速开始

### 环境准备

```bash
cd /path/to/UOSBetter

# 创建并激活虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate  # Linux
```

### 安装依赖

```bash
pip install -r requirements.txt
# 或手动安装
pip install flask requests
```

### 运行程序

**方式一：直接启动**
```bash
python3 app.py
```

**方式二：使用包装脚本（推荐）**
```bash
python3 UOSBetter.py
```
包装脚本会自动检查服务是否已在运行，若未运行则自动启动并打开浏览器访问 `http://127.0.0.1:55000`。

### 添加桌面图标

在「关于」标签页点击「添加 UOSBetter 桌面图标」按钮，即可在桌面和应用程序菜单中创建快捷方式。创建的图标将指向包装脚本 `UOSBetter.py`，确保双击图标时能够正确启动服务并打开浏览器。

## 📖 功能说明

### 🔒 系统安全
- **内核版本管理**：锁定/解锁内核版本，防止误操作导致系统不稳定
- **软件源管理**：一键切换 UOS 官方源、深度源、清华源
- **更新软件包列表**：刷新 apt 缓存

### 🧩 软件组件
- **文件关联设置**：双击直接打开 `.exe` 文件（基于 Deepin-Wine / Wine）、双击安装 `.apk` 文件
- **文件管理器**：安装 Thunar 并设为默认
- **磁盘挂载**：挂载/卸载 Wine C 盘、Windows 风格系统盘盘符
- **多屏支持**：安装副屏应用（SpaceDesk）
- **键鼠共享**：安装 Barrier 实现多电脑共享键鼠
- **游戏支持**：安装 Steam 便携版，解决缺库问题

### 🏪 应用商店
- **星火应用商店**：一键安装
- **PIP源优化**：自动切换为清华大学镜像源
- **Flatpak商店**：添加 Flatpak 应用商店快捷方式
- **AppImage商店**：安装 AppImagePool 应用商店

### 🎨 美化定制
- **Windows主题**：安装 Windows 11 风格主题和图标
- **Windows字体**：安装微软雅黑等常用字体
- **亮度调节**：安装 brightnessctl，通过滑块实时调节屏幕亮度

### 🖥️ 桌面与菜单
- **快捷方式创建**：轻松创建桌面和应用程序菜单快捷方式
- **右键菜单定制**：自定义文件和文件夹的右键菜单项
- **图标管理**：管理系统和用户级应用图标

### ⚙️ 服务与软件包
- **开机自启服务**：创建和管理 systemd 系统服务
- **服务管理**：启动、停止、查看服务日志
- **软件包管理**：支持 YPK、TAR、TAR.GZ、TAR.BZ2 格式安装卸载

## 📁 项目结构

```
UOSBetter/
├── app.py                      # Flask 主程序入口
├── templates/
│   └── index.html              # 主页面模板
├── static/
│   ├── css/style.css           # 样式文件
│   ├── js/app.js               # 前端交互脚本
│   └── vendor/                 # 本地静态资源（离线使用）
│       ├── bootstrap/          # Bootstrap 5.3 CSS/JS
│       └── bootstrap-icons/    # Bootstrap Icons 字体
├── UOSBetter.py                # 包装启动脚本（推荐）
├── models/                     # 核心功能模块
│   ├── utils.py               # 工具函数
│   ├── privilege.py           # pkexec 权限提升
│   ├── system.py              # 系统管理（内核、软件源、磁盘、美化）
│   ├── apps.py                # 应用管理（商店、Wine、Steam、Barrier）
│   ├── desktop.py             # 桌面图标与菜单动态生成
│   ├── services.py            # systemd 服务管理
│   ├── packages.py            # YPK / TAR 软件包管理
│   ├── InstallYPK.py          # YPK 包管理核心（保留兼容）
│   ├── InstallTAR.py          # TAR 包管理核心（保留兼容）
│   └── GetRelease.py          # GitHub 下载管理（保留兼容）
├── documents/                  # 项目文档
├── data/
│   ├── apks/                   # APK 应用包
│   │   └── SpaceDesk.apk
│   ├── appImages/              # AppImage 应用
│   │   └── AppImagePool.AppImage
│   └── themes/                 # 主题文件
│       └── win11theme.tar
├── requirements.txt            # Python 依赖
├── README.md                   # 项目说明
└── .venv/                      # Python 虚拟环境
```

## 🔧 核心模块说明

### privilege.py - 权限提升
- 使用 `pkexec` 进行临时权限提升
- 检测是否已 root，避免重复提权
- 统一封装命令执行接口

### system.py - 系统管理
- 原 `data/scripts/` 中所有 shell 脚本已转换为 Python 函数
- 软件源切换、内核锁定、磁盘挂载、亮度调节等

### desktop.py - 桌面图标
- 动态生成 `.desktop` 文件内容
- 支持系统图标自动复制到用户目录
- 创建快捷方式、右键菜单项

## ⚠️ 注意事项

1. 部分功能（如安装软件、修改系统配置）需要管理员权限，程序会自动弹出 `pkexec` 认证窗口
2. 锁定内核版本后可能无法更新显卡驱动，请根据需要谨慎使用
3. 安装 Windows 主题和字体后需要注销重新登录才能生效
4. 右键菜单功能需要重启文件管理器才能生效
5. YPK 包的虚拟环境模式更安全，LOCAL 模式系统集成度更高

## 📝 更新日志

### V2.0.0
- 全面重构为 Flask Web 应用，浏览器访问本地服务
- 左侧标签栏 + 右侧内容页布局
- 移除 PySimpleGUI 依赖
- 所有脚本功能改为 Python 实现
- 使用 pkexec 进行权限提升，无需全局 sudo
- AppImage 默认目录迁移至 ~/.local/share/UOSBetter/appimages/
- 桌面图标改为动态生成，删除 desktops 文件夹
- 实时日志流显示
- 重新规划标签页：系统安全、软件组件、应用商店、美化定制、桌面与菜单、服务与软件包

### V1.5.0
- 修复带目录的文件管理器设置为默认文件管理器后，无法打开的问题
- 删除部分图标，提升在XFCE上的兼容性

### V1.4.0
- 修改带目录的文件管理器为thunar
- 进一步补全Win11主题的图标，提升在XFCE上的兼容性

### V1.3.0
- 修改带目录的文件管理器为PCManFM
- 增加挂载Wine的C盘为盘符功能
- 增加系统盘显示为Windows风格文件夹的功能
- 双击打开.exe文件支持选择安装Deepin-Wine或Wine
- 安装Wine时自动安装常用字体

### V1.2.0
- 修复了创建的图标启动目录为桌面的问题
- 主题中增加了压缩包和NEMO的图标
- 修改复制操作的原文件为绝对地址

### V1.1.0
- 增加了TAR等格式的绿色软件的安装卸载功能
- Steam改为在线获取，大幅缩小软件体积

### V1.0.0
- 部分功能支持Debian系的其他系统
- 比如Ubuntu，GXDE，AnduinOS，Raspbian等

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：
- 提交 Issue
- 查看项目文档：`documents/` 目录
- 运行日志：Web 界面底部的实时日志输出

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ for UOS Community

</div>
