import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class StockIndicator:
    """
    股票技术指标计算类
    基于通达信指标源码实现，用于计算主力资金进出、买卖信号等技术指标
    """
    
    def __init__(self, stock_data: pd.DataFrame, index_data: pd.DataFrame):
        """
        初始化股票指标计算器
        
        Args:
            stock_data: 股票数据，包含 OHLCV 数据
            index_data: 指数数据，包含 OHLC 数据
        """
        self.stock_data = stock_data.copy()
        self.index_data = index_data.copy()
        self.results = {}
        
        # 确保数据包含必要的列
        required_stock_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        required_index_cols = ['Open', 'High', 'Low', 'Close']
        
        if not all(col in self.stock_data.columns for col in required_stock_cols):
            raise ValueError("股票数据缺少必要的OHLCV列")
        if not all(col in self.index_data.columns for col in required_index_cols):
            raise ValueError("指数数据缺少必要的OHLC列")
    
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线 (EMA)
        
        Args:
            data: 输入数据序列
            period: 周期
            
        Returns:
            EMA序列
        """
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, data: pd.Series, period: int, weight: float = 1) -> pd.Series:
        """
        计算加权移动平均线 (SMA)
        
        Args:
            data: 输入数据序列
            period: 周期
            weight: 权重
            
        Returns:
            SMA序列
        """
        # 确保输入是 pandas.Series
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        alpha = weight / period
        return data.ewm(alpha=alpha, adjust=False).mean()
    
    def calculate_hhv(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算指定周期内的最高价 (HHV)
        
        Args:
            data: 输入数据序列
            period: 周期
            
        Returns:
            HHV序列
        """
        return data.rolling(window=period).max()
    
    def calculate_llv(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算指定周期内的最低价 (LLV)
        
        Args:
            data: 输入数据序列
            period: 周期
            
        Returns:
            LLV序列
        """
        return data.rolling(window=period).min()
    
    def calculate_ref(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算前N期的值 (REF)
        
        Args:
            data: 输入数据序列
            period: 前推期数
            
        Returns:
            REF序列
        """
        return data.shift(period)
    
    def calculate_cross(self, data1: pd.Series, data2) -> pd.Series:
        """
        计算金叉死叉信号 (CROSS)
        
        Args:
            data1: 数据序列1
            data2: 数据序列2 或标量值
            
        Returns:
            交叉信号序列
        """
        # 确保 data1 是 pandas.Series
        if not isinstance(data1, pd.Series):
            data1 = pd.Series(data1)
        
        # 如果 data2 是标量，转换为 Series
        if not isinstance(data2, pd.Series):
            data2 = pd.Series([data2] * len(data1), index=data1.index)
        
        return ((data1 > data2) & (data1.shift(1) <= data2.shift(1))).astype(int)
    
    def calculate_filter(self, condition: pd.Series, period: int) -> pd.Series:
        """
        过滤连续信号 (FILTER)
        
        Args:
            condition: 条件序列
            period: 过滤周期
            
        Returns:
            过滤后的信号序列
        """
        result = condition.copy()
        for i in range(1, len(condition)):
            if condition.iloc[i] and any(condition.iloc[max(0, i-period):i]):
                result.iloc[i] = False
        return result
    
    def calculate_bars_count(self, data: pd.Series) -> pd.Series:
        """
        计算数据长度 (BARSCOUNT)
        
        Args:
            data: 输入数据序列
            
        Returns:
            数据长度序列
        """
        return pd.Series(range(1, len(data) + 1), index=data.index)
    
    def calculate_avedev(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算平均绝对偏差 (AVEDEV)
        
        Args:
            data: 输入数据序列
            period: 周期
            
        Returns:
            AVEDEV序列
        """
        return data.rolling(window=period).apply(lambda x: np.mean(np.abs(x - np.mean(x))))
    
    def calculate_sum(self, data: pd.Series, period: int) -> pd.Series:
        """
        计算指定周期的和 (SUM)
        
        Args:
            data: 输入数据序列
            period: 周期
            
        Returns:
            SUM序列
        """
        # 确保输入是 pandas.Series
        if not isinstance(data, pd.Series):
            data = pd.Series(data)
        return data.rolling(window=period).sum()
    
    def calculate_count(self, condition: pd.Series, period: int) -> pd.Series:
        """
        计算指定周期内满足条件的数量 (COUNT)
        
        Args:
            condition: 条件序列
            period: 周期
            
        Returns:
            COUNT序列
        """
        return condition.rolling(window=period).sum()
    
    def calculate_all_indicators(self) -> Dict:
        """
        计算所有技术指标
        
        Returns:
            包含所有指标结果的字典
        """
        # 获取基础数据
        C = self.stock_data['Close']  # 收盘价
        H = self.stock_data['High']   # 最高价
        L = self.stock_data['Low']    # 最低价
        O = self.stock_data['Open']   # 开盘价
        VOL = self.stock_data['Volume']  # 成交量
        
        # 指数数据
        INDEXC = self.index_data['Close']  # 指数收盘价
        INDEXH = self.index_data['High']   # 指数最高价
        INDEXL = self.index_data['Low']    # 指数最低价
        
        # 假设流通股本（实际应用中需要从数据源获取）
        CAPITAL = VOL * 100  # 简化处理
        
        # 计算V1-V4系列指标
        V1 = (C * 2 + H + L) / 4 * 10
        V2 = self.calculate_ema(V1, 13) - self.calculate_ema(V1, 34)
        V3 = self.calculate_ema(V2, 5)
        V4 = 2 * (V2 - V3) * 5.5
        
        # 计算V5-V7系列指标（大盘相关）
        V5 = (self.calculate_hhv(INDEXH, 8) - INDEXC) / (self.calculate_hhv(INDEXH, 8) - self.calculate_llv(INDEXL, 8)) * 8
        V6 = self.calculate_ema(3 * V5 - 2 * self.calculate_sma(V5, 18, 1), 5)
        V7 = (INDEXC - self.calculate_llv(INDEXL, 8)) / (self.calculate_hhv(INDEXH, 8) - self.calculate_llv(INDEXL, 8)) * 10
        
        # 计算V8-VB系列指标（大盘动量）
        V8 = (INDEXC * 2 + INDEXH + INDEXL) / 4
        V9 = self.calculate_ema(V8, 13) - self.calculate_ema(V8, 34)
        VA = self.calculate_ema(V9, 3)
        VB = (V9 - VA) / 2
        
        # 计算V11-V12系列指标（个股强弱动量）
        price_range = (C - self.calculate_llv(L, 55)) / (self.calculate_hhv(H, 55) - self.calculate_llv(L, 55)) * 100
        V11 = 3 * self.calculate_sma(price_range, 5, 1) - 2 * self.calculate_sma(self.calculate_sma(price_range, 5, 1), 3, 1)
        V12 = (self.calculate_ema(V11, 3) - self.calculate_ref(self.calculate_ema(V11, 3), 1)) / self.calculate_ref(self.calculate_ema(V11, 3), 1) * 100
        
        # 计算买入信号
        buy_condition = (self.calculate_ema(V11, 3) <= 13) & (V12 > 13)
        BB1 = buy_condition & self.calculate_filter(buy_condition, 10)
        
        # 计算卖出信号
        sell_condition = (self.calculate_ema(V11, 3) > 60) & (self.calculate_ema(V11, 3) > self.calculate_ref(self.calculate_ema(V11, 3), 1))
        CC1 = (self.calculate_ema(V11, 3) >= 90) & V12 & self.calculate_filter((self.calculate_ema(V11, 3) >= 90) & V12, 10)
        
        # 计算AA-C4系列指标（价格加权和趋势）
        AA = (O + H + L + C) / 4
        BB = AA.rolling(window=3).mean()
        
        # 修复：确保使用 pandas.Series 而不是 numpy.ndarray
        AA_prev = self.calculate_ref(AA, 1)
        up_condition = AA > AA_prev
        down_condition = AA < AA_prev
        
        # 使用 pandas 的 where 方法
        up_volume = pd.Series(np.where(up_condition, AA * VOL, 0), index=AA.index)
        down_volume = pd.Series(np.where(down_condition, AA * VOL, 0), index=AA.index)
        
        CC = self.calculate_sum(up_volume, 4) / self.calculate_sum(down_volume, 4)
        DD = self.calculate_ref(100 - (100 / (1 + CC)), 1)
        
        # 计算不同周期的趋势指标
        A1 = self.calculate_hhv(AA, 10)
        A2 = self.calculate_llv(AA, 30)
        A3 = A1 - A2
        A4 = self.calculate_ema((AA - A2) / A3, 1) * 100
        
        B1 = self.calculate_hhv(AA, 16)
        B2 = self.calculate_llv(AA, 90)
        B3 = B1 - B2
        B4 = self.calculate_ema((AA - B2) / B3, 1) * 100  # 中线趋势
        
        C1 = self.calculate_hhv(AA, 30)
        C2 = self.calculate_llv(AA, 240)
        C3 = C1 - C2
        C4 = self.calculate_ema((AA - C2) / C3, 1) * 100
        
        # 计算VAR系列指标（超级主力建仓信号）
        VARE = self.calculate_ref(L, 1) * 0.9
        VARF = L * 0.9
        VAR10 = (VARF * VOL + VARE * (CAPITAL - VOL)) / CAPITAL
        VAR11 = self.calculate_ema(VAR10, 30)
        VAR12 = C - self.calculate_ref(C, 1)
        
        # 修复：确保使用 pandas.Series
        VAR13 = pd.Series(np.maximum(VAR12, 0), index=VAR12.index)
        VAR14 = pd.Series(np.abs(VAR12), index=VAR12.index)
        VAR15 = self.calculate_sma(VAR13, 7, 1) / self.calculate_sma(VAR14, 7, 1) * 100
        VAR16 = self.calculate_sma(VAR13, 13, 1) / self.calculate_sma(VAR14, 13, 1) * 100
        VAR17 = self.calculate_bars_count(C)
        
        # 修复：确保使用 pandas.Series
        VAR18 = self.calculate_sma(pd.Series(np.maximum(VAR12, 0), index=VAR12.index), 6, 1) / self.calculate_sma(pd.Series(np.abs(VAR12), index=VAR12.index), 6, 1) * 100
        VAR19 = (-200) * (self.calculate_hhv(H, 60) - C) / (self.calculate_hhv(H, 60) - self.calculate_llv(L, 60)) + 100
        VAR1A = (C - self.calculate_llv(L, 15)) / (self.calculate_hhv(H, 15) - self.calculate_llv(L, 15)) * 100
        VAR1B = self.calculate_sma((self.calculate_sma(VAR1A, 4, 1) - 50) * 2, 3, 1)
        VAR1C = (INDEXC - self.calculate_llv(INDEXL, 14)) / (self.calculate_hhv(INDEXH, 14) - self.calculate_llv(INDEXL, 14)) * 100
        VAR1D = self.calculate_sma(VAR1C, 4, 1)
        VAR1E = self.calculate_sma(VAR1D, 3, 1)
        VAR1F = (self.calculate_hhv(H, 30) - C) / C * 100
        
        # 超级主力建仓条件
        VAR20 = (VAR18 <= 25) & (VAR19 < -95) & (VAR1F > 20) & (VAR1B < -30) & (VAR1E < 30) & (VAR11 - C >= -0.25) & (VAR15 < 22) & (VAR16 < 28) & (VAR17 > 50)
        
        # 布林带相关计算
        VAR21 = (H + L + C) / 3
        VAR22 = (VAR21 - VAR21.rolling(window=14).mean()) / (0.015 * self.calculate_avedev(VAR21, 14))
        VAR23 = (VAR21 - VAR21.rolling(window=70).mean()) / (0.015 * self.calculate_avedev(VAR21, 70))
        
        # 超级主力建仓信号
        super_buy_signal = self.calculate_cross(VAR20, 0.5) & (self.calculate_count(VAR20 == 1, 10) == 1)
        
        # 存储所有计算结果
        self.results = {
            'V1': V1, 'V2': V2, 'V3': V3, 'V4': V4,
            'V5': V5, 'V6': V6, 'V7': V7,
            'V8': V8, 'V9': V9, 'VA': VA, 'VB': VB,
            'V11': V11, 'V12': V12,
            'buy_signal': buy_condition,
            'BB1': BB1,
            'sell_signal': sell_condition,
            'CC1': CC1,
            'AA': AA, 'BB': BB, 'CC': CC, 'DD': DD,
            'A1': A1, 'A2': A2, 'A3': A3, 'A4': A4,
            'B1': B1, 'B2': B2, 'B3': B3, 'B4': B4,  # 中线趋势
            'C1': C1, 'C2': C2, 'C3': C3, 'C4': C4,
            'VAR20': VAR20,
            'super_buy_signal': super_buy_signal,
            'price': C,
            'volume': VOL
        }
        
        return self.results
    
    def get_signals(self) -> Dict:
        """
        获取买卖信号
        
        Returns:
            包含买卖信号的字典
        """
        if not self.results:
            self.calculate_all_indicators()
        
        signals = {
            'buy_signals': self.results['BB1'],
            'sell_signals': self.results['CC1'],
            'super_buy_signals': self.results['super_buy_signal'],
            'mid_trend': self.results['B4']
        }
        
        return signals
    
    def get_summary(self) -> Dict:
        """
        获取指标摘要信息
        
        Returns:
            指标摘要字典
        """
        if not self.results:
            self.calculate_all_indicators()
        
        latest = {k: v.iloc[-1] if hasattr(v, 'iloc') else v for k, v in self.results.items()}
        
        # 确保布尔值能正确序列化
        buy_signal_active = bool(latest['BB1']) if hasattr(latest['BB1'], '__bool__') else False
        sell_signal_active = bool(latest['CC1']) if hasattr(latest['CC1'], '__bool__') else False
        super_buy_signal_active = bool(latest['super_buy_signal']) if hasattr(latest['super_buy_signal'], '__bool__') else False
        
        summary = {
            'current_price': float(latest['price']),
            'mid_trend_value': float(latest['B4']),
            'v11_value': float(latest['V11']),
            'v12_value': float(latest['V12']),
            'buy_signal_active': buy_signal_active,
            'sell_signal_active': sell_signal_active,
            'super_buy_signal_active': super_buy_signal_active,
            'trend_strength': '强' if latest['B4'] > 70 else '中' if latest['B4'] > 30 else '弱'
        }
        
        return summary 