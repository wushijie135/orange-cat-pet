@echo off
chcp 65001 >nul
echo 正在打包橘橘桌宠，请稍候...
python -m PyInstaller --noconfirm --windowed --name "橘橘桌宠" ^
  --add-data "assets;assets" ^
  --exclude-module PySide6.QtWebEngineCore ^
  --exclude-module PySide6.QtWebEngineWidgets ^
  --exclude-module PySide6.QtWebEngineQuick ^
  --exclude-module PySide6.QtPdf ^
  --exclude-module PySide6.QtQml ^
  --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtQuick3D ^
  --exclude-module PySide6.Qt3DCore ^
  --exclude-module PySide6.QtMultimedia ^
  --exclude-module PySide6.QtCharts ^
  --exclude-module PySide6.QtDataVisualization ^
  --exclude-module PySide6.QtWebSockets ^
  --exclude-module PySide6.QtWebChannel ^
  --exclude-module PySide6.QtTest ^
  main.py
echo.
echo 打包完成，程序在 dist\橘橘桌宠\ 文件夹里，双击"橘橘桌宠.exe"即可运行。
pause
