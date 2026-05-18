#!/bin/bash

echo "Begin to Install Deepin-Wine"
sudo apt install deepin-wine
echo "Install Deepin-Wine Sucessfully!"

echo "Begin to Write Openlink"
filepath="/usr/share/applications/Deepin-Wine.desktop"
rm $filepath
echo "[Desktop Entry]" > $filepath
cat > $filepath<<EOF
[Desktop Entry]
Categories=System;
Comment=用于打开EXE
Encoding=UTF-8
Exec=deepin-wine %U
Icon=deepin-wine-assist
MimeType=exe
Name=Deepin-Wine
StartupWMClass=Deepin-Wine
Terminal=false
Type=Application
X-Deepin-Vendor=user-custom
EOF
echo "Write Deepin-Wine Openlink Sucessfully!"