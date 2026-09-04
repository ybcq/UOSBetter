#!/bin/bash
# 挂载 Wine 的 C 盘为虚拟磁盘

REAL_HOME="$HOME"
WINE_C="$REAL_HOME/.wine/drive_c"
MOUNT_POINT="/media/$(whoami)/Wine-C"

# 检查 Wine C 盘是否存在
if [ ! -d "$WINE_C" ]; then
    echo "❌ 未找到 Wine C 盘：$WINE_C"
    echo "   请先运行 winecfg 或任意 Wine 程序初始化 Wine 环境。"
    exit 1
fi

# 如果挂载点已存在且被占用，先卸载
if mountpoint -q "$MOUNT_POINT"; then
    echo "卸载旧的挂载..."
    sudo umount "$MOUNT_POINT"
fi

sudo mkdir -p "$MOUNT_POINT"
sudo mount --bind "$WINE_C" "$MOUNT_POINT"

echo "✅ 挂载成功！"
echo "📍 文件管理器侧边栏现在应出现 'Wine-C' 磁盘。"
echo "🔴 如需卸载：sudo umount $MOUNT_POINT"