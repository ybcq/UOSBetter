#!/bin/bash
# ====================================================
# 在 ~/WinLike 中创建 Windows 风格映射，并挂载为“磁盘”
# ====================================================

# ---------- 1. 定义路径 ----------
# 获取当前用户真实主目录（防止 sudo 环境变量丢失）
REAL_HOME="$HOME"
WIN_DRIVE="$REAL_HOME/WinLike"
MOUNT_POINT="/media/$(whoami)/WinLike"  # 挂载到 /media/用户名/ 下，更像磁盘

# ---------- 2. 创建目录并清空（防止旧链接干扰） ----------
echo "📁 正在创建目录：$WIN_DRIVE"
rm -rf "$WIN_DRIVE"          # 如果存在就删掉重来（确保干净）
mkdir -p "$WIN_DRIVE"

# ---------- 3. 创建软链接（核心映射） ----------
echo "🔗 正在创建 Windows 风格映射..."
ln -s /home "$WIN_DRIVE/Users"
ln -s /usr "$WIN_DRIVE/Program Files"
ln -s /opt "$WIN_DRIVE/Program Files (x86)"
ln -s /etc "$WIN_DRIVE/Windows"
ln -s /usr/bin "$WIN_DRIVE/System32"
ln -s /usr/share/applications "$WIN_DRIVE/开始菜单（系统）"

# 用户级开始菜单（自动识别）
USER_APPS="$REAL_HOME/.local/share/applications"
if [ ! -d "$USER_APPS" ]; then
    echo "📁 创建用户开始菜单目录：$USER_APPS"
    mkdir -p "$USER_APPS"
fi
ln -s "$USER_APPS" "$WIN_DRIVE/开始菜单（用户）"

# 额外赠送：把常见的“下载/文档/桌面”也映射进去（Windows 用户狂喜）
# ln -s "$REAL_HOME/Downloads" "$WIN_DRIVE/下载"
# ln -s "$REAL_HOME/Documents" "$WIN_DRIVE/文档"
# ln -s "$REAL_HOME/Desktop" "$WIN_DRIVE/桌面"
# ln -s "$REAL_HOME/Pictures" "$WIN_DRIVE/图片"
# ln -s "$REAL_HOME/Music" "$WIN_DRIVE/音乐"
# ln -s "$REAL_HOME/Videos" "$WIN_DRIVE/视频"

# ---------- 4. 关键步骤：把这个文件夹挂载成“磁盘” ----------
echo "========================================="
echo "💾 准备将 $WIN_DRIVE 挂载为虚拟磁盘..."
echo "目标挂载点：$MOUNT_POINT"
read -p "是否执行挂载？(需要 sudo 权限) (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 如果挂载点已存在且被占用，先卸载
    if mountpoint -q "$MOUNT_POINT"; then
        echo "卸载旧的挂载..."
        sudo umount "$MOUNT_POINT"
    fi
    
    sudo mkdir -p "$MOUNT_POINT"
    sudo mount --bind "$WIN_DRIVE" "$MOUNT_POINT"
    
    echo "✅ 挂载成功！"
    echo "📍 现在打开你的文件管理器（如 Nautilus/Dolphin），"
    echo "   在左侧边栏应该能看到一个名为 'WinLike' 的磁盘设备。"
    echo "   点击它，就能看到 Users、Program Files 等文件夹了。"
fi

# ---------- 5. 提示持久化（可选） ----------
echo "========================================="
echo "🎉 全部完成！"
echo "📂 原始文件夹路径：$WIN_DRIVE"
echo "💾 挂载磁盘路径：$MOUNT_POINT"
echo ""
echo "🔴 如需开机自动挂载，请将以下行添加到 /etc/fstab："
echo "   $WIN_DRIVE  $MOUNT_POINT  none  bind  0  0"
echo ""
echo "🔴 如需卸载该磁盘，执行：sudo umount $MOUNT_POINT"
echo "========================================="