#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows阿里云服务器部署脚本
用于打包和部署股票技术指标分析系统
"""

import os
import sys
import subprocess
import shutil
import zipfile
from datetime import datetime

def create_deployment_package():
    """创建部署包"""
    print("=" * 60)
    print("📦 创建Windows部署包")
    print("=" * 60)
    
    # 创建部署目录
    deploy_dir = "deploy_windows"
    if os.path.exists(deploy_dir):
        shutil.rmtree(deploy_dir)
    os.makedirs(deploy_dir)
    
    # 需要包含的文件和目录
    files_to_include = [
        'app.py',
        'data_loader.py',
        'stock_indicator.py',
        'requirements.txt',
        'README.md',
        'templates/',
        'static/',
        'logs/',
        'data/'
    ]
    
    # 复制文件
    for item in files_to_include:
        src = item
        dst = os.path.join(deploy_dir, item)
        
        if os.path.isfile(src):
            # 复制文件
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✅ 复制文件: {src}")
        elif os.path.isdir(src):
            # 复制目录
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
            print(f"✅ 复制目录: {src}")
    
    # 创建启动脚本
    create_startup_scripts(deploy_dir)
    
    # 创建配置文件
    create_config_files(deploy_dir)
    
    # 创建部署说明
    create_deployment_guide(deploy_dir)
    
    print(f"\n✅ 部署包已创建: {deploy_dir}")
    return deploy_dir

def create_startup_scripts(deploy_dir):
    """创建启动脚本"""
    
    # Windows批处理脚本
    bat_content = '''@echo off
echo 启动股票技术指标分析系统...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\\Scripts\\activate.bat

REM 安装依赖
echo 安装依赖包...
pip install -r requirements.txt

REM 启动应用
echo 启动Web应用...
echo 访问地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo.
python app.py

pause
'''
    
    with open(os.path.join(deploy_dir, 'start.bat'), 'w', encoding='utf-8') as f:
        f.write(bat_content)
    
    # PowerShell脚本
    ps_content = '''# 股票技术指标分析系统启动脚本
Write-Host "启动股票技术指标分析系统..." -ForegroundColor Green
Write-Host ""

# 检查Python
try {
    python --version | Out-Null
} catch {
    Write-Host "错误: 未找到Python，请先安装Python 3.7+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查虚拟环境
if (-not (Test-Path "venv")) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    python -m venv venv
}

# 激活虚拟环境
Write-Host "激活虚拟环境..." -ForegroundColor Yellow
& "venv\\Scripts\\Activate.ps1"

# 安装依赖
Write-Host "安装依赖包..." -ForegroundColor Yellow
pip install -r requirements.txt

# 启动应用
Write-Host "启动Web应用..." -ForegroundColor Green
Write-Host "访问地址: http://localhost:5000" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""
python app.py

Read-Host "按回车键退出"
'''
    
    with open(os.path.join(deploy_dir, 'start.ps1'), 'w', encoding='utf-8') as f:
        f.write(ps_content)

def create_config_files(deploy_dir):
    """创建配置文件"""
    
    # 生产环境配置
    config_content = '''# 生产环境配置文件
import os

class Config:
    # 基本配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DEBUG = False
    
    # 数据库配置（如果需要）
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///stock_analysis.db'
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
    # 缓存配置
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # 安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # 性能配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # 股票数据配置
    YFINANCE_TIMEOUT = 30
    DATA_CACHE_TIMEOUT = 3600  # 1小时
'''

    with open(os.path.join(deploy_dir, 'config.py'), 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    # 创建日志目录
    os.makedirs(os.path.join(deploy_dir, 'logs'), exist_ok=True)
    
    # 创建数据目录
    os.makedirs(os.path.join(deploy_dir, 'data'), exist_ok=True)

def create_deployment_guide(deploy_dir):
    """创建部署说明文档"""
    
    guide_content = '''# Windows阿里云服务器部署指南

## 系统要求

- Windows Server 2016/2019/2022
- Python 3.7+
- 至少2GB内存
- 至少10GB磁盘空间

## 快速部署

### 1. 上传文件到服务器
将部署包上传到阿里云Windows服务器

### 2. 解压部署包
```cmd
# 解压到指定目录
tar -xzf stock-analysis-windows.zip
cd stock-analysis-windows
```

### 3. 启动应用
```cmd
# 使用批处理脚本启动
start.bat

# 或使用PowerShell脚本启动
powershell -ExecutionPolicy Bypass -File start.ps1
```

### 4. 访问应用
打开浏览器访问: http://服务器IP:5000

## 生产环境部署

### 1. 使用Gunicorn（推荐）
```cmd
# 安装gunicorn
pip install gunicorn

# 启动服务
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. 使用Windows服务
```cmd
# 安装nssm
# 下载nssm并安装

# 创建Windows服务
nssm install StockAnalysis "C:\\path\\to\\python.exe" "C:\\path\\to\\app.py"
nssm set StockAnalysis AppDirectory "C:\\path\\to\\app"
nssm start StockAnalysis
```

### 3. 配置反向代理（可选）
使用Nginx或IIS作为反向代理

## 防火墙配置

在Windows防火墙中开放端口5000：
```cmd
netsh advfirewall firewall add rule name="Stock Analysis" dir=in action=allow protocol=TCP localport=5000
```

## 阿里云安全组配置

1. 登录阿里云控制台
2. 进入ECS实例管理
3. 配置安全组规则：
   - 协议类型：TCP
   - 端口范围：5000/5000
   - 授权对象：0.0.0.0/0（或指定IP）

## 监控和维护

### 1. 日志查看
```cmd
# 查看应用日志
type logs\\app.log

# 查看系统日志
eventvwr
```

### 2. 性能监控
- 使用Windows任务管理器监控CPU和内存
- 使用阿里云监控服务

### 3. 备份策略
- 定期备份数据目录
- 备份配置文件
- 使用阿里云快照功能

## 故障排除

### 1. 端口被占用
```cmd
# 查看端口占用
netstat -ano | findstr :5000

# 结束进程
taskkill /PID <进程ID> /F
```

### 2. Python环境问题
```cmd
# 重新创建虚拟环境
rmdir /s venv
python -m venv venv
venv\\Scripts\\activate.bat
pip install -r requirements.txt
```

### 3. 权限问题
确保运行用户有足够的权限访问应用目录

## 联系支持

如遇到问题，请查看日志文件或联系技术支持。
'''
    
    with open(os.path.join(deploy_dir, 'DEPLOYMENT_GUIDE.md'), 'w', encoding='utf-8') as f:
        f.write(guide_content)

def create_zip_package(deploy_dir):
    """创建ZIP压缩包"""
    print("\n📦 创建ZIP压缩包...")
    
    zip_filename = f"stock-analysis-windows-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
                print(f"✅ 添加文件: {arcname}")
    
    print(f"\n✅ ZIP包已创建: {zip_filename}")
    return zip_filename

def main():
    """主函数"""
    print("🚀 Windows阿里云服务器部署工具")
    print("=" * 60)
    
    try:
        # 创建部署包
        deploy_dir = create_deployment_package()
        
        # 创建ZIP包
        zip_filename = create_zip_package(deploy_dir)
        
        print("\n" + "=" * 60)
        print("🎉 部署包创建完成！")
        print("=" * 60)
        print(f"📁 部署目录: {deploy_dir}")
        print(f"📦 ZIP包: {zip_filename}")
        print("\n📋 下一步操作:")
        print("1. 将ZIP包上传到阿里云Windows服务器")
        print("2. 解压ZIP包")
        print("3. 运行 start.bat 启动应用")
        print("4. 访问 http://服务器IP:5000")
        
    except Exception as e:
        print(f"❌ 创建部署包时出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 