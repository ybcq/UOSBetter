# UOS系统优化大师

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

一款专为UOS（统信操作系统）设计的系统优化工具，提供图形化界面，让系统配置更加简单便捷。

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

## 📋 系统要求

- **操作系统**：UOS 20 / Deepin 20 / Ubuntu / Debian 系发行版
- **Python版本**：Python 3.6 或更高版本
- **权限要求**：需要管理员权限（sudo）运行

## 🚀 快速开始

### 安装依赖

```bash
pip install pysimplegui-4-foss
```

### 运行程序

```bash
# 使用管理员权限运行
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

## 📁 项目结构

```
UOSBetter/
├── UOSBetter.py              # 主程序文件
├── README.md                 # 项目说明文档
└── data/
    ├── apks/                 # APK应用包
    │   └── SpaceDesk.apk
    ├── appImages/            # AppImage应用
    │   ├── AppImagePool.AppImage
    │   └── Steam.AppImage
    ├── desktops/             # 桌面快捷方式
    │   ├── appimage.desktop
    │   ├── flathub.desktop
    │   └── steam.desktop
    ├── scripts/              # 安装脚本
    │   ├── APT-Deepin20.sh
    │   ├── APT-TsingHua.sh
    │   ├── APT-UOS20.sh
    │   └── Deepin-Wine.sh
    └── themes/               # 主题文件
        └── win11theme.tar
```

## 🔄 更新日志

### v1.0.0
- 首次发布
- 部分功能支持Debian系的其他系统（如Ubuntu、GXDE、AnduinOS、Raspbian等）

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 注意事项

1. 部分功能需要管理员权限，请使用 `sudo` 运行程序
2. 锁定内核版本后可能无法更新显卡驱动，请根据需要谨慎使用
3. 安装Windows主题和字体后需要注销重新登录才能生效
4. 右键菜单功能需要重启文件管理器才能生效

## 📮 联系方式

如有问题或建议，欢迎通过以下方式联系：

- 提交 [Issue](../../issues)
- 发送邮件

---

<div align="center">

**如果这个项目对您有帮助，请给个 ⭐ Star 支持一下！**

Made with ❤️ for UOS Community

</div>