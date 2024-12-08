#!/bin/bash

# 0. 清理旧的构建目录
rm -rf dist/installers
rm -rf python
rm -rf assets

# 1. 准备环境
python scripts/packaging/prepare.py

# 2. 构建前端
pnpm build

# 3. 确保目录存在
mkdir -p python
mkdir -p assets

# 4. 安装 electron 依赖
cd electron && npm install && cd ..

# 5. 打包应用
if [ "$1" == "windows" ]; then
    pnpm package:windows
elif [ "$1" == "mac" ]; then
    pnpm package:mac
else
    pnpm package
fi 