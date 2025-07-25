#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
买卖信号场景演示脚本
展示模拟数据中的各种买卖信号触发情况
"""

import pandas as pd
import numpy as np
from data_loader import DataLoader
from stock_indicator import StockIndicator
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def demo_signal_scenarios():
    """演示各种买卖信号场景"""
    print("=" * 80)
    print("🔔 买卖信号场景演示")
    print("=" * 80)
    
    # 加载模拟数据
    loader = DataLoader()
    stock_data, index_data = loader.get_mock_data(200)
    
    print(f"📊 数据概览:")
    print(f"   股票数据: {len(stock_data)} 个交易日")
    print(f"   指数数据: {len(index_data)} 个交易日")
    print(f"   时间范围: {stock_data.index[0].strftime('%Y-%m-%d')} 到 {stock_data.index[-1].strftime('%Y-%m-%d')}")
    print()
    
    # 计算技术指标
    indicator = StockIndicator(stock_data, index_data)
    results = indicator.calculate_all_indicators()
    
    # 获取信号数据
    signals = indicator.get_signals()
    
    # 分析各个场景
    analyze_signal_scenarios(stock_data, index_data, results, signals)
    
    # 可视化信号
    visualize_signals(stock_data, results, signals)

def analyze_signal_scenarios(stock_data, index_data, results, signals):
    """分析各个买卖信号场景"""
    print("🎯 买卖信号场景分析:")
    print("-" * 60)
    
    # 场景1: 买入信号 (30-40天)
    print("📈 场景1: 买入信号触发 (第30-40天)")
    print("   触发条件: V11 <= 13 且 V12 > 13")
    print("   市场状态: 超卖反弹，主力开始建仓")
    print("   投资建议: 可考虑分批买入，设置止损")
    
    buy_signals = signals['buy_signals']
    buy_dates = buy_signals[buy_signals].index
    if len(buy_dates) > 0:
        print(f"   实际触发: {len(buy_dates)} 次")
        for i, date in enumerate(buy_dates[:3]):  # 显示前3次
            price = stock_data.loc[date, 'Close']
            v11 = results['V11'].loc[date]
            v12 = results['V12'].loc[date]
            print(f"     {date.strftime('%Y-%m-%d')}: 价格¥{price:.2f}, V11={v11:.1f}, V12={v12:.1f}")
    print()
    
    # 场景2: 超级买入信号 (80-90天)
    print("⭐ 场景2: 超级买入信号触发 (第80-90天)")
    print("   触发条件: 多重极端条件同时满足")
    print("   市场状态: 主力大举建仓，技术指标共振")
    print("   投资建议: 强烈买入信号，可重仓买入")
    
    super_buy_signals = signals['super_buy_signals']
    super_buy_dates = super_buy_signals[super_buy_signals].index
    if len(super_buy_dates) > 0:
        print(f"   实际触发: {len(super_buy_dates)} 次")
        for i, date in enumerate(super_buy_dates[:3]):  # 显示前3次
            price = stock_data.loc[date, 'Close']
            var20 = results['VAR20'].loc[date]
            print(f"     {date.strftime('%Y-%m-%d')}: 价格¥{price:.2f}, VAR20={var20}")
    print()
    
    # 场景3: 卖出信号 (120-130天)
    print("📉 场景3: 卖出信号触发 (第120-130天)")
    print("   触发条件: V11 >= 90 且 V12 > 0")
    print("   市场状态: 超买区域，主力开始减仓")
    print("   投资建议: 及时止损，避免深度套牢")
    
    sell_signals = signals['sell_signals']
    sell_dates = sell_signals[sell_signals].index
    if len(sell_dates) > 0:
        print(f"   实际触发: {len(sell_dates)} 次")
        for i, date in enumerate(sell_dates[:3]):  # 显示前3次
            price = stock_data.loc[date, 'Close']
            v11 = results['V11'].loc[date]
            v12 = results['V12'].loc[date]
            print(f"     {date.strftime('%Y-%m-%d')}: 价格¥{price:.2f}, V11={v11:.1f}, V12={v12:.1f}")
    print()
    
    # 场景4: 再次买入信号 (160-170天)
    print("🔄 场景4: 再次买入信号触发 (第160-170天)")
    print("   触发条件: 价格回调后再次满足买入条件")
    print("   市场状态: 二次探底成功，新的买入机会")
    print("   投资建议: 确认趋势后买入，设置止损")
    
    # 统计信号总数
    total_buy = buy_signals.sum()
    total_sell = sell_signals.sum()
    total_super = super_buy_signals.sum()
    
    print("📊 信号统计汇总:")
    print(f"   买入信号总数: {total_buy}")
    print(f"   卖出信号总数: {total_sell}")
    print(f"   超级买入信号总数: {total_super}")
    print(f"   信号比率 (买入/卖出): {total_buy/max(total_sell, 1):.2f}")
    print()

def visualize_signals(stock_data, results, signals):
    """可视化买卖信号"""
    print("📊 信号可视化分析:")
    print("-" * 60)
    
    # 创建图表
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
    
    # 子图1: 价格走势和信号标记
    ax1.plot(stock_data.index, stock_data['Close'], 'b-', linewidth=1, label='收盘价')
    
    # 标记买入信号
    buy_signals = signals['buy_signals']
    buy_dates = buy_signals[buy_signals].index
    if len(buy_dates) > 0:
        buy_prices = stock_data.loc[buy_dates, 'Close']
        ax1.scatter(buy_dates, buy_prices, color='red', s=100, marker='^', label='买入信号', zorder=5)
    
    # 标记卖出信号
    sell_signals = signals['sell_signals']
    sell_dates = sell_signals[sell_signals].index
    if len(sell_dates) > 0:
        sell_prices = stock_data.loc[sell_dates, 'Close']
        ax1.scatter(sell_dates, sell_prices, color='green', s=100, marker='v', label='卖出信号', zorder=5)
    
    # 标记超级买入信号
    super_buy_signals = signals['super_buy_signals']
    super_buy_dates = super_buy_signals[super_buy_signals].index
    if len(super_buy_dates) > 0:
        super_buy_prices = stock_data.loc[super_buy_dates, 'Close']
        ax1.scatter(super_buy_dates, super_buy_prices, color='purple', s=150, marker='*', label='超级买入信号', zorder=5)
    
    ax1.set_title('股票价格走势与买卖信号', fontsize=14, fontweight='bold')
    ax1.set_ylabel('价格 (¥)', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 子图2: V11和V12指标
    ax2.plot(stock_data.index, results['V11'], 'b-', linewidth=1, label='V11 (个股强弱动量)')
    ax2.plot(stock_data.index, results['V12'], 'r-', linewidth=1, label='V12 (V11变化率)')
    
    # 添加买入信号区域
    ax2.axhline(y=13, color='red', linestyle='--', alpha=0.5, label='买入信号线 (V11=13)')
    ax2.axhline(y=90, color='green', linestyle='--', alpha=0.5, label='卖出信号线 (V11=90)')
    
    ax2.set_title('V11和V12技术指标', fontsize=14, fontweight='bold')
    ax2.set_ylabel('指标值', fontsize=12)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 子图3: 中线趋势
    ax3.plot(stock_data.index, results['B4'], 'purple', linewidth=2, label='中线趋势 (B4)')
    
    # 添加趋势强度区域
    ax3.axhline(y=70, color='green', linestyle='--', alpha=0.5, label='强势线 (70)')
    ax3.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='弱势线 (30)')
    
    ax3.set_title('中线趋势指标 (B4)', fontsize=14, fontweight='bold')
    ax3.set_ylabel('趋势值', fontsize=12)
    ax3.set_xlabel('日期', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 格式化x轴日期
    for ax in [ax1, ax2, ax3]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    plt.savefig('signal_analysis.png', dpi=300, bbox_inches='tight')
    print("✅ 信号分析图表已保存为 'signal_analysis.png'")
    print()

def demo_current_status():
    """演示当前状态分析"""
    print("🎯 当前状态分析:")
    print("-" * 60)
    
    # 加载数据
    loader = DataLoader()
    stock_data, index_data = loader.get_mock_data(200)
    indicator = StockIndicator(stock_data, index_data)
    results = indicator.calculate_all_indicators()
    summary = indicator.get_summary()
    
    print(f"📈 当前价格: ¥{summary['current_price']:.2f}")
    print(f"📊 中线趋势: {summary['mid_trend_value']:.1f}")
    print(f"💪 趋势强度: {summary['trend_strength']}")
    print(f"🔔 买入信号: {'是' if summary['buy_signal_active'] else '否'}")
    print(f"🔔 卖出信号: {'是' if summary['sell_signal_active'] else '否'}")
    print(f"⭐ 超级买入: {'是' if summary['super_buy_signal_active'] else '否'}")
    print()
    
    # 投资建议
    if summary['buy_signal_active']:
        print("💡 投资建议: 当前出现买入信号，可考虑分批买入")
    elif summary['sell_signal_active']:
        print("💡 投资建议: 当前出现卖出信号，建议及时止损")
    elif summary['super_buy_signal_active']:
        print("💡 投资建议: 当前出现超级买入信号，强烈建议买入")
    else:
        print("💡 投资建议: 当前无明确信号，建议观望")
    
    if summary['mid_trend_value'] > 70:
        print("📈 趋势分析: 中线趋势强劲，市场情绪乐观")
    elif summary['mid_trend_value'] > 30:
        print("📊 趋势分析: 中线趋势温和，市场方向不明确")
    else:
        print("📉 趋势分析: 中线趋势弱势，注意风险")

if __name__ == "__main__":
    try:
        demo_signal_scenarios()
        demo_current_status()
        print("🎉 演示完成！")
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc() 