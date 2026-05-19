# YPK文件结构解析

## 概述
YPK (Ylmf OS Package) 是 Ylmf OS 4 采用的软件包格式，类似于 Debian 的 DEB 包，用于软件的打包、分发和安装。

## 文件结构组成

### 1. YPK 包结构
YPK 文件本质上是一个 TAR 归档文件，包含两个核心部分：

```
leafpad_0.8.18.1.ypk
├── pkgdata          # 数据包（程序文件）
└── pkginfo          # 信息包（元数据和配置）
```

### 2. pkgdata（数据包）
- **格式**：XZ 压缩的 CPIO 归档
- **内容**：实际的程序文件和系统文件
- **解压命令**：`xz -d -c pkgdata | cpio -idu`

典型目录结构：
```
usr/
├── bin/                    # 可执行文件
│   └── leafpad
├── share/
│   ├── applications/       # 桌面配置文件
│   │   └── leafpad.desktop
│   └── pixmaps/           # 程序图标
│       └── leafpad.png
var/                        # 系统相关文件
```

### 3. pkginfo（信息包）
- **格式**：tar.bz2 压缩归档
- **内容**：元数据、配置文件和构建脚本
- **解压命令**：`tar xvf pkginfo`

典型文件内容：
```
control.xml              # 包信息（XML格式）
leafpad.desktop         # 桌面配置文件
leafpad.png             # 软件图标
```

## 构建脚本（PBS文件）

### PBS 文件结构
每个 YPK 包包含一个 `.pbs` (Package Build Script) 文件，定义包的元数据和构建行为。

### 主要字段说明

```bash
DESCRIPTION="this is a test"                    # 软件简单描述
HOMEPAGE=""                                      # 软件主页
LICENSE="GPL-2"                                  # 许可协议
PACKAGER="ylmfos4-user@115.com"                 # 打包者邮箱
RDEPEND="atk cairo gtk+"                        # 运行时依赖
BDEPEND="atk-dev cairo-dev gtk+-dev"            # 编译时依赖
NOTES=""                                        # 注意事项
```

### 钩子函数

```bash
pbs_postinst() {     # 安装后执行
    gnome2_desktop_database_update
    gnome2_icon_cache_update
}

pbs_prerm() {        # 卸载前执行
    :
}

pbs_postrm() {       # 卸载后执行
    :
}
```

## 打包和安装流程

### 手动打包步骤
1. 创建目录（格式：软件名_版本号，如 `test_123`）
2. 复制程序文件到标准目录结构
3. 创建 PBS 配置文件
4. 使用 `ypkg -b 目录名` 打包

### 自动解压
```bash
ypkg -x package.ypk  # 自动解压到 package 目录
```

### 安装命令
```bash
sudo ypkg -i package.ypk
```

### 卸载命令
```bash
sudo yget remove package_name
```

## 安装后的系统变化

1. **数据库记录**：`/var/ypkg/db/package_name/`
2. **世界文件**：`/var/ypkg/db/world` (XML格式)
3. **软件中心**：可在"已安装软件"中搜索到

## 总结

YPK 是一个功能完整的软件包管理系统，具有标准化的文件结构、元数据管理和安装钩子机制。通过理解其内部结构，可以实现到其他包格式的转换，满足不同的使用需求。