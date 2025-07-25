#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 mock 数据功能
"""

import pandas as pd
import numpy as np
from data_loader import DataLoader
from stock_indicator import StockIndicator

def test_mock_data():
    """测试 mock 数据生成和指标计算"""
    print("🧪 测试 Mock 数据功能")
    print("=" * 50)
    
    try:
        # 创建数据加载器
        loader = DataLoader()
        
        # 生成 mock 数据
        print("📊 生成模拟数据...")
        stock_data, index_data = loader.get_mock_data(100)
        
        print(f"✅ 股票数据: {len(stock_data)} 条记录")
        print(f"✅ 指数数据: {len(index_data)} 条记录")
        print(f"📅 数据范围: {stock_data.index[0]} 到 {stock_data.index[-1]}")
        
        # 检查数据格式
        print("\n📋 数据格式检查:")
        print(f"股票数据列: {list(stock_data.columns)}")
        print(f"指数数据列: {list(index_data.columns)}")
        
        # 创建指标计算器
        print("\n🔧 创建指标计算器...")
        indicator = StockIndicator(stock_data, index_data)
        
        # 计算指标
        print("📈 计算技术指标...")
        results = indicator.calculate_all_indicators()
        
        print("✅ 指标计算完成!")
        
        # 获取摘要
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
        
        # 获取信号
        signals = indicator.get_signals()
        print(f"\n📈 信号统计:")
        print(f"   买入信号总数: {signals['buy_signals'].sum()}")
        print(f"   卖出信号总数: {signals['sell_signals'].sum()}")
        print(f"   超级买入信号总数: {signals['super_buy_signals'].sum()}")
        
        print("\n🎉 Mock 数据测试成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_mock_data() 