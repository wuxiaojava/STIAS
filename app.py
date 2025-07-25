from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import json
import os
from stock_indicator import StockIndicator
from data_loader import DataLoader
import plotly.graph_objects as go
import plotly.utils
from datetime import datetime
import traceback
import numpy as np
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

def safe_float(value, default=0.0):
    """安全地转换为浮点数，处理NaN和inf值"""
    try:
        if pd.isna(value) or np.isinf(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def safe_bool(value, default=False):
    """安全地转换为布尔值"""
    try:
        if pd.isna(value):
            return default
        return bool(value)
    except (TypeError, ValueError):
        return default

# 全局变量存储当前数据
current_data = {
    'stock_data': None,
    'index_data': None,
    'indicator': None,
    'symbol': None,
    'index_symbol': None
}

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/symbols')
def get_symbols():
    """获取可用的股票和指数代码"""
    try:
        loader = DataLoader()
        symbols = loader.get_available_symbols()
        return jsonify(symbols)
    except Exception as e:
        print(f"获取符号列表失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取符号列表失败: {str(e)}'}), 500

@app.route('/api/load_data', methods=['POST'])
def load_data():
    """
    加载股票和指数数据
    ---
    tags:
      - 数据加载
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            stock_symbol:
              type: string
              description: 股票代码
            index_symbol:
              type: string
              description: 指数代码
            period:
              type: string
              description: 数据周期
            mock:
              type: boolean
              description: 是否使用模拟数据
            data_source:
              type: string
              description: 数据源(yfinance/akshare)
    responses:
      200:
        description: 成功返回
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            summary:
              type: object
            data_points:
              type: integer
      400:
        description: 参数错误
      500:
        description: 服务器错误
    """
    try:
        print("=== 开始处理 load_data 请求 ===")
        data = request.get_json()
        if data is None:
            print("❌ 无效的请求数据")
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        print(f"收到的参数: {data}")
        
        # 参数校验
        required_fields = ['stock_symbol', 'index_symbol', 'period', 'mock', 'data_source']
        for field in required_fields:
            if field not in data:
                print(f"❌ 缺少必需参数: {field}")
                return jsonify({'success': False, 'error': f'缺少参数: {field}'}), 400
        
        print("✅ 参数校验通过")
            
        use_mock = data.get('mock', False)
        stock_symbol = data.get('stock_symbol', 'AAPL')
        index_symbol = data.get('index_symbol', '^GSPC')
        period = data.get('period', '1y')
        data_source = data.get('data_source', 'yfinance')
        
        print(f"加载数据请求: mock={use_mock}, stock={stock_symbol}, index={index_symbol}, period={period}, source={data_source}")
        
        # 创建数据加载器
        try:
            loader = DataLoader(data_source=data_source)
            print("✅ 数据加载器创建成功")
        except ImportError as e:
            print(f"❌ 数据加载器创建失败: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 400
        
        if use_mock:
            # 使用模拟数据
            print("使用模拟数据...")
            stock_data, index_data = loader.get_mock_data(200)
            print(f"模拟数据生成完成: 股票{len(stock_data)}条, 指数{len(index_data)}条")
        else:
            # 获取股票数据
            print(f"获取真实股票数据: {stock_symbol}")
            stock_data = loader.get_stock_data(stock_symbol, period)
            if stock_data.empty:
                print(f"❌ 无法获取股票数据: {stock_symbol}")
                return jsonify({'success': False, 'error': f'无法获取股票 {stock_symbol} 的数据'}), 400
            print(f"✅ 股票数据获取成功: {len(stock_data)}条记录")
            
            # 获取指数数据
            print(f"获取真实指数数据: {index_symbol}")
            index_data = loader.get_index_data(index_symbol, period)
            if index_data.empty:
                print(f"❌ 无法获取指数数据: {index_symbol}")
                return jsonify({'success': False, 'error': f'无法获取指数 {index_symbol} 的数据'}), 400
            print(f"✅ 指数数据获取成功: {len(index_data)}条记录")
            
            # 验证数据
            if not loader.validate_data(stock_data, 'stock'):
                print("❌ 股票数据验证失败")
                return jsonify({'success': False, 'error': '股票数据不完整'}), 400
            if not loader.validate_data(index_data, 'index'):
                print("❌ 指数数据验证失败")
                return jsonify({'success': False, 'error': '指数数据不完整'}), 400
            print("✅ 数据验证通过")
        
        # 创建指标计算器
        print("创建指标计算器...")
        indicator = StockIndicator(stock_data, index_data)
        print("计算技术指标...")
        indicator.calculate_all_indicators()
        print("指标计算完成")
        
        # 存储全局数据
        global current_data
        current_data['stock_data'] = stock_data
        current_data['index_data'] = index_data
        current_data['indicator'] = indicator
        current_data['symbol'] = stock_symbol
        current_data['index_symbol'] = index_symbol
        
        # 获取摘要信息
        print("生成摘要信息...")
        summary = indicator.get_summary()
        print(f"✅ 摘要信息生成成功: {list(summary.keys())}")
        
        print(f"数据加载完成: {len(stock_data)}条记录")
        
        # 构建响应数据，安全处理所有数值
        response_data = {
            'success': True,
            'message': f'成功加载 {stock_symbol} 和 {index_symbol} 的数据' + ('（模拟数据）' if use_mock else ''),
            'summary': {
                'symbol': stock_symbol,
                'current_price': safe_float(summary.get('current_price', 0)),
                'mid_trend_value': safe_float(summary.get('mid_trend_value', 0)),
                'trend_strength': str(summary.get('trend_strength', '未知')),
                'buy_signal_active': safe_bool(summary.get('buy_signal_active', False)),
                'sell_signal_active': safe_bool(summary.get('sell_signal_active', False)),
                'super_buy_signal_active': safe_bool(summary.get('super_buy_signal_active', False)),
                'v11_value': safe_float(summary.get('v11_value', 0)),
                'v12_value': safe_float(summary.get('v12_value', 0)),
                'price_change': safe_float(summary.get('price_change', 0)),
                'price_change_percent': safe_float(summary.get('price_change_percent', 0))
            },
            'data_points': len(stock_data)
        }
        
        print("=== 准备返回响应 ===")
        print(f"响应数据结构: {list(response_data.keys())}")
        
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f'加载数据时出错: {str(e)}'
        print(f"❌ 处理请求时发生异常: {error_msg}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/indicators')
def get_indicators():
    """获取技术指标数据"""
    try:
        if current_data['indicator'] is None:
            return jsonify({'success': False, 'error': '请先加载数据'}), 400
        
        indicator = current_data['indicator']
        results = indicator.results
        
        # 准备图表数据
        dates = results['price'].index.strftime('%Y-%m-%d').tolist()
        
        chart_data = {
            'dates': dates,
            'price': results['price'].tolist(),
            'volume': results['volume'].tolist(),
            'mid_trend': results['B4'].tolist(),
            'v11': results['V11'].tolist(),
            'v12': results['V12'].tolist(),
            'buy_signals': results['BB1'].tolist(),
            'sell_signals': results['CC1'].tolist(),
            'super_buy_signals': results['super_buy_signal'].tolist(),
            'var20': results['VAR20'].tolist()
        }
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'summary': indicator.get_summary()
        })
        
    except Exception as e:
        print(f"获取指标数据失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取指标数据时出错: {str(e)}'}), 500

@app.route('/api/signals')
def get_signals():
    """获取买卖信号"""
    try:
        if current_data['indicator'] is None:
            return jsonify({'success': False, 'error': '请先加载数据'}), 400
        
        indicator = current_data['indicator']
        signals = indicator.get_signals()
        
        # 获取最近的信号
        recent_signals = []
        dates = signals['buy_signals'].index
        
        for i in range(len(dates)):
            date = dates[i].strftime('%Y-%m-%d')
            if safe_bool(signals['buy_signals'].iloc[i]):
                recent_signals.append({
                    'date': date,
                    'type': '买入信号',
                    'description': '主力进场，建议买入'
                })
            elif safe_bool(signals['sell_signals'].iloc[i]):
                recent_signals.append({
                    'date': date,
                    'type': '卖出信号',
                    'description': '主力减仓，建议卖出'
                })
            elif safe_bool(signals['super_buy_signals'].iloc[i]):
                recent_signals.append({
                    'date': date,
                    'type': '超级买入信号',
                    'description': '超级主力建仓，强烈买入！'
                })
        
        # 只返回最近30个信号
        recent_signals = recent_signals[-30:]
        
        return jsonify({
            'success': True,
            'signals': recent_signals,
            'total_buy': int(signals['buy_signals'].sum()),
            'total_sell': int(signals['sell_signals'].sum()),
            'total_super_buy': int(signals['super_buy_signals'].sum())
        })
        
    except Exception as e:
        print(f"获取信号失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取信号时出错: {str(e)}'}), 500

@app.route('/api/chart')
def get_chart():
    """获取图表数据"""
    try:
        if current_data['indicator'] is None:
            return jsonify({'success': False, 'error': '请先加载数据'}), 400
        
        print("开始生成图表...")
        indicator = current_data['indicator']
        results = indicator.results
        
        # 创建价格和成交量图表
        fig = go.Figure()
        
        # 添加K线图
        print("添加K线图...")
        fig.add_trace(go.Candlestick(
            x=results['price'].index,
            open=current_data['stock_data']['Open'],
            high=current_data['stock_data']['High'],
            low=current_data['stock_data']['Low'],
            close=results['price'],
            name='K线',
            increasing_line_color='red',
            decreasing_line_color='green'
        ))
        
        # 添加每日价格连线 - 安全处理
        try:
            print("生成价格连线...")
            price_dates = results['price'].index
            
            # 安全地获取股票数据，确保索引匹配
            stock_aligned = current_data['stock_data'].reindex(price_dates)
            open_values = stock_aligned['Open'].fillna(method='ffill').fillna(method='bfill').values
            high_values = stock_aligned['High'].fillna(method='ffill').fillna(method='bfill').values
            low_values = stock_aligned['Low'].fillna(method='ffill').fillna(method='bfill').values
            close_values = stock_aligned['Close'].fillna(method='ffill').fillna(method='bfill').values
            volume_values = stock_aligned['Volume'].fillna(0).values
            
            # 计算每日均价 (开盘价 + 最高价 + 最低价 + 收盘价) / 4
            price_values = (open_values + high_values + low_values + close_values) / 4
            
            # 构建每日详细信息的悬浮文本，包含所有字段信息
            daily_texts = []
            for i, date in enumerate(price_dates):
                try:
                    # 安全地获取数值，处理NaN值
                    open_val = safe_float(open_values[i], price_values[i])
                    high_val = safe_float(high_values[i], price_values[i])  
                    low_val = safe_float(low_values[i], price_values[i])
                    close_val = safe_float(close_values[i], price_values[i])
                    price_val = safe_float(price_values[i], 0)
                    volume_val = safe_float(volume_values[i], 0)
                    
                    # 计算涨跌和涨跌幅
                    price_change = price_val - open_val
                    price_change_pct = (price_change / open_val * 100) if open_val != 0 else 0
                    trend_symbol = "📈" if price_change > 0 else "📉" if price_change < 0 else "➡️"
                    
                    # 计算日内振幅
                    amplitude = ((high_val - low_val) / open_val * 100) if open_val != 0 else 0
                    
                    # 获取当天的所有技术指标数据
                    v11_val = safe_float(results['V11'].iloc[i] if i < len(results['V11']) else 0)
                    v12_val = safe_float(results['V12'].iloc[i] if i < len(results['V12']) else 0)
                    b4_val = safe_float(results['B4'].iloc[i] if i < len(results['B4']) else 0)  # 中线趋势
                    a4_val = safe_float(results['A4'].iloc[i] if i < len(results['A4']) else 0)  # 短线趋势
                    c4_val = safe_float(results['C4'].iloc[i] if i < len(results['C4']) else 0)  # 长线趋势
                    
                    # 获取买卖信号状态
                    buy_signal = safe_bool(results['BB1'].iloc[i] if i < len(results['BB1']) else False)
                    sell_signal = safe_bool(results['CC1'].iloc[i] if i < len(results['CC1']) else False)
                    super_buy_signal = safe_bool(results['super_buy_signal'].iloc[i] if i < len(results['super_buy_signal']) else False)
                    
                    # 获取其他技术指标
                    v1_val = safe_float(results['V1'].iloc[i] if i < len(results['V1']) else 0)
                    v2_val = safe_float(results['V2'].iloc[i] if i < len(results['V2']) else 0)
                    v3_val = safe_float(results['V3'].iloc[i] if i < len(results['V3']) else 0)
                    v4_val = safe_float(results['V4'].iloc[i] if i < len(results['V4']) else 0)
                    
                    # 获取更多辅助指标
                    aa_val = safe_float(results['AA'].iloc[i] if i < len(results['AA']) else 0)  # 价格加权
                    bb_val = safe_float(results['BB'].iloc[i] if i < len(results['BB']) else 0)  # 3日均价
                    cc_val = safe_float(results['CC'].iloc[i] if i < len(results['CC']) else 0)  # 上涨下跌比
                    dd_val = safe_float(results['DD'].iloc[i] if i < len(results['DD']) else 0)  # RSI指标
                    
                    # 获取VAR20超级主力条件
                    var20_val = safe_bool(results['VAR20'].iloc[i] if i < len(results['VAR20']) else False)
                    
                    # 构建分组的详细信息
                    signal_status = []
                    if buy_signal:
                        signal_status.append("🔴 买入信号")
                    if sell_signal:
                        signal_status.append("🔵 卖出信号")
                    if super_buy_signal:
                        signal_status.append("⭐ 超级买入")
                    if not signal_status:
                        signal_status.append("⚪ 无信号")
                    
                    daily_texts.append(
                        f"📅 {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})<br>" +
                        f"<b>━━━ 价格信息 ━━━</b><br>" +
                        f"🏷️ 开盘: ¥{open_val:.2f} | ⬆️ 最高: ¥{high_val:.2f}<br>" +
                        f"⬇️ 最低: ¥{low_val:.2f} | 🎯 收盘: ¥{close_val:.2f}<br>" +
                        f"💰 均价: ¥{price_val:.2f} | 📊 成交量: {volume_val:,.0f}<br>" +
                        f"{trend_symbol} 涨跌: ¥{price_change:+.2f} ({price_change_pct:+.2f}%) | 📏 振幅: {amplitude:.2f}%<br>" +
                        f"<b>━━━ 信号状态 ━━━</b><br>" +
                        f"{' | '.join(signal_status)}<br>" +
                        f"<b>━━━ 核心指标 ━━━</b><br>" +
                        f"🔶 V11 (强弱动量): {v11_val:.2f}<br>" +
                        f"🔷 V12 (动量变化率): {v12_val:.2f}<br>" +
                        f"🟣 中线趋势 (B4): {b4_val:.2f}<br>" +
                        f"🟠 短线趋势 (A4): {a4_val:.2f}<br>" +
                        f"🟡 长线趋势 (C4): {c4_val:.2f}<br>" +
                        f"<b>━━━ 辅助指标 ━━━</b><br>" +
                        f"V1: {v1_val:.2f} | V2: {v2_val:.2f}<br>" +
                        f"V3: {v3_val:.2f} | V4: {v4_val:.2f}<br>" +
                        f"<b>━━━ 高级指标 ━━━</b><br>" +
                        f"🔸 价格加权(AA): {aa_val:.2f}<br>" +
                        f"🔹 3日均价(BB): {bb_val:.2f}<br>" +
                        f"📊 涨跌比(CC): {cc_val:.2f}<br>" +
                        f"🎯 RSI类(DD): {dd_val:.2f}<br>" +
                        f"⭐ 超级主力条件: {'✅ 满足' if var20_val else '❌ 不满足'}"
                    )
                except (IndexError, ValueError, TypeError) as e:
                    # 如果数据有问题，提供基本信息
                    daily_texts.append(
                        f"📅 {date.strftime('%Y-%m-%d')} ({date.strftime('%A')})<br>" +
                        f"<b>━━━ 基本信息 ━━━</b><br>" +
                        f"💰 均价: ¥{safe_float(price_values[i]):.2f}<br>" +
                        f"⚠️ 部分技术指标数据暂不可用<br>" +
                        f"📊 正在重新计算中..."
                    )
            
            # 添加价格连线
            fig.add_trace(go.Scatter(
                x=price_dates,
                y=price_values,
                mode='lines+markers',
                line=dict(
                    color='#FFD700', 
                    width=3, 
                    dash='solid'
                ),
                marker=dict(
                    size=6, 
                    color='#FFD700', 
                    symbol='circle',
                    line=dict(color='#FFA500', width=1)
                ),
                name='💰 均价趋势线',
                text=daily_texts,
                hovertemplate='<b>📊 完整技术分析数据</b><br>%{text}<extra></extra>',
                hoverlabel=dict(
                    bgcolor='rgba(0,0,0,0.9)',
                    bordercolor='#FFD700',
                    font=dict(color='white', size=11),
                    align='left'
                ),
                showlegend=True,
                opacity=0.9
            ))
            print("✅ 价格连线生成成功")
            
        except Exception as e:
            # 如果价格连线生成失败，添加简单的价格线
            print(f"价格连线生成失败: {e}")
            fig.add_trace(go.Scatter(
                x=results['price'].index,
                y=results['price'].values,
                mode='lines',
                line=dict(color='#FFD700', width=2),
                name='💰 均价趋势线',
                showlegend=True
            ))
        
        # 添加买入信号
        print("添加买入信号...")
        buy_dates = results['BB1'][results['BB1']].index
        if len(buy_dates) > 0:
            # 准备买入信号的详细信息
            buy_prices = results['price'].loc[buy_dates]
            buy_v11 = results['V11'].loc[buy_dates]
            buy_v12 = results['V12'].loc[buy_dates]
            buy_trend = results['B4'].loc[buy_dates]
            
            # 构建买入信号的详细文本
            buy_texts = []
            for i, date in enumerate(buy_dates):
                buy_texts.append(f"主力进<br>买入价格: ¥{safe_float(buy_prices.iloc[i]):.2f}<br>V11指标: {safe_float(buy_v11.iloc[i]):.1f} (≤13买入线)<br>V12指标: {safe_float(buy_v12.iloc[i]):.1f}<br>中线趋势: {safe_float(buy_trend.iloc[i]):.1f}")
            
            fig.add_trace(go.Scatter(
                x=buy_dates,
                y=results['price'].loc[buy_dates] * 0.95,
                mode='markers',
                marker=dict(symbol='triangle-up', size=15, color='red'),
                name='买入信号',
                text=buy_texts,
                hovertemplate='%{text}<br>信号日期: %{x}<extra></extra>'
            ))
        
        # 添加卖出信号
        print("添加卖出信号...")
        sell_dates = results['CC1'][results['CC1']].index
        if len(sell_dates) > 0:
            # 准备卖出信号的详细信息
            sell_prices = results['price'].loc[sell_dates]
            sell_v11 = results['V11'].loc[sell_dates]
            sell_v12 = results['V12'].loc[sell_dates]
            sell_trend = results['B4'].loc[sell_dates]
            
            # 构建卖出信号的详细文本
            sell_texts = []
            for i, date in enumerate(sell_dates):
                sell_texts.append(f"主力减仓<br>卖出价格: ¥{safe_float(sell_prices.iloc[i]):.2f}<br>V11指标: {safe_float(sell_v11.iloc[i]):.1f} (≥90卖出线)<br>V12指标: {safe_float(sell_v12.iloc[i]):.1f}<br>中线趋势: {safe_float(sell_trend.iloc[i]):.1f}")
            
            fig.add_trace(go.Scatter(
                x=sell_dates,
                y=results['price'].loc[sell_dates] * 1.05,
                mode='markers',
                marker=dict(symbol='triangle-down', size=15, color='blue'),
                name='卖出信号',
                text=sell_texts,
                hovertemplate='%{text}<br>信号日期: %{x}<extra></extra>'
            ))
        
        # 添加超级买入信号
        print("添加超级买入信号...")
        super_buy_dates = results['super_buy_signal'][results['super_buy_signal']].index
        if len(super_buy_dates) > 0:
            # 准备超级买入信号的详细信息
            super_buy_prices = results['price'].loc[super_buy_dates]
            super_buy_v11 = results['V11'].loc[super_buy_dates]
            super_buy_trend = results['B4'].loc[super_buy_dates]
            
            # 构建超级买入信号的详细文本
            super_buy_texts = []
            for i, date in enumerate(super_buy_dates):
                super_buy_texts.append(f"超级主力建仓!<br>建仓价格: ¥{safe_float(super_buy_prices.iloc[i]):.2f}<br>V11指标: {safe_float(super_buy_v11.iloc[i]):.1f}<br>中线趋势: {safe_float(super_buy_trend.iloc[i]):.1f}<br>多重条件共振确认")
            
            fig.add_trace(go.Scatter(
                x=super_buy_dates,
                y=results['price'].loc[super_buy_dates] * 0.9,
                mode='markers',
                marker=dict(symbol='star', size=20, color='purple'),
                name='超级买入信号',
                text=super_buy_texts,
                hovertemplate='%{text}<br>信号日期: %{x}<extra></extra>'
            ))
        
        print("设置图表布局...")
        fig.update_layout(
            title=f'{current_data["symbol"]} 技术指标分析',
            xaxis_title='日期',
            yaxis_title='价格 (¥)',
            height=600,
            showlegend=True,
            hovermode='x unified',  # 统一悬浮模式，显示所有线条信息
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat='¥.2f',  # 格式化Y轴显示为人民币
                side='left'
            )
        )
        
        # 创建指标图表
        print("创建指标图表...")
        fig2 = go.Figure()
        
        # 添加中线趋势
        fig2.add_trace(go.Scatter(
            x=results['B4'].index,
            y=results['B4'],
            mode='lines',
            name='中线趋势',
            line=dict(color='magenta', width=2)
        ))
        
        # 添加V11指标
        fig2.add_trace(go.Scatter(
            x=results['V11'].index,
            y=results['V11'],
            mode='lines',
            name='V11指标',
            line=dict(color='orange', width=1),
            yaxis='y2'
        ))
        
        # 添加V12指标
        fig2.add_trace(go.Scatter(
            x=results['V12'].index,
            y=results['V12'],
            mode='lines',
            name='V12指标',
            line=dict(color='cyan', width=1),
            yaxis='y2'
        ))
        
        # 添加水平参考线
        fig2.add_hline(y=13, line_dash="dash", line_color="red", annotation_text="买入线")
        fig2.add_hline(y=90, line_dash="dash", line_color="blue", annotation_text="卖出线")
        
        fig2.update_layout(
            title='技术指标',
            xaxis_title='日期',
            yaxis_title='中线趋势',
            yaxis2=dict(title='V11/V12指标', overlaying='y', side='right'),
            height=400,
            showlegend=True
        )
        
        print("✅ 图表生成完成")
        
        return jsonify({
            'success': True,
            'price_chart': json.loads(fig.to_json()),
            'indicator_chart': json.loads(fig2.to_json())
        })
        
    except Exception as e:
        error_msg = f'生成图表时出错: {str(e)}'
        print(f"❌ 图表生成失败: {error_msg}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/analysis')
def get_analysis():
    """获取详细分析报告"""
    try:
        if current_data['indicator'] is None:
            return jsonify({'success': False, 'error': '请先加载数据'}), 400
        
        print("生成分析报告...")
        indicator = current_data['indicator']
        results = indicator.results
        summary = indicator.get_summary()
        
        # 计算统计信息
        total_days = len(results['price'])
        price_change = (results['price'].iloc[-1] - results['price'].iloc[0]) / results['price'].iloc[0] * 100
        max_price = results['price'].max()
        min_price = results['price'].min()
        
        # 信号统计
        buy_count = results['BB1'].sum()
        sell_count = results['CC1'].sum()
        super_buy_count = results['super_buy_signal'].sum()
        
        # 趋势分析
        current_trend = results['B4'].iloc[-1]
        trend_direction = "上升" if current_trend > 50 else "下降" if current_trend < 30 else "震荡"
        
        analysis = {
            'basic_info': {
                'symbol': current_data['symbol'],
                'index_symbol': current_data['index_symbol'],
                'total_days': total_days,
                'current_price': safe_float(summary.get('current_price', 0)),
                'price_change_percent': round(safe_float(price_change), 2),
                'max_price': round(safe_float(max_price), 2),
                'min_price': round(safe_float(min_price), 2)
            },
            'signals': {
                'buy_signals': int(buy_count),
                'sell_signals': int(sell_count),
                'super_buy_signals': int(super_buy_count),
                'signal_ratio': round(buy_count / max(sell_count, 1), 2)
            },
            'trend_analysis': {
                'current_trend_value': round(safe_float(current_trend), 2),
                'trend_direction': trend_direction,
                'trend_strength': str(summary.get('trend_strength', '未知')),
                'v11_value': round(safe_float(summary.get('v11_value', 0)), 2),
                'v12_value': round(safe_float(summary.get('v12_value', 0)), 2)
            },
            'recommendations': []
        }
        
        # 生成详细建议
        recommendations = []
        
        # 1. 当前信号建议
        if safe_bool(summary.get('super_buy_signal_active', False)):
            recommendations.append({
                'type': '超级买入信号',
                'level': '最高',
                'message': '出现超级主力建仓信号，这是最强烈的买入信号',
                'action': '强烈建议买入',
                'risk_level': '中等',
                'priority': 1
            })
        elif safe_bool(summary.get('buy_signal_active', False)):
            recommendations.append({
                'type': '买入信号',
                'level': '中等',
                'message': '当前出现买入信号，可考虑分批买入',
                'action': '建议买入',
                'risk_level': '中等',
                'priority': 2
            })
        elif safe_bool(summary.get('sell_signal_active', False)):
            recommendations.append({
                'type': '卖出信号',
                'level': '高',
                'message': '当前出现卖出信号，建议及时止损',
                'action': '建议卖出',
                'risk_level': '高',
                'priority': 2
            })
        else:
            recommendations.append({
                'type': '无明确信号',
                'level': '低',
                'message': '当前无明确买卖信号，建议观望',
                'action': '建议观望',
                'risk_level': '低',
                'priority': 7
            })
        
        # 2. 趋势分析建议
        current_trend_val = safe_float(current_trend)
        if current_trend_val > 70:
            recommendations.append({
                'type': '趋势分析',
                'level': '高',
                'message': f'中线趋势强劲({current_trend_val:.1f})，市场情绪乐观',
                'action': '可继续持有或加仓',
                'risk_level': '低',
                'priority': 3
            })
        elif current_trend_val < 30:
            recommendations.append({
                'type': '趋势分析',
                'level': '高',
                'message': f'中线趋势较弱({current_trend_val:.1f})，市场情绪谨慎',
                'action': '注意风险，考虑减仓',
                'risk_level': '高',
                'priority': 3
            })
        else:
            recommendations.append({
                'type': '趋势分析',
                'level': '中等',
                'message': f'中线趋势震荡({current_trend_val:.1f})，市场方向不明确',
                'action': '谨慎操作，等待明确信号',
                'risk_level': '中等',
                'priority': 3
            })
        
        # 3. 主力资金分析
        v11 = safe_float(summary.get('v11_value', 0))
        v12 = safe_float(summary.get('v12_value', 0))
        
        if v11 > 50 and v12 < 30:
            recommendations.append({
                'type': '主力资金',
                'level': '高',
                'message': f'主力积极建仓(V11:{v11:.1f})，出货压力较小(V12:{v12:.1f})',
                'action': '主力看好，可跟随买入',
                'risk_level': '低',
                'priority': 4
            })
        elif v11 < 30 and v12 > 50:
            recommendations.append({
                'type': '主力资金',
                'level': '高',
                'message': f'主力减仓明显(V11:{v11:.1f})，出货压力较大(V12:{v12:.1f})',
                'action': '主力看空，注意风险',
                'risk_level': '高',
                'priority': 4
            })
        else:
            recommendations.append({
                'type': '主力资金',
                'level': '中等',
                'message': f'主力观望为主(V11:{v11:.1f}, V12:{v12:.1f})',
                'action': '等待主力明确方向',
                'risk_level': '中等',
                'priority': 4
            })
        
        # 4. 信号统计分析
        if buy_count > sell_count * 2:
            recommendations.append({
                'type': '信号统计',
                'level': '中等',
                'message': f'买入信号({buy_count}次)远多于卖出信号({sell_count}次)',
                'action': '市场情绪偏乐观，可考虑买入',
                'risk_level': '中等',
                'priority': 5
            })
        elif sell_count > buy_count * 2:
            recommendations.append({
                'type': '信号统计',
                'level': '中等',
                'message': f'卖出信号({sell_count}次)远多于买入信号({buy_count}次)',
                'action': '市场情绪偏谨慎，注意风险',
                'risk_level': '高',
                'priority': 5
            })
        
        # 5. 价格位置分析
        current_price = safe_float(summary.get('current_price', 0))
        if current_price > 0 and safe_float(max_price) > safe_float(min_price):
            price_position = (current_price - safe_float(min_price)) / (safe_float(max_price) - safe_float(min_price)) * 100
            
            if price_position > 80:
                recommendations.append({
                    'type': '价格位置',
                    'level': '中等',
                    'message': f'当前价格处于高位({price_position:.1f}%)，注意回调风险',
                    'action': '谨慎追高，设置止损',
                    'risk_level': '高',
                    'priority': 6
                })
            elif price_position < 20:
                recommendations.append({
                    'type': '价格位置',
                    'level': '中等',
                    'message': f'当前价格处于低位({price_position:.1f}%)，可能存在反弹机会',
                    'action': '可考虑逢低买入',
                    'risk_level': '中等',
                    'priority': 6
                })
        
        # 6. 综合建议
        overall_recommendation = "观望"
        overall_risk = "中等"
        
        # 按优先级生成综合建议
        if safe_bool(summary.get('super_buy_signal_active', False)) and current_trend_val > 60:
            overall_recommendation = "强烈买入"
            overall_risk = "中等"
        elif safe_bool(summary.get('buy_signal_active', False)) and current_trend_val > 50:
            overall_recommendation = "建议买入"
            overall_risk = "中等"
        elif safe_bool(summary.get('sell_signal_active', False)) or current_trend_val < 30:
            overall_recommendation = "建议卖出"
            overall_risk = "高"
        elif current_trend_val > 70:
            overall_recommendation = "继续持有"
            overall_risk = "低"
        
        # 按优先级排序
        recommendations.sort(key=lambda x: x.get('priority', 7))
        
        analysis['recommendations'] = recommendations
        analysis['overall_recommendation'] = overall_recommendation
        analysis['overall_risk'] = overall_risk
        
        print("✅ 分析报告生成完成")
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        error_msg = f'生成分析报告时出错: {str(e)}'
        print(f"❌ 分析报告生成失败: {error_msg}")
        print(f"错误堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': error_msg}), 500

@app.route('/api/yfinance_test', methods=['GET', 'POST'])
def yfinance_test():
    """
    yfinance数据测试接口
    ---
    tags:
      - 测试工具
    parameters:
      - name: symbol
        in: query
        type: string
        required: true
        description: 股票或指数代码（如AAPL、^GSPC）
      - name: method
        in: query
        type: string
        required: false
        description: yfinance方法名
      - name: period
        in: query
        type: string
        required: false
        description: 数据周期（如1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max）
      - name: interval
        in: query
        type: string
        required: false
        description: 数据间隔（如1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo）
      - name: start
        in: query
        type: string
        required: false
        description: 开始日期（YYYY-MM-DD格式）
      - name: end
        in: query
        type: string
        required: false
        description: 结束日期（YYYY-MM-DD格式）
      - name: prepost
        in: query
        type: boolean
        required: false
        description: 是否包含盘前盘后数据
      - name: actions
        in: query
        type: boolean
        required: false
        description: 是否包含公司行为
      - name: auto_adjust
        in: query
        type: boolean
        required: false
        description: 是否自动调整
    responses:
      200:
        description: 成功返回
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: array
              items:
                type: object
            columns:
              type: array
              items:
                type: string
      400:
        description: 参数错误
      500:
        description: 服务器错误
    """
    try:
        from yfinance import Ticker
        import pandas as pd
        from datetime import datetime
        
        # 获取基本参数
        symbol = request.args.get('symbol') or (request.json and request.json.get('symbol'))
        method = request.args.get('method') or (request.json and request.json.get('method')) or 'history'
        
        if not symbol:
            return jsonify({'success': False, 'error': '缺少symbol参数'}), 400
            
        ticker = Ticker(symbol)
        
        # 支持的method
        allowed_methods = [
            'history','info','actions','dividends','splits','financials','balance_sheet','cashflow',
            'quarterly_financials','quarterly_balance_sheet','quarterly_cashflow','earnings','quarterly_earnings',
            'sustainability','calendar','isin','options','institutional_holders','mutualfund_holders','major_holders',
            'recommendations','news','get_income_stmt','get_balance_sheet','get_cashflow','get_earnings_dates'
        ]
        if method not in allowed_methods:
            return jsonify({'success': False, 'error': f'不支持的method: {method}'}), 400
            
        # 获取通用参数
        def get_param(param_name, param_type=str, default=None):
            value = request.args.get(param_name) or (request.json and request.json.get(param_name))
            if value is None:
                return default
            if param_type == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif param_type == int:
                try:
                    return int(value)
                except:
                    return default
            elif param_type == float:
                try:
                    return float(value)
                except:
                    return default
            return value
            
        # 构建参数字典
        params = {}
        
        if method == 'history':
            # history方法的特殊参数
            period = get_param('period', str, '1y')
            interval = get_param('interval', str, '1d')
            start = get_param('start')
            end = get_param('end')
            prepost = get_param('prepost', bool, False)
            actions = get_param('actions', bool, True)
            auto_adjust = get_param('auto_adjust', bool, True)
            back_adjust = get_param('back_adjust', bool, False)
            repair = get_param('repair', bool, False)
            keepna = get_param('keepna', bool, False)
            proxy = get_param('proxy')
            rounding = get_param('rounding', bool, True)
            timeout = get_param('timeout', int, 10)
            session = get_param('session')
            progress = get_param('progress', bool, True)
            show_errors = get_param('show_errors', bool, True)
            
            # 构建参数字典
            params = {
                'period': period,
                'interval': interval,
                'prepost': prepost,
                'actions': actions,
                'auto_adjust': auto_adjust,
                'back_adjust': back_adjust,
                'repair': repair,
                'keepna': keepna,
                'rounding': rounding,
                'timeout': timeout,
                'progress': progress,
                'show_errors': show_errors
            }
            
            if start:
                params['start'] = start
            if end:
                params['end'] = end
            if proxy:
                params['proxy'] = proxy
            if session:
                params['session'] = session
                
            df = ticker.history(**params)
            
        elif method in ['actions', 'dividends', 'splits', 'financials', 'balance_sheet', 'cashflow', 
                       'quarterly_financials', 'quarterly_balance_sheet', 'quarterly_cashflow', 
                       'earnings', 'quarterly_earnings', 'calendar', 'recommendations']:
            # 这些方法支持start和end参数
            start = get_param('start')
            end = get_param('end')
            
            params = {}
            if start:
                params['start'] = start
            if end:
                params['end'] = end
                
            attr = getattr(ticker, method)
            if callable(attr):
                result = attr(**params)
            else:
                result = attr
                
        elif method in ['get_income_stmt', 'get_balance_sheet', 'get_cashflow']:
            # 新版财务接口支持start和end参数
            start = get_param('start')
            end = get_param('end')
            
            params = {}
            if start:
                params['start'] = start
            if end:
                params['end'] = end
                
            attr = getattr(ticker, method)
            if callable(attr):
                result = attr(**params)
            else:
                result = attr
                
        else:
            # 其他方法不需要额外参数
            attr = getattr(ticker, method)
            if callable(attr):
                result = attr()
            else:
                result = attr
                
        # 处理结果
        if method == 'history':
            if df.empty:
                return jsonify({'success': False, 'error': '未获取到数据'}), 400
            data = df.head(10).reset_index().to_dict(orient='records')
            columns = list(df.columns)
            return jsonify({'success': True, 'data': data, 'columns': columns})
        else:
            # DataFrame转dict
            if isinstance(result, pd.DataFrame):
                data = result.head(10).reset_index().to_dict(orient='records')
                columns = list(result.columns)
                return jsonify({'success': True, 'data': data, 'columns': columns})
            elif isinstance(result, (list, tuple)):
                return jsonify({'success': True, 'data': result, 'columns': []})
            elif isinstance(result, dict):
                return jsonify({'success': True, 'data': result, 'columns': list(result.keys())})
            else:
                return jsonify({'success': True, 'data': result, 'columns': []})
                
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/yfinance_test.html')
def yfinance_test_page():
    return render_template('yfinance_test.html')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 确保templates目录存在
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(debug=True, host='0.0.0.0', port=5000) 