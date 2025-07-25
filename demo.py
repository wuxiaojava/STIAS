#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票技术指标分析系统 - 演示脚本
用于测试和演示指标计算功能
"""

import pandas as pd
import numpy as np
from stock_indicator import StockIndicator
from data_loader import DataLoader
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def demo_basic_usage():
    """演示基本使用方法"""
    print("=" * 60)
    print("股票技术指标分析系统 - 基本使用演示")
    print("=" * 60)
    
    # 创建数据加载器
    loader = DataLoader()
    
    # 获取示例数据
    print("正在获取示例数据...")
    stock_data, index_data = loader.get_sample_data()
    
    if stock_data.empty or index_data.empty:
        print("❌ 无法获取示例数据，请检查网络连接")
        return
    
    print(f"✅ 成功获取数据:")
    print(f"   股票数据: {len(stock_data)} 条记录")
    print(f"   指数数据: {len(index_data)} 条记录")
    
    # 创建指标计算器
    indicator = StockIndicator(stock_data, index_data)
    
    # 计算所有指标
    print("\n正在计算技术指标...")
    results = indicator.calculate_all_indicators()
    
    print("✅ 指标计算完成")
    
    # 获取摘要信息
    summary = indicator.get_summary()
    
    print("\n📊 当前状态摘要:")
    print(f"   当前价格: ${summary['current_price']:.2f}")
    print(f"   中线趋势: {summary['mid_trend_value']:.2f}")
    print(f"   V11指标: {summary['v11_value']:.2f}")
    print(f"   V12指标: {summary['v12_value']:.2f}")
    print(f"   趋势强度: {summary['trend_strength']}")
    print(f"   买入信号: {'是' if summary['buy_signal_active'] else '否'}")
    print(f"   卖出信号: {'是' if summary['sell_signal_active'] else '否'}")
    print(f"   超级买入: {'是' if summary['super_buy_signal_active'] else '否'}")

def demo_signals():
    """演示信号分析"""
    print("\n" + "=" * 60)
    print("买卖信号分析演示")
    print("=" * 60)
    
    # 获取数据
    loader = DataLoader()
    stock_data, index_data = loader.get_sample_data()
    
    if stock_data.empty or index_data.empty:
        print("❌ 无法获取数据")
        return
    
    # 计算指标
    indicator = StockIndicator(stock_data, index_data)
    indicator.calculate_all_indicators()
    
    # 获取信号
    signals = indicator.get_signals()
    
    print("📈 信号统计:")
    print(f"   买入信号总数: {signals['buy_signals'].sum()}")
    print(f"   卖出信号总数: {signals['sell_signals'].sum()}")
    print(f"   超级买入信号总数: {signals['super_buy_signals'].sum()}")
    
    # 显示最近的信号
    print("\n🔔 最近10个信号:")
    dates = signals['buy_signals'].index
    signal_count = 0
    
    for i in range(len(dates) - 1, max(0, len(dates) - 11), -1):
        date = dates[i].strftime('%Y-%m-%d')
        if signals['buy_signals'].iloc[i]:
            print(f"   {date}: 🟢 买入信号 - 主力进")
            signal_count += 1
        elif signals['sell_signals'].iloc[i]:
            print(f"   {date}: 🔴 卖出信号 - 主力减仓")
            signal_count += 1
        elif signals['super_buy_signals'].iloc[i]:
            print(f"   {date}: ⭐ 超级买入信号 - 超级主力建仓!")
            signal_count += 1
        
        if signal_count >= 10:
            break

def demo_chinese_stocks():
    """演示中国股票分析"""
    print("\n" + "=" * 60)
    print("中国股票分析演示")
    print("=" * 60)
    
    # 中国股票代码示例
    chinese_stocks = [
        ('000001.SZ', '平安银行'),
        ('600000.SS', '浦发银行'),
        ('000858.SZ', '五粮液'),
        ('600519.SS', '贵州茅台')
    ]
    
    loader = DataLoader()
    
    for symbol, name in chinese_stocks:
        print(f"\n📊 分析 {name} ({symbol}):")
        
        try:
            # 获取股票数据
            stock_data = loader.get_chinese_stock_data(symbol, '6mo')
            index_data = loader.get_chinese_index_data('shanghai', '6mo')
            
            if stock_data.empty or index_data.empty:
                print(f"   ❌ 无法获取 {name} 的数据")
                continue
            
            # 计算指标
            indicator = StockIndicator(stock_data, index_data)
            indicator.calculate_all_indicators()
            
            # 获取摘要
            summary = indicator.get_summary()
            
            print(f"   当前价格: ¥{summary['current_price']:.2f}")
            print(f"   中线趋势: {summary['mid_trend_value']:.2f}")
            print(f"   趋势强度: {summary['trend_strength']}")
            print(f"   买入信号: {'是' if summary['buy_signal_active'] else '否'}")
            
        except Exception as e:
            print(f"   ❌ 分析 {name} 时出错: {e}")

def demo_indicators_explanation():
    """演示指标解释"""
    print("\n" + "=" * 60)
    print("技术指标详细解释")
    print("=" * 60)
    
    print("📋 核心指标说明:")
    print()
    print("🔸 V11 (个股强弱动量指标):")
    print("   - 基于价格在55日高低点区间内的位置")
    print("   - 通过多重平滑计算得出")
    print("   - 数值范围通常在0-100之间")
    print("   - 低位表示超卖，高位表示超买")
    print()
    
    print("🔸 V12 (V11变化率):")
    print("   - 反映V11指标的加速度")
    print("   - 正值表示V11在上升")
    print("   - 负值表示V11在下降")
    print("   - 用于判断动量转折点")
    print()
    
    print("🔸 中线趋势 (B4):")
    print("   - 基于价格在90日高低点区间内的位置")
    print("   - 反映中短期趋势强弱")
    print("   - 数值越高趋势越强")
    print("   - 通常用于判断趋势方向")
    print()
    
    print("🔸 买入信号条件:")
    print("   EMA(V11,3) ≤ 13 且 V12 > 13")
    print("   - 表示动量处于低位且开始加速上升")
    print("   - 通常出现在超卖反弹时")
    print()
    
    print("🔸 卖出信号条件:")
    print("   EMA(V11,3) ≥ 90 且 V12 > 0")
    print("   - 表示动量处于高位且继续上升")
    print("   - 通常出现在超买区域")
    print()
    
    print("🔸 超级主力建仓信号:")
    print("   - 满足多重极端条件")
    print("   - 包括价格、动量、成交量等多个维度")
    print("   - 出现概率较低但可靠性较高")

def demo_visualization():
    """演示可视化功能"""
    print("\n" + "=" * 60)
    print("可视化功能演示")
    print("=" * 60)
    
    # 获取数据
    loader = DataLoader()
    stock_data, index_data = loader.get_sample_data()
    
    if stock_data.empty or index_data.empty:
        print("❌ 无法获取数据")
        return
    
    # 计算指标
    indicator = StockIndicator(stock_data, index_data)
    results = indicator.calculate_all_indicators()
    
    # 创建图表
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    fig.suptitle('股票技术指标分析演示', fontsize=16, fontweight='bold')
    
    # 1. 价格走势
    axes[0].plot(results['price'].index, results['price'], label='收盘价', linewidth=2)
    axes[0].set_title('价格走势')
    axes[0].set_ylabel('价格 ($)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 2. V11和V12指标
    axes[1].plot(results['V11'].index, results['V11'], label='V11指标', linewidth=2)
    axes[1].plot(results['V12'].index, results['V12'], label='V12指标', linewidth=2)
    axes[1].axhline(y=13, color='red', linestyle='--', alpha=0.7, label='买入线')
    axes[1].axhline(y=90, color='blue', linestyle='--', alpha=0.7, label='卖出线')
    axes[1].set_title('V11/V12指标')
    axes[1].set_ylabel('指标值')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 3. 中线趋势
    axes[2].plot(results['B4'].index, results['B4'], label='中线趋势', linewidth=2, color='purple')
    axes[2].set_title('中线趋势')
    axes[2].set_ylabel('趋势值')
    axes[2].set_xlabel('日期')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    # 格式化x轴日期
    for ax in axes:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('stock_analysis_demo.png', dpi=300, bbox_inches='tight')
    print("✅ 图表已保存为 'stock_analysis_demo.png'")
    
    # 显示图表
    plt.show()

def main():
    """主函数"""
    print("🚀 股票技术指标分析系统 - 演示程序")
    print("基于通达信指标源码的专业股票分析工具")
    print()
    
    try:
        # 基本使用演示
        demo_basic_usage()
        
        # 信号分析演示
        demo_signals()
        
        # 中国股票演示
        demo_chinese_stocks()
        
        # 指标解释
        demo_indicators_explanation()
        
        # 可视化演示
        print("\n是否要显示可视化图表? (y/n): ", end="")
        choice = input().lower().strip()
        if choice in ['y', 'yes', '是']:
            demo_visualization()
        
        print("\n" + "=" * 60)
        print("🎉 演示完成!")
        print("=" * 60)
        print("💡 提示:")
        print("   - 运行 'python app.py' 启动Web应用")
        print("   - 访问 http://localhost:5000 使用完整功能")
        print("   - 查看 README.md 了解更多使用方法")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        print("请检查网络连接和依赖包安装")

if __name__ == "__main__":
    main() 