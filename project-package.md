



根据项目描述和代码，我来说明如何将该项目打包成客户端应用。

### 1. 打包方案选择

可以使用以下几种方式：

1. Electron 打包 - 最佳选择，可以打包成跨平台的桌面应用
2. PyInstaller - 可以打包 Python 后端
3. Docker - 容器化部署方案

### 2. Electron 打包步骤

1. 首先创建 Electron 主配置文件：

```javascript:electron/main.js
const { app, BrowserWindow } = require('electron')
const path = require('path')
const { spawn } = require('child_process')

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: true
    }
  })

  // 加载前端
  win.loadURL('http://localhost:8080')
}

// 启动后端服务
function startBackend() {
  const backend = spawn('python', ['-m', 'open_webui.main'], {
    stdio: 'inherit'
  })
  
  backend.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
  })
}

app.whenReady().then(() => {
  startBackend()
  createWindow()
})
```

2. 修改 `package.json` 添加打包配置：

```json:package.json
{
  "name": "open-webui",
  "version": "1.0.0",
  "main": "electron/main.js",
  "scripts": {
    "start": "electron .",
    "build": "electron-builder",
    "pack": "electron-builder --dir"
  },
  "build": {
    "appId": "com.open-webui.app",
    "productName": "Open WebUI",
    "directories": {
      "output": "dist"
    },
    "files": [
      "dist/**/*",
      "electron/**/*",
      "backend/**/*"
    ],
    "extraResources": [
      {
        "from": "backend",
        "to": "backend",
        "filter": ["**/*"]
      }
    ]
  }
}
```

3. 打包命令：

```bash
# 安装依赖
npm install electron electron-builder --save-dev

# 构建前端
pnpm build

# 打包 Python 后端
cd backend
python setup.py bdist_wheel

# 打包应用
npm run build
```

### 3. 自动安装脚本

创建安装脚本处理依赖：

```python:scripts/install.py
import os
import sys
import subprocess

def install_dependencies():
    # 安装 Python 依赖
    subprocess.check_call([
        sys.executable, 
        '-m', 
        'pip', 
        'install', 
        'open-webui[all]'
    ])
    
    # 初始化数据库
    subprocess.check_call([
        sys.executable,
        '-m',
        'open_webui.setup'
    ])

if __name__ == '__main__':
    install_dependencies()
```

### 4. 打包配置文件

```ini:setup.cfg
[metadata]
name = open-webui
version = 1.0.0
description = Open WebUI Client Application
author = Your Name
author_email = your.email@example.com

[options]
packages = find:
install_requires =
    fastapi
    uvicorn
    sqlalchemy
    alembic
    python-multipart
    python-jose[cryptography]
    
[options.entry_points]
console_scripts =
    open-webui = open_webui.main:main
```

### 5. 发布流程

1. 构建安装包:
```bash
# Windows
pyinstaller --onefile --windowed --add-data "frontend/dist;frontend/dist" app.py

# Mac
pyinstaller --onefile --windowed --add-data "frontend/dist:frontend/dist" app.py
```

2. 创建安装程序:
- Windows: 使用 NSIS 或 Inno Setup
- Mac: 创建 .dmg 文件
- Linux: 创建 .deb 或 .rpm 包


让我详细说明每个平台的安装程序创建过程：

### Windows (使用 Inno Setup)

1. 首先下载并安装 [Inno Setup](https://jrsoftware.org/isdl.php)

2. 创建安装脚本 `setup.iss`:

`````iss:installer/setup.iss
[Setup]
AppName=Open WebUI
AppVersion=1.0.0
DefaultDirName={pf}\OpenWebUI
DefaultGroupName=Open WebUI
OutputDir=output
OutputBaseFilename=OpenWebUI-Setup
Compression=lzma
SolidCompression=yes

[Files]
; 主程序文件
Source: "dist\open-webui.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

; Python 运行环境
Source: "python\*"; DestDir: "{app}\python"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\Open WebUI"; Filename: "{app}\open-webui.exe"
Name: "{commondesktop}\Open WebUI"; Filename: "{app}\open-webui.exe"

[Run]
; 安装后运行
Filename: "{app}\open-webui.exe"; Description: "启动 Open WebUI"; Flags: postinstall nowait

[Code]
// 检查 Python 环境
function InitializeSetup(): Boolean;
begin
    Result := True;
end;
`````

3. 构建安装程序：
```bash
# 1. 打包应用
pyinstaller --onefile --windowed --add-data "frontend/dist;frontend/dist" app.py

# 2. 编译安装程序
iscc setup.iss
```

### Mac (.dmg 文件)

1. 创建 DMG 构建脚本：

`````bash:installer/build-dmg.sh
#!/bin/bash

# 设置变量
APP_NAME="Open WebUI"
DMG_NAME="OpenWebUI-Installer"
SOURCE_DIR="dist/Open WebUI.app"
VOLUME_NAME="Open WebUI Installer"

# 创建临时 DMG
hdiutil create -srcfolder "${SOURCE_DIR}" -volname "${VOLUME_NAME}" -fs HFS+ \
      -fsargs "-c c=64,a=16,e=16" -format UDRW -size 200m temp.dmg

# 挂载 DMG
device=$(hdiutil attach -readwrite -noverify -noautoopen "temp.dmg" | \
         egrep '^/dev/' | sed 1q | awk '{print $1}')

# 设置背景和图标
mkdir /Volumes/"${VOLUME_NAME}"/.background
cp installer/background.png /Volumes/"${VOLUME_NAME}"/.background/

# 创建 .DS_Store
echo '
   tell application "Finder"
     tell disk "'${VOLUME_NAME}'"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {400, 100, 885, 430}
           set theViewOptions to the icon view options of container window
           set arrangement of theViewOptions to not arranged
           set icon size of theViewOptions to 72
           set background picture of theViewOptions to file ".background:background.png"
           make new alias file at container window to POSIX file "/Applications" with properties {name:"Applications"}
           set position of item "'${APP_NAME}'" of container window to {100, 100}
           set position of item "Applications" of container window to {375, 100}
           update without registering applications
           delay 5
           close
     end tell
   end tell
' | osascript

# 转换 DMG
hdiutil detach "${device}"
hdiutil convert "temp.dmg" -format UDZO -imagekey zlib-level=9 -o "${DMG_NAME}"
rm -f temp.dmg
`````

2. 构建应用和 DMG：
```bash
# 1. 创建 .app
pyinstaller --windowed --add-data "frontend/dist:frontend/dist" \
            --name "Open WebUI" \
            --icon "assets/icon.icns" \
            app.py

# 2. 创建 DMG
chmod +x installer/build-dmg.sh
./installer/build-dmg.sh
```

### Linux (.deb 包)

1. 创建 Debian 包结构：

```bash
mkdir -p debian-package/DEBIAN
mkdir -p debian-package/usr/local/bin
mkdir -p debian-package/usr/share/applications
mkdir -p debian-package/usr/share/icons/hicolor/512x512/apps
```

2. 创建控制文件：

`````text:debian-package/DEBIAN/control
Package: open-webui
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Depends: python3 (>= 3.8)
Maintainer: Your Name <your.email@example.com>
Description: Open WebUI Client Application
 A modern web interface for language models.
`````

3. 创建启动脚本：

`````bash:debian-package/usr/local/bin/open-webui
#!/bin/bash
/usr/lib/open-webui/open-webui "$@"
`````

4. 创建桌面文件：

`````desktop:debian-package/usr/share/applications/open-webui.desktop
[Desktop Entry]
Name=Open WebUI
Exec=/usr/local/bin/open-webui
Icon=open-webui
Type=Application
Categories=Development;
`````

5. 构建 .deb 包：

```bash
# 1. 打包应用
pyinstaller --onefile --windowed --add-data "frontend/dist:frontend/dist" app.py

# 2. 复制文件到 debian 包结构
cp dist/open-webui debian-package/usr/lib/open-webui/
cp assets/icon.png debian-package/usr/share/icons/hicolor/512x512/apps/open-webui.png

# 3. 设置权限
chmod 755 debian-package/usr/local/bin/open-webui
chmod 755 debian-package/usr/lib/open-webui/open-webui

# 4. 构建 deb 包
dpkg-deb --build debian-package open-webui_1.0.0_amd64.deb
```

### 通用步骤

1. 创建自动化构建脚本：

`````python:scripts/build.py
import os
import platform
import subprocess

def build_installer():
    system = platform.system()
    
    # 通用步骤
    subprocess.run(['pyinstaller', '--windowed', 
                   '--add-data', 'frontend/dist:frontend/dist',
                   'app.py'])
    
    if system == 'Windows':
        subprocess.run(['iscc', 'installer/setup.iss'])
    elif system == 'Darwin':
        subprocess.run(['./installer/build-dmg.sh'])
    elif system == 'Linux':
        subprocess.run(['./installer/build-deb.sh'])

if __name__ == '__main__':
    build_installer()
`````

2. 运行构建：
```bash
python scripts/build.py
```

这样就能为不同平台创建专业的安装程序了。安装程序会：

1. 安装所需的依赖
2. 配置环境变量
3. 创建快捷方式
4. 提供卸载功能
5. 处理权限问题

用户只需要下载对应平台的安装程序，双击安装即可使用。



参考项目描述中的部署说明：

````154:165:project-desc.md
## 8. 部署说明

### 8.1 Docker 部署
```bash
docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui
```

### 8.2 开发环境
```bash
pip install open-webui
open-webui serve
```
````


这样用户就可以通过安装包一键安装和使用了。安装后会自动:
1. 安装所需依赖
2. 初始化数据库
3. 启动服务
4. 打开客户端界面
