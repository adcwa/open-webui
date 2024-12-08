import os
import sys
import subprocess
import shutil
import venv

def prepare_python_env():
    """准备 Python 环境和依赖"""
    # 创建虚拟环境
    venv_path = os.path.join('python', 'venv')
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)
    
    # 使用 venv 模块创建虚拟环境
    builder = venv.EnvBuilder(with_pip=True, symlinks=False, clear=True)
    builder.create(venv_path)
    
    # 安装依赖
    pip_path = os.path.join(venv_path, 'Scripts' if os.name == 'nt' else 'bin', 'pip')
    # 升级 pip
    subprocess.run([pip_path, 'install', '--upgrade', 'pip'])
    
    subprocess.run([pip_path, 'install', '-r', 'backend/requirements.txt'])
    
    # 安装项目包
    subprocess.run([pip_path, 'install', '.'])

def prepare_assets():
    """准备打包所需的资源文件"""
    os.makedirs('assets', exist_ok=True)
    
    # 清理旧的图标文件
    if os.path.exists('assets/icon.ico'):
        os.remove('assets/icon.ico')
    if os.path.exists('assets/icon.icns'):
        os.remove('assets/icon.icns')
    
    # 复制图标文件
    if not os.path.exists('assets/icon.ico'):
        shutil.copy('src/assets/icon.png', 'assets/icon.ico')
    if not os.path.exists('assets/icon.icns'):
        shutil.copy('src/assets/icon.png', 'assets/icon.icns')

if __name__ == '__main__':
    # 确保目录干净
    if os.path.exists('python'):
        shutil.rmtree('python')
    if os.path.exists('assets'):
        shutil.rmtree('assets')
    
    prepare_python_env()
    prepare_assets() 