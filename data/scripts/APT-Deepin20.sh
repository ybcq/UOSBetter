#!/bin/bash

# 定义官方源
OFFICIAL_SOURCE="deb https://community-packages.deepin.com/deepin apricot main contrib non-free"
SOURCES_FILE="/etc/apt/sources.list"
BACKUP_FILE="$SOURCES_FILE.bak"

# 检查管理员权限
if [ "$(id -u)" -ne 0 ]; then
    echo "请以管理员权限运行此脚本。"
    exit 1
fi

# 备份原始文件
sudo cp "$SOURCES_FILE" "$BACKUP_FILE"
echo "已备份原 sources.list 到：$BACKUP_FILE"

# 写入官方源
echo "$OFFICIAL_SOURCE" | sudo tee "$SOURCES_FILE" >/dev/null
echo "已将 sources.list 更新为深度源。"
cat "$SOURCES_FILE"
