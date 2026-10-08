# PySimpleGUI 应用转写为 Flask 应用方案

## 1. 整体架构迁移

| 维度 | 原方案 (1.x) | 新方案 (2.0) |
|------|-------------|-------------|
| GUI 框架 | PySimpleGUI（Tkinter） | Flask + Bootstrap 5.3 浏览器界面 |
| 访问方式 | 桌面应用窗口 | 浏览器访问 `http://127.0.0.1:55000`（UOSBetter）<br>浏览器访问 `http://127.0.0.1:55500`（CQApkTools） |
| 权限提升 | 全局 `sudo` 启动 | `pkexec` 按需提权（UOSBetter）<br>无需提权（CQApkTools，但需管理员权限的操作会弹出 UAC） |
| 布局结构 | PySimpleGUI TabGroup | 左侧 sidebar nav-pills + 右侧内容区 + 右侧日志面板 |
| 日志输出 | 窗口文本框 | SSE 实时日志流（右侧固定面板） |
| 图标/菜单 | 静态 `data/desktops/` | Python 动态生成 `.desktop` |
| 打包方式 | PyInstaller 打包单文件 exe | 无需打包，直接运行 `python3 app.py`（可选：使用 PyInstaller 制作便携版） |
| 跨平台支持 | Windows（PySimpleGUI） | Linux（UOSBetter，使用 zenity）<br>Windows（CQApkTools，使用 easygui） |

## 2. 项目文件结构

```
UOSBetter/
├── app.py                      # Flask 主入口，REST API + SSE
├── templates/
│   └── index.html              # 单页面模板
├── static/
│   ├── css/style.css           # 蓝白主题样式
│   ├── js/app.js               # 前端交互（SSE、文件选择、Tab 切换、模态框）
│   └── vendor/                 # 本地静态资源（离线使用）
│       ├── bootstrap/          # Bootstrap 5.3 (CSS/JS)
│       └── bootstrap-icons/    # Bootstrap Icons (CSS/fonts)
├── models/
│   ├── utils.py                # 常量、路径工具、UPDATE_LOG
│   ├── privilege.py            # pkexec 封装
│   ├── system.py               # 内核/软件源/磁盘/亮度/文件管理器
│   ├── apps.py                 # 商店/Wine/Steam/Barrier
│   ├── desktop.py              # 动态 .desktop 生成
│   ├── services.py             # systemd 服务管理
│   └── packages.py             # YPK/TAR 包安装卸载
├── requirements.txt            # Flask>=2.3.0, requests>=2.28.0
├── README.md                   # 项目说明 + 版本历史（V1.4.0 → V2.0.0）
├── AGENTS.md                   # 开发指引（部署、运行、调试）
├── UOSBetter_legacy.py         # 1.x 主程序备份（PySimpleGUI 版）
└── data/                       # APK、AppImage、主题文件、图标缓存

CQApkTools/
├── app.py                      # Flask 主入口，REST API
├── templates/
│   └── index.html              # 单页面模板
├── static/
│   ├── css/style.css           # 蓝白主题样式
│   ├── js/app.js               # 前端交互（文件选择、模态框）
│   └── vendor/                 # 本地静态资源（离线使用）
│       ├── bootstrap/          # Bootstrap 5.3 (CSS/JS)
│       └── bootstrap-icons/    # Bootstrap Icons (CSS/fonts)
├── models/
│   └── utils.py                # 常用工具函数（如 ADB 命令封装）
├── requirements.txt            # Flask>=3.0.0, easygui
├── README.md                   # 项目说明 + 版本历史
├── AGENTS.md                   # 开发指引
└── Project/                    # 打包资源（aapt.exe, AdbWinApi.dll 等）
```

## 3. 标签页重构（UOSBetter）

| 侧边栏顺序 | 标签页 ID | 内容 |
|-----------|----------|------|
| 1 | 软件组件 | 文件关联、文件管理器（Thunar/PCManFM/Nemo）、Wine 磁盘、多电脑共享、Steam、Barrier |
| 2 | 系统安全 | 内核版本管理、系统更新、磁盘检查 |
| 3 | 应用商店 | 星火商店、Flatpak、AppImage、软件源管理（APT + PIP）、Snap |
| 4 | 美化定制 | 主题字体、亮度调节、Windows 磁盘、图标主题、光标主题 |
| 5 | 桌面与菜单 | 快捷方式创建、右键菜单动态生成、桌面布局重置 |
| 6 | 系统服务 | 服务创建/启动/编辑/日志、服务开机自启管理 |
| 7 | 软件包安装 | YPK/TAR 安装卸载、虚拟环境模式 vs LOCAL 模式 |
| footer | 关于 | 应用信息 + 更新日志 + 系统信息 |

## 4. 核心功能实现

### 4.1 日志系统
- 后端 `LogCapture` 类（线程安全）劫持 `sys.stdout/stderr`，过滤掉 Flask/werkzeug 请求日志以避免噪声
- 逐行拆分 `print` 输出，通过 SSE 推送到前端（`/api/logs` 接口）
- 前端通过 `EventSource('/api/logs')` 建立 SSE 连接，`appendLog()` 追加到右侧日志面板
- 日志面板保留最近 1000 条，超出自动删除最早条目
- 显示完整命令执行结果：
  - `>>> 执行命令: <command>`
  - `<<< 返回结果: <output>`（若有）
  - `✓ <success message>` 或 `✗ <error message>`
- 支持折叠/展开日志面板，宽度记忆（通过 localStorage）
- 日志按钮为无边框纯图标，折叠状态显示双箭头方向

### 4.2 原生文件/文件夹/图标选择（关键改动）
#### UOSBetter（Linux）
- 后端新增三个 API 端点：
  - `/api/pick-file`：使用 `zenity --file-selection` 返回单个文件路径
    - 支持自定义标题（`title` 参数）、文件过滤器（`filter` 参数，逗号分隔扩展名）、默认目录（`default` 参数）
    - 返回 JSON：`{'success': True, 'message': '已选择', 'data': {'path': <full_path>}}`
  - `/api/pick-folder`：使用 `zenity --file-selection --directory` 返回文件夹路径
  - `/api/pick-icon`：使用 `zenity --file-selection` 并过滤图标类型（`.svg,.png,.xpm,.ico`），默认打开 `/usr/share/icons/hicolor/scalable/apps/`
- 前端统一函数：
  - `pickFile(inputId, filter = '')`：调用 `/api/pick-file?filter=<filter>`，成功后将路径填入指定 `inputId` 的文本框
  - `pickIcon(inputId)`：调用 `/api/pick-icon`，成功后将路径填入指定 `inputId` 的文本框
- 模板中所有文件选择按钮的 `onclick` 直接调用上述函数，**移除** 隐藏的 `<input type="file">` 元素
- 所有原生选择对话框均为系统原生 zenity 窗口，支持键盘导航、书签等特性
- 错误处理：若 zenity 不可用，返回错误信息并弹出提示模态框；若用户取消选择，则不修改原值

#### CQApkTools（Windows）
- 后端新增两个 API 端点：
  - `/api/pick-file`：使用 `easygui.fileopenbox` 返回单个文件路径
    - 支持自定义标题、默认路径、文件过滤器（如 `"*.apk|*.exe"`）
    - 返回 JSON 结构同上
  - `/api/pick-folder`：使用 `easygui.diropenbox` 返回文件夹路径
- 前端函数（与 UOSBetter 类似，但调用不同端点）：
  - `handleBrowseFile(btn)`：调用 `/api/pick-file`（无过滤器）
  - `handleBrowseFolder(btn)`：调用 `/api/pick-folder`
- 模板中所有文件选择按钮的 `onclick` 直接调用上述函数，**移除** 隐藏的 `<input type="file">` 元素
- 所有原生选择对话框均为系统原生 easygui 窗口（基于 Tkinter），支持键盘导航
- 错误处理：若 easygui 不可用，返回错误信息；若用户取消选择，则不修改原值

### 4.3 统一成功/失败反馈机制（关键改动）
#### UOSBetter
- 新增成功模态框 `#successModal`：
  - 标题栏：`bg-success text-white`（绿色背景、白色文字）
  - 标题图标：`<i class="bi bi-check-circle"></i>`
  - 标题文字：固定 “执行成功”
  - 内容区：`<p id="successModalMessage" class="mb-0"></p>`
  - 底部按钮：蓝色 primary 按钮 “确定”
- 前端函数：
  - `showSuccessModal(message)`：设置内容并显示模态框
  - `showErrorModal(message)`：复用错误模态框（红色背景、警告图标）
  - 初始化：在 `DOMContentLoaded` 中创建 `bootstrap.Modal` 实例
- 执行流程：
  - 前端通过 `doAction(action, params)` 发送 POST 到 `/api/action`
  - 后端返回 JSON：`{'success': bool, 'message': str, 'logout_required': bool, 'data': ...}`
  - 前端处理：
    - 若 `success` 为真：
      - 记录日志：`✓ ${message}`
      - 若 `logout_required` 为真：显示注销提示模态框
      - 否则：显示成功模态框（`showSuccessModal(message)`）
    - 若 `success` 为假：
      - 记录日志：`✗ ${message}`
      - 显示错误模态框（`showErrorModal(message)`）
  - 网络异常：捕获 `fetch` 异常，记录日志并显示网络错误模态框
- 所有操作按钮（通过 `data-action` 或 `doAction` 调用）均走此流程，确保成功/失败有明确视觉区分

#### CQApkTools
- 新增成功模态框 `#successModal`（结构同上）
- 前端函数：
  - `showSuccessModal(message)`：显示成功模态框
  - `showErrorModal(title, message)`：显示错误模态框（可自定义标题和内容）
- 执行流程：
  - 前端通过 `doAction(action, params)` 发送 POST 到 `/api/action`
  - 后端返回 JSON：`{'ok': bool, 'msg': str}`
  - 前端处理：
    - 若 `ok` 为真：
      - 记录日志：`✓ ${msg}`（通过 `appendLog`）
      - 显示成功模态框：`showSuccessModal(msg)`
    - 若 `ok` 为假：
      - 记录日志：`✗ ${msg}`
      - 显示错误模态框：`showErrorModal('操作失败', msg)`（或其他标题如‘提示’、‘网络错误’）
  - 网络异常：捕获异常，记录日志并显示网络错误模态框
- 关键改动：将原先成功操作也用错误模态框（红色标题）的做法改为使用专门的成功模态框（绿色标题），提升用户体验

### 4.4 UI 细节优化（关键改动）
- 字体尺寸统一缩小一号：
  - `.form-control, .form-select`：`font-size: 0.875rem`（原 1rem）
  - `.form-label`：`font-size: 0.8rem`（原 1rem）
  - 按钮（`.btn`、`.btn-outline-secondary` 等）：`font-size: 0.875rem`
  - 输入框组文字（`.input-group-text`）：在需要的地方也调整至 `0.875rem`
- 本地静态资源实现离线使用：
  - 所有 CSS/JS/字体均从 `static/vendor/` 加载，不依赖 CDN
  - 模板中使用 `{{ url_for('static', filename='vendor/...') }}` 生成路径
  - 资源包括：
    - Bootstrap 5.3.3：`bootstrap.min.css`、`bootstrap.bundle.min.js`
    - Bootstrap Icons：`bootstrap-icons.css`、`fonts/` 目录下的 woff2 字体
- 模态框统一使用 Bootstrap 5，居中显示，带淡入淡出动画
- 表单验证：前端提交前检查必填项，后端再次校验，双重保险
- 响应式布局：
  - 宽度 < 900px 自动折叠日志面板
  - 宽度 < 768px 侧边栏收缩为仅图标模式（左上角汉堡菜单可展开）

### 4.5 快捷方式创建修复（UOSBetter）
- 问题：原代码使用 `document.getElementById('sc_location')` 获取单选框值，但实际有两个同名单选框（桌面/应用程序菜单），导致总是获取第一个
- 解决：修改为 `document.querySelector('input[name="sc_location"]:checked')` 获取被选中的单选框值
- 模板中确保两个单选框都有 `name="sc_location"` 且 `value` 属性正确：
  - 桌面单选框：`<input class="form-check-input" type="radio" name="sc_location" id="sc_desktop" value="desktop" checked>`
  - 应用程序菜单单选框：`<input class="form-check-input" type="radio" name="sc_location" id="sc_applist" value="applist">`
- 后端路由 `/api/action` 的 `create_shortcut` 动作根据 `location` 参数（`desktop` 或 `applist`）生成 `.desktop` 文件到相应目录：
  - 桌面：`~/Desktop/`
  - 应用程序菜单：`~/.local/share/applications/`

### 4.6 其他功能细节
- 系统服务管理：
  - 后端 `manage_services()` 支持查询、启动、停止、重启、禁用、启用系统服务
  - 前端以卡片形式列出服务，每张卡片显示状态（运行中/已停止）和操作按钮
  - 新增 `_find_terminal()` 自动检测可用终端模块（支持 gnome-terminal、konsole、xfce4-terminal、deepin-terminal 等）
  - 查看服务日志时在新终端窗口中执行 `journalctl -u <service> -f`
- 软件包安装（YPK/TAR）：
  - 支持虚拟环境模式（隔离）和 LOCAL 模式（系统集成）
  - 前端通过 radio 按钮选择模式，后端根据模式执行不同的安装逻辑
  - 安装过程显示完整日志，成功后提示是否需要注销（如涉及系统服务或图标缓存更新）
- 主题和字体安装：
  - 主题安装后自动刷新 gsettings（如需要）
  - 字体安装后刷新 fontconfig 缓存
  - 两者安装完成后弹出提示：建议立即注销重新登录以使更改生效
- 关于页面：
  - 左侧列表显示：应用名称、版本号、作者、许可证
  - 右侧列表显示：更新日志（从 V1.4.0 到 V2.0.0 的所有版本条目）
  - 底部显示：系统信息（操作系统、内核版本、Python 版本等）

## 5. 依赖与环境要求

### UOSBetter（Linux）
- 系统要求：Ubuntu 20.04+/Deepin 20.5+/UOS 20+（其他发行版可能需要调整）
- 必要系统组件：
  - `zenity`：文件/文件夹/图标选择对话框
  - `pkexec`：权限提升后端
  - `systemd`：服务管理（大多数现代发行版默认安装）
  - `gsettings`：主题/字体应用（GNOME 基础）
- Python 依赖（见 `requirements.txt`）：
  - `Flask>=2.3.0`
  - `requests>=2.28.0`
- 可选依赖（增强功能）：
  - `python3-pip`：用于 PIP 包管理
  - `flatpak`：Flatpak 支持
  - `snapd`：Snap 支持
  - `wine`：Windows 程序运行

### CQApkTools（Windows）
- 系统要求：Windows 7+（推荐 Windows 10/11）
- 必要系统组件：
  - 无额外系统组件（易gui 基于 Tkinter，随 Python 自带）
- Python 依赖（见 `requirements.txt`）：
  - `Flask>=3.0.0`
  - `easygui`
- 可选依赖（增强功能）：
  - `adb`：Android 调试桥（需安装 Android Platform Tools）
  - `java`：运行某些需要 Java 的工具
  - `7z`：解压缩 APK（可选，内置有 aapt.exe）

## 6. 离线使用指南
1. 确保已将仓库完整克隆或下载到本地目录
2. 进入项目目录（UOSBetter 或 CQApkTools）
3. 安装 Python 依赖：`pip install -r requirements.txt`
4. （UOSBetter 仅需）确保系统已安装 `zenity` 和 `pkexec`
5. （CQApkTools 仅需）确保系统已安装 Python 且支持 Tkinter（通常随 Python 自带）
6. 启动服务：
   - UOSBetter：`python3 app.py` → 浏览器访�器访问 `http://127.0.0.1:55000`
   - CQApkTools：`python3 app.py` → 浏览器访问 `http://127.0.0.1:55500`
7. 所有界面资源（Bootstrap、图标）均从本地 `static/vendor/` 加载，**无需网络连接**
8. 文件选择等操作均使用系统原生 dialog（zenity/easygui），不依赖网络

## 7. 开发与调试指南
- 后端调试：查看终端输出（print 日志）或 `app.log`（如使用 nohup）
- 前端调试：浏览器开发者工具（F12）查看控制台错误和网络请求
- 常见问题：
  - “未找到 zenity”：请通过包管理器安装 zenity（例如 `sudo apt install zenity`）
  - “模态框不显示”：检查浏览器控制台是否有 Bootstrap 加载错误，确保已正确加载 `bootstrap.bundle.min.js`
  - “字体过小”：已调整为 0.875rem，如需进一步调整请修改 `static/css/style.css`
  - “快捷方式创建失败”：检查 `~/Desktop` 和 `~/.local/share/applications` 目录的写权限
- 版本控制：提交前请确保更新 `README.md` 和 `AGENTS.md` 中的版本号和变更日志
- 打包（可选）：
  - UOSBetter：可使用 PyInstaller 生成单文件可执行文件（需额外处理数据文件）
  - CQApkTools：已提供 PyInstaller 脚本（`Py2EXE.bat`）和 Inno Setup 脚本（`CQApkTools.iss`）

## 8. 版本历史（摘录自 README.md）
- V1.4.0：修复带目录的文件管理器设置为默认后无法打开的问题；补全 Win11 主题图标
- V1.5.0：删除部分图标以提升 XFCE 兼容性；修复带目录的文件管理器设置为默认后无法打开的问题
- V2.0.0：全面重构为 Flask Web 应用；左侧标签栏 + 右侧内容页布局；移除 PySimpleGUI 依赖；所有脚本功能改为 Python 实现；使用 pkexec 进行权限提升；AppImage 默认目录迁移至 `~/.local/share/UOSBetter/appimages/`；桌面图标改为动态生成；实时日志流显示；重新规划标签页
- V2.0.1（当前）：添加成功模态框区分操作结果；优化字体尺寸；实现离线使用（本地静态资源）；修复快捷方式创建位置错误；更新文档和依赖

## 9. 迁移 Checklist（已完成）
- [x] 移除 PySimpleGUI 依赖
- [x] 删除 `data/scripts/` 和 `data/desktops/` 静态文件
- [x] 所有 shell 脚本改为 Python `models/` 模块
- [x] 用 `pkexec` 替换全局 `sudo`（UOSBetter）
- [x] 蓝白主题替换暗色主题
- [x] 日志面板从底部移到右侧，支持折叠/展开
- [x] 恢复 README 版本历史
- [x] 关于页面重新设计
- [x] 添加专门成功模态框（绿色检查图标）
- [x] 成功操作使用成功模态框，失败操作使用错误模态框（红色警告图标）
- [x] 将字体尺寸缩小一号（.form-control: 0.875rem, .form-label: 0.8rem）
- [x] 实现离线使用：所有静态资源均从本地 static/vendor/ 加载
- [x] 修复快捷方式创建：使用 querySelector 获取被选中单选框值
- [x] 更新 AGENTS.md 和 README.md
- [x] 验证所有功能在离线状态下正常工作

## 10. 未来工作方向
- 增加操作确认弹窗（如删除、卸载重要组件）
- 日志面板支持关键字搜索和高亮
- 主题/字体安装后自动应用无需注销（如果技术可行）
- 增加深色主题切换选项（手动切换或跟随系统）
- 扩展 CQApkTools 功能：支持多设备同时管理、APK 反编译集成
- 探索使用 Tauri 或 Electron 打包成原生桌面应用（可选）
