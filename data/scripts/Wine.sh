#!/bin/bash

echo "开始安装 Wine"
sudo apt install -y wine
echo "Wine 安装成功！"

echo "正在安装 Wine 常用字体..."
sudo apt install -y fonts-wine
echo "字体安装成功！"

echo "正在安装 winetricks 并修复中文字体映射..."
sudo apt install -y winetricks
cd ~/.wine
winetricks fakechinese
echo "中文字体映射修复完成！"

echo "正在创建打开方式链接..."
filepath="/usr/share/applications/Wine.desktop"
sudo rm -f $filepath
sudo cat > $filepath <<EOF
[Desktop Entry]
Categories=System;
Comment=用于打开EXE
Encoding=UTF-8
Exec=wine %U
Icon=wine
MimeType=exe
Name=Wine
StartupWMClass=Wine
Terminal=false
Type=Application
EOF
echo "Wine 打开方式链接创建成功！"
