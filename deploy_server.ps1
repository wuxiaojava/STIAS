# Windows服务器部署脚本
# 用于手动部署股票技术指标分析系统

param(
    [string]$AppDir = "C:\STIAS",
    [string]$ServiceName = "STIAS-StockAnalysis",
    [string]$PythonPath = "C:\Python39\python.exe"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "股票技术指标分析系统 - Windows部署脚本" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "错误: 需要管理员权限运行此脚本" -ForegroundColor Red
    exit 1
}

# 停止现有服务
Write-Host "`n1. 检查现有服务..." -ForegroundColor Yellow
if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Write-Host "停止现有服务: $ServiceName" -ForegroundColor Yellow
    Stop-Service -Name $ServiceName -Force
    Start-Sleep -Seconds 3
}

# 创建应用目录
Write-Host "`n2. 创建应用目录..." -ForegroundColor Yellow
if (!(Test-Path $AppDir)) {
    New-Item -ItemType Directory -Path $AppDir -Force
    Write-Host "创建目录: $AppDir" -ForegroundColor Green
} else {
    Write-Host "目录已存在: $AppDir" -ForegroundColor Green
}

# 检查Python环境
Write-Host "`n3. 检查Python环境..." -ForegroundColor Yellow
if (!(Test-Path $PythonPath)) {
    Write-Host "错误: Python未找到，请安装Python 3.9+到 $PythonPath" -ForegroundColor Red
    exit 1
}

$pythonVersion = & $PythonPath --version
Write-Host "Python版本: $pythonVersion" -ForegroundColor Green

# 创建虚拟环境
Write-Host "`n4. 设置Python虚拟环境..." -ForegroundColor Yellow
$venvPath = "$AppDir\venv"
if (!(Test-Path $venvPath)) {
    Write-Host "创建虚拟环境..." -ForegroundColor Yellow
    & $PythonPath -m venv $venvPath
    Write-Host "虚拟环境已创建: $venvPath" -ForegroundColor Green
} else {
    Write-Host "虚拟环境已存在: $venvPath" -ForegroundColor Green
}

# 激活虚拟环境并安装依赖
Write-Host "`n5. 安装Python依赖..." -ForegroundColor Yellow
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    pip install --upgrade pip
    if (Test-Path "$AppDir\requirements.txt") {
        pip install -r "$AppDir\requirements.txt"
        Write-Host "Python依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "警告: requirements.txt未找到" -ForegroundColor Yellow
    }
} else {
    Write-Host "错误: 虚拟环境激活脚本未找到" -ForegroundColor Red
    exit 1
}

# 创建启动脚本
Write-Host "`n6. 创建启动脚本..." -ForegroundColor Yellow
$startScriptContent = @"
@echo off
cd /d $AppDir
call venv\Scripts\activate.bat
python app.py
"@
Set-Content -Path "$AppDir\start_service.bat" -Value $startScriptContent -Encoding ASCII
Write-Host "启动脚本已创建: $AppDir\start_service.bat" -ForegroundColor Green

# 下载并安装NSSM
Write-Host "`n7. 设置Windows服务..." -ForegroundColor Yellow
$nssmPath = "C:\nssm\nssm.exe"
if (!(Test-Path $nssmPath)) {
    Write-Host "下载NSSM..." -ForegroundColor Yellow
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = "C:\nssm.zip"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath "C:\nssm" -Force
        Remove-Item $nssmZip
        Write-Host "NSSM下载完成" -ForegroundColor Green
    } catch {
        Write-Host "错误: NSSM下载失败" -ForegroundColor Red
        exit 1
    }
}

# 安装Windows服务
Write-Host "安装Windows服务..." -ForegroundColor Yellow
try {
    # 如果服务已存在，先删除
    if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
        & $nssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    }
    
    # 安装新服务
    & $nssmPath install $ServiceName "$AppDir\start_service.bat"
    & $nssmPath set $ServiceName AppDirectory $AppDir
    & $nssmPath set $ServiceName Description "股票技术指标分析系统"
    & $nssmPath set $ServiceName Start SERVICE_AUTO_START
    
    Write-Host "Windows服务安装完成" -ForegroundColor Green
} catch {
    Write-Host "错误: 服务安装失败" -ForegroundColor Red
    exit 1
}

# 启动服务
Write-Host "`n8. 启动服务..." -ForegroundColor Yellow
try {
    Start-Service -Name $ServiceName
    Write-Host "服务启动中..." -ForegroundColor Yellow
    
    # 等待服务启动
    Start-Sleep -Seconds 10
    
    # 检查服务状态
    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq "Running") {
        Write-Host "✅ 部署成功！服务正在运行" -ForegroundColor Green
        Write-Host "访问地址: http://localhost:5000" -ForegroundColor Cyan
    } else {
        Write-Host "❌ 服务启动失败，状态: $($service.Status)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "错误: 服务启动失败" -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "部署完成！" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

# 显示服务信息
Write-Host "`n服务信息:" -ForegroundColor Cyan
Write-Host "服务名称: $ServiceName" -ForegroundColor White
Write-Host "安装路径: $AppDir" -ForegroundColor White
Write-Host "访问地址: http://localhost:5000" -ForegroundColor White

Write-Host "`n管理命令:" -ForegroundColor Cyan
Write-Host "查看状态: Get-Service -Name '$ServiceName'" -ForegroundColor White
Write-Host "启动服务: Start-Service -Name '$ServiceName'" -ForegroundColor White
Write-Host "停止服务: Stop-Service -Name '$ServiceName'" -ForegroundColor White
Write-Host "重启服务: Restart-Service -Name '$ServiceName'" -ForegroundColor White 