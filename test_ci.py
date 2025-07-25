#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CI/CD测试脚本
用于验证项目配置是否正确
"""

import sys
import os

def test_imports():
    """测试关键模块导入"""
    print("🔍 测试模块导入...")
    
    try:
        import app
        print("✅ app.py 导入成功")
    except Exception as e:
        print(f"❌ app.py 导入失败: {e}")
        return False
    
    try:
        import data_loader
        print("✅ data_loader.py 导入成功")
    except Exception as e:
        print(f"❌ data_loader.py 导入失败: {e}")
        return False
    
    try:
        import stock_indicator
        print("✅ stock_indicator.py 导入成功")
    except Exception as e:
        print(f"❌ stock_indicator.py 导入失败: {e}")
        return False
    
    return True

def test_dependencies():
    """测试依赖包"""
    print("\n📦 测试依赖包...")
    
    required_packages = [
        'flask',
        'pandas', 
        'numpy',
        'plotly',
        'yfinance',
        'akshare',
        'requests',
        'urllib3'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def test_files():
    """测试必要文件"""
    print("\n📁 测试必要文件...")
    
    required_files = [
        'app.py',
        'data_loader.py', 
        'stock_indicator.py',
        'requirements.txt',
        'templates/index.html'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  缺少文件: {', '.join(missing_files)}")
        return False
    
    return True

def test_flask_app():
    """测试Flask应用"""
    print("\n🌐 测试Flask应用...")
    
    try:
        from app import app as flask_app
        print("✅ Flask应用创建成功")
        
        # 测试路由
        with flask_app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ 主页路由正常")
            else:
                print(f"❌ 主页路由异常: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask应用测试失败: {e}")
        return False
    
    return True

def main():
    """主测试函数"""
    print("=" * 50)
    print("🚀 股票技术指标分析系统 - CI/CD测试")
    print("=" * 50)
    
    tests = [
        ("模块导入", test_imports),
        ("依赖包", test_dependencies),
        ("必要文件", test_files),
        ("Flask应用", test_flask_app)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 测试: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} 测试失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！项目配置正确。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查配置。")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 