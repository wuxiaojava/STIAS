import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import time
import ssl
import urllib3
warnings.filterwarnings('ignore')

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置SSL上下文以处理证书问题
import urllib.request
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 可选导入 yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("警告: yfinance 未安装，将无法获取Yahoo Finance数据")

# 可选导入 akshare
try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告: akshare 未安装，将无法获取AKShare数据")

class DataLoader:
    """
    数据加载器类
    用于获取股票和指数数据
    支持多种数据源：yfinance、akshare
    """
    
    def __init__(self, data_source: str = "yfinance"):
        """
        初始化数据加载器
        
        Args:
            data_source: 数据源，可选 "yfinance" 或 "akshare"
        """
        self.data_source = data_source
        
        # 检查数据源可用性
        if data_source == "yfinance" and not YFINANCE_AVAILABLE:
            raise ImportError("yfinance 未安装，无法使用Yahoo Finance数据源")
        elif data_source == "akshare" and not AKSHARE_AVAILABLE:
            raise ImportError("akshare 未安装，无法使用AKShare数据源")
        
        # 如果使用AKShare，配置网络环境
        if data_source == "akshare":
            self._setup_network_environment()
            print("AKShare数据源已配置网络环境和重试机制")
    
    def get_stock_data(self, symbol: str, period: str = "1y", realtime_only: bool = False) -> pd.DataFrame:
        """
        获取股票数据
        Args:
            symbol: 股票代码（如 'AAPL', '000001.SZ'）
            period: 数据周期
            realtime_only: 是否只查实时数据
        Returns:
            DataFrame
        """
        if self.data_source == "yfinance":
            return self._get_stock_data_yfinance(symbol, period)
        elif self.data_source == "akshare":
            ak_symbol = self._convert_symbol_for_akshare(symbol)
            if realtime_only:
                # 单只A股实时行情
                try:
                    df = ak.stock_zh_a_quote(symbol=ak_symbol)
                    # 标准化
                    df = df.rename(columns={
                        '最新价': 'Close', '开盘价': 'Open', '最高价': 'High', '最低价': 'Low', '成交量': 'Volume',
                        '最新': 'Close', '开盘': 'Open', '最高': 'High', '最低': 'Low', '成交量(手)': 'Volume'
                    })
                    # 只保留一行
                    if isinstance(df, pd.DataFrame) and not df.empty:
                        df = df.iloc[[0]]
                        df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
                        df['High'] = pd.to_numeric(df['High'], errors='coerce')
                        df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
                        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
                        df.index = [pd.Timestamp.now()]
                    return df
                except Exception as e:
                    print(f"akshare实时股票接口失败: {e}")
                    return pd.DataFrame()
            else:
                return self._normalize_akshare_data(self._get_akshare_stock_hist(ak_symbol, period))
        else:
            raise ValueError(f"不支持的数据源: {self.data_source}")
    
    def _get_stock_data_yfinance(self, symbol: str, period: str) -> pd.DataFrame:
        """使用yfinance获取股票数据"""
        if not YFINANCE_AVAILABLE:
            print(f"yfinance 未安装，无法获取股票 {symbol} 的数据")
            return pd.DataFrame()
            
        try:
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                raise ValueError(f"无法获取股票 {symbol} 的数据")
            
            # 确保列名正确
            data.columns = [col.title() for col in data.columns]
            
            return data
            
        except Exception as e:
            print(f"获取股票数据时出错: {e}")
            return pd.DataFrame()
    
    def _get_stock_data_akshare(self, symbol: str, period: str) -> pd.DataFrame:
        """使用akshare获取股票数据，带重试和备选方案"""
        if not AKSHARE_AVAILABLE:
            print(f"akshare 未安装，无法获取股票 {symbol} 的数据")
            return pd.DataFrame()
            
        # 处理股票代码格式
        ak_symbol = self._convert_symbol_for_akshare(symbol)
        
        # 如果不是A股代码，直接使用yfinance
        if not self._is_chinese_stock(ak_symbol):
            print(f"检测到非A股代码 {symbol}，使用yfinance获取数据")
            return self._get_stock_data_yfinance(symbol, period)
        
        # 多种获取方式，按优先级尝试
        methods = [
            self._get_akshare_stock_realtime,
            self._get_akshare_stock_hist,
            self._get_akshare_stock_daily,
        ]
        
        for i, method in enumerate(methods):
            try:
                print(f"尝试方法 {i+1}: {method.__name__}")
                data = method(ak_symbol, period)
                
                if not data.empty:
                    print(f"成功获取数据: {len(data)} 条记录")
                    return self._normalize_akshare_data(data)
                    
            except Exception as e:
                print(f"方法 {i+1} 失败: {str(e)[:100]}...")
                continue
        
        # 所有AKShare方法都失败，尝试yfinance作为备选
        print(f"AKShare获取失败，尝试使用yfinance获取 {symbol} 数据")
        try:
            return self._get_stock_data_yfinance(symbol, period)
        except Exception as e:
            print(f"yfinance备选方案也失败: {e}")
            return pd.DataFrame()
    
    def _is_chinese_stock(self, symbol: str) -> bool:
        """判断是否为中国A股代码"""
        if len(symbol) == 6 and symbol.isdigit():
            # 上海: 60xxxx, 688xxx (科创板)
            # 深圳: 00xxxx, 30xxxx (创业板), 002xxx (中小板)
            return (symbol.startswith('60') or symbol.startswith('688') or 
                   symbol.startswith('00') or symbol.startswith('30'))
        return False
    
    def _setup_network_environment(self):
        """配置网络环境以处理AKShare的连接问题"""
        try:
            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # 配置requests会话
            session = requests.Session()
            
            # 配置重试策略
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            
            # 设置请求头
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            })
            
            # 禁用SSL验证
            session.verify = False
            
            return session
            
        except ImportError:
            return None
    
    def _safe_akshare_call(self, func, *args, **kwargs):
        """安全的AKShare调用，带重试机制"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # 每次调用前休眠
                if attempt > 0:
                    print(f"第 {attempt + 1} 次重试...")
                    time.sleep(retry_delay * (attempt + 1))
                
                # 调用AKShare函数
                result = func(*args, **kwargs)
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # 检查是否是网络相关错误
                if any(keyword in error_msg.lower() for keyword in 
                       ['ssl', 'connection', 'timeout', 'httpsconnectionpool', 'max retries']):
                    print(f"网络错误 (尝试 {attempt + 1}/{max_retries}): {error_msg[:100]}...")
                    
                    if attempt == max_retries - 1:
                        raise Exception(f"网络连接失败，已重试 {max_retries} 次")
                    continue
                else:
                    # 非网络错误，直接抛出
                    raise e
        
        raise Exception("未知错误")
    
    def _get_akshare_stock_realtime(self, symbol: str, period: str) -> pd.DataFrame:
        """使用akshare实时数据接口"""
        # 将周期转换为天数
        period_days = self._convert_period_to_days(period)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y%m%d')
        
        # 添加延时避免请求过快
        time.sleep(1)
        
        # 安全调用akshare
        data = self._safe_akshare_call(
            ak.stock_zh_a_hist,
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date,
            adjust=""
        )
        return data
    
    def _get_akshare_stock_hist(self, symbol: str, period: str) -> pd.DataFrame:
        """使用akshare历史数据接口"""
        period_days = self._convert_period_to_days(period)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y%m%d')
        
        time.sleep(1)
        
        # 安全调用akshare
        data = self._safe_akshare_call(
            ak.stock_zh_a_hist,
            symbol=symbol, 
            period="daily",
            start_date=start_date, 
            end_date=end_date,
            adjust="qfq"
        )
        return data
    
    def _get_akshare_stock_daily(self, symbol: str, period: str) -> pd.DataFrame:
        """使用akshare日线数据接口"""
        try:
            time.sleep(1)
            
            # 安全调用akshare
            data = self._safe_akshare_call(ak.stock_zh_a_daily, symbol=symbol, adjust="qfq")
            
            # 筛选时间范围
            if not data.empty and '日期' in data.columns:
                period_days = self._convert_period_to_days(period)
                start_date = datetime.now() - timedelta(days=period_days)
                data['日期'] = pd.to_datetime(data['日期'])
                data = data[data['日期'] >= start_date]
                
            return data
            
        except Exception as e:
            # 如果daily接口不存在，返回空DataFrame
            raise e
    
    def get_index_data(self, symbol: str, period: str = "1y", realtime_only: bool = False) -> pd.DataFrame:
        """
        获取指数数据
        Args:
            symbol: 指数代码
            period: 数据周期
            realtime_only: 是否只查实时数据
        Returns:
            DataFrame
        """
        if self.data_source == "yfinance":
            return self._normalize_yahoo_index_data(self._get_index_data_yfinance(symbol, period))
        elif self.data_source == "akshare":
            ak_symbol = self._convert_index_symbol_for_akshare(symbol)
            if realtime_only:
                try:
                    df = ak.stock_zh_index_spot()
                    # 过滤目标指数
                    df = df[df['代码'] == ak_symbol]
                    df = df.rename(columns={
                        '最新价': 'Close', '开盘价': 'Open', '最高价': 'High', '最低价': 'Low',
                        '最新': 'Close', '开盘': 'Open', '最高': 'High', '最低': 'Low'
                    })
                    if not df.empty:
                        df = df.iloc[[0]]
                        df['Open'] = pd.to_numeric(df['Open'], errors='coerce')
                        df['High'] = pd.to_numeric(df['High'], errors='coerce')
                        df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
                        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                        df['Volume'] = 0
                        df.index = [pd.Timestamp.now()]
                    return df
                except Exception as e:
                    print(f"akshare实时指数接口失败: {e}")
                    return pd.DataFrame()
            else:
                return self._normalize_akshare_index_data(self._get_akshare_index_daily(ak_symbol, period))
        else:
            raise ValueError(f"不支持的数据源: {self.data_source}")

    def _get_index_data_yfinance(self, symbol: str, period: str) -> pd.DataFrame:
        """使用yfinance获取指数数据"""
        if not YFINANCE_AVAILABLE:
            print(f"yfinance 未安装，无法获取指数 {symbol} 的数据")
            return pd.DataFrame()
            
        try:
            # 使用yfinance获取指数数据
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                raise ValueError(f"无法获取指数 {symbol} 的数据")
            
            # 确保列名正确
            data.columns = [col.title() for col in data.columns]
            
            return data
            
        except Exception as e:
            print(f"获取指数数据时出错: {e}")
            return pd.DataFrame()
    
    def _get_index_data_akshare(self, symbol: str, period: str) -> pd.DataFrame:
        """使用akshare获取指数数据，带重试和备选方案"""
        if not AKSHARE_AVAILABLE:
            print(f"akshare 未安装，无法获取指数 {symbol} 的数据")
            return pd.DataFrame()
        
        # 处理指数代码格式
        ak_symbol = self._convert_index_symbol_for_akshare(symbol)
        
        # 如果不是中国指数，直接使用yfinance
        if not (ak_symbol.startswith('sh') or ak_symbol.startswith('sz')):
            print(f"检测到非中国指数 {symbol}，使用yfinance获取数据")
            return self._get_index_data_yfinance(symbol, period)
        
        # 多种获取方式，按优先级尝试
        methods = [
            self._get_akshare_index_daily,
            self._get_akshare_index_hist,
        ]
        
        for i, method in enumerate(methods):
            try:
                print(f"尝试指数方法 {i+1}: {method.__name__}")
                data = method(ak_symbol, period)
                
                if not data.empty:
                    print(f"成功获取指数数据: {len(data)} 条记录")
                    return self._normalize_akshare_index_data(data)
                    
            except Exception as e:
                print(f"指数方法 {i+1} 失败: {str(e)[:100]}...")
                continue
        
        # 所有AKShare方法都失败，尝试yfinance作为备选
        print(f"AKShare获取指数失败，尝试使用yfinance获取 {symbol} 数据")
        try:
            return self._get_index_data_yfinance(symbol, period)
        except Exception as e:
            print(f"yfinance备选方案也失败: {e}")
            return pd.DataFrame()
    
    def _get_akshare_index_daily(self, ak_symbol: str, period: str) -> pd.DataFrame:
        """使用akshare获取指数日线数据"""
        try:
            time.sleep(1)
            
            # 安全调用akshare
            data = self._safe_akshare_call(ak.stock_zh_index_daily, symbol=ak_symbol)
            
            # 筛选时间范围
            if not data.empty and '日期' in data.columns:
                period_days = self._convert_period_to_days(period)
                start_dt = datetime.now() - timedelta(days=period_days)
                data['日期'] = pd.to_datetime(data['日期'])
                data = data[data['日期'] >= start_dt]
            
            return data
            
        except Exception as e:
            raise e
    
    def _get_akshare_index_hist(self, ak_symbol: str, period: str) -> pd.DataFrame:
        """使用akshare获取指数历史数据"""
        try:
            time.sleep(1)
            
            # 将周期转换为天数
            period_days = self._convert_period_to_days(period)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y%m%d')
            
            # 安全调用akshare
            data = self._safe_akshare_call(
                ak.index_zh_a_hist, 
                symbol=ak_symbol, 
                period="daily",
                start_date=start_date, 
                end_date=end_date
            )
            
            return data
            
        except Exception as e:
            raise e
    
    def _convert_period_to_days(self, period: str) -> int:
        """将周期字符串转换为天数"""
        period_map = {
            '1mo': 30,
            '3mo': 90,
            '6mo': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825,
            '1d': 1,
            '5d': 5
        }
        return period_map.get(period, 365)
    
    def _convert_symbol_for_akshare(self, symbol: str) -> str:
        """将股票代码转换为akshare格式"""
        # 如果已经是akshare格式，直接返回
        if len(symbol) == 6 and symbol.isdigit():
            return symbol
        
        # 处理yfinance格式转akshare格式
        if '.SS' in symbol:
            return symbol.replace('.SS', '')
        elif '.SZ' in symbol:
            return symbol.replace('.SZ', '')
        elif symbol.isdigit() and len(symbol) == 6:
            return symbol
        else:
            # 对于美股等，保持原格式
            return symbol
    
    def _convert_index_symbol_for_akshare(self, symbol: str) -> str:
        """将指数代码转换为akshare格式"""
        index_map = {
            '000001.SS': 'sh000001',  # 上证指数
            '399001.SZ': 'sz399001',  # 深证成指
            '000300.SS': 'sh000300',  # 沪深300
            '000905.SS': 'sh000905',  # 中证500
            '399006.SZ': 'sz399006',  # 创业板指
        }
        return index_map.get(symbol, symbol)
    
    def _normalize_akshare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化akshare股票数据格式"""
        try:
            # akshare的列名映射
            column_map = {
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close', 
                '最高': 'High',
                '最低': 'Low',
                '成交量': 'Volume',
                '成交额': 'Amount'
            }
            
            # 重命名列
            data = data.rename(columns=column_map)
            
            # 设置日期为索引
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)
            
            # 确保数据类型正确
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            return data
            
        except Exception as e:
            print(f"标准化akshare数据时出错: {e}")
            return data
    
    def _normalize_akshare_index_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化akshare指数数据格式"""
        try:
            # akshare指数的列名映射
            column_map = {
                '日期': 'Date',
                '开盘': 'Open',
                '收盘': 'Close',
                '最高': 'High', 
                '最低': 'Low'
            }
            
            # 重命名列
            data = data.rename(columns=column_map)
            
            # 设置日期为索引
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)
            
            # 确保数据类型正确
            for col in ['Open', 'High', 'Low', 'Close']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # 指数数据通常没有成交量，添加占位符
            if 'Volume' not in data.columns:
                data['Volume'] = 0
            
            return data
            
        except Exception as e:
            print(f"标准化akshare指数数据时出错: {e}")
            return data

    def _normalize_yahoo_index_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化yahoo指数数据格式"""
        try:
            # Yahoo返回的通常已经是Open/High/Low/Close/Volume
            column_map = {
                'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume',
                'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close', 'Volume': 'Volume'
            }
            data = data.rename(columns=column_map)
            # 设置索引为Date
            if 'Date' in data.columns:
                data['Date'] = pd.to_datetime(data['Date'])
                data.set_index('Date', inplace=True)
            # 确保数据类型
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            # Yahoo指数有的没有Volume，补0
            if 'Volume' not in data.columns:
                data['Volume'] = 0
            return data
        except Exception as e:
            print(f"标准化yahoo指数数据时出错: {e}")
            return data
    
    def get_sample_data(self) -> tuple:
        """
        获取示例数据（用于演示）
        
        Returns:
            (stock_data, index_data) 元组
        """
        if YFINANCE_AVAILABLE:
            # 获取苹果股票数据作为示例
            stock_data = self.get_stock_data('AAPL', '1y')
            
            # 获取标普500指数数据作为示例
            index_data = self.get_index_data('^GSPC', '1y')
        else:
            # 如果没有 yfinance，使用 mock 数据
            print("使用模拟数据作为示例")
            stock_data, index_data = self.get_mock_data(200)
        
        return stock_data, index_data
    
    def get_chinese_stock_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """
        获取中国股票数据
        
        Args:
            symbol: 股票代码（如 '000001.SZ', '600000.SS'）
            period: 数据周期
            
        Returns:
            包含OHLCV数据的DataFrame
        """
        try:
            # 中国股票代码格式
            if not symbol.endswith(('.SZ', '.SS')):
                if symbol.startswith('6'):
                    symbol += '.SS'  # 上海证券交易所
                else:
                    symbol += '.SZ'  # 深圳证券交易所
            
            return self.get_stock_data(symbol, period)
            
        except Exception as e:
            print(f"获取中国股票数据时出错: {e}")
            return pd.DataFrame()
    
    def get_chinese_index_data(self, symbol: str = "000001.SS", period: str = "1y") -> pd.DataFrame:
        """
        获取中国指数数据
        
        Args:
            symbol: 指数代码（默认上证指数）
            period: 数据周期
            
        Returns:
            包含OHLC数据的DataFrame
        """
        # 常见中国指数代码
        index_mapping = {
            'shanghai': '000001.SS',  # 上证指数
            'shenzhen': '399001.SZ',  # 深证成指
            'csi300': '000300.SS',    # 沪深300
            'csi500': '000905.SS',    # 中证500
            'gem': '399006.SZ'        # 创业板指
        }
        
        if symbol.lower() in index_mapping:
            symbol = index_mapping[symbol.lower()]
        
        return self.get_index_data(symbol, period)
    
    def validate_data(self, data: pd.DataFrame, data_type: str = "stock") -> bool:
        """
        验证数据完整性
        
        Args:
            data: 数据DataFrame
            data_type: 数据类型（'stock' 或 'index'）
            
        Returns:
            数据是否有效
        """
        if data.empty:
            return False
        
        if data_type == "stock":
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        else:
            required_cols = ['Open', 'High', 'Low', 'Close']
        
        # 检查必要列是否存在
        if not all(col in data.columns for col in required_cols):
            return False
        
        # 检查是否有足够的数据点（至少100个）
        if len(data) < 100:
            return False
        
        # 检查是否有空值
        if data[required_cols].isnull().any().any():
            return False
        
        return True
    
    def get_available_symbols(self) -> dict:
        """
        获取可用的股票和指数代码示例
        
        Returns:
            包含可用代码的字典
        """
        return {
            'us_stocks': [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL'
            ],
            'us_indices': [
                '^GSPC',  # 标普500
                '^DJI',   # 道琼斯
                '^IXIC',  # 纳斯达克
                '^RUT',   # 罗素2000
                '^VIX'    # 恐慌指数
            ],
            'chinese_stocks': [
                '000001.SZ',  # 平安银行
                '000002.SZ',  # 万科A
                '600000.SS',  # 浦发银行
                '600036.SS',  # 招商银行
                '000858.SZ',  # 五粮液
                '002415.SZ',  # 海康威视
                '600519.SS',  # 贵州茅台
                '000725.SZ'   # 京东方A
            ],
            'chinese_indices': [
                '000001.SS',  # 上证指数
                '399001.SZ',  # 深证成指
                '000300.SS',  # 沪深300
                '000905.SS',  # 中证500
                '399006.SZ'   # 创业板指
            ]
        } 

    def get_mock_data(self, n: int = 200) -> tuple:
        """
        生成模拟股票和指数数据，专门设计来展示各种买卖信号场景
        Args:
            n: 数据点数量
        Returns:
            (stock_data, index_data) 元组
        """
        import numpy as np
        import pandas as pd
        import datetime
        
        np.random.seed(42)  # 确保结果可重现
        base = pd.date_range(datetime.datetime.today() - pd.Timedelta(days=n), periods=n, freq='B')
        
        # 创建包含多个买卖信号场景的价格序列
        price = np.zeros(n)
        volume = np.zeros(n)
        
        # 场景1: 初始下跌阶段 (0-30天) - 为买入信号做准备
        price[0] = 100
        for i in range(1, 30):
            # 持续下跌，成交量放大
            price[i] = price[i-1] * (1 + np.random.normal(-0.02, 0.01))
            volume[i] = np.random.randint(150000, 250000)
        
        # 场景2: 买入信号触发 (30-40天) - V11<=13, V12>13
        for i in range(30, 40):
            # 价格开始反弹，成交量继续放大
            price[i] = price[i-1] * (1 + np.random.normal(0.015, 0.008))
            volume[i] = np.random.randint(200000, 300000)
        
        # 场景3: 上涨阶段 (40-80天) - 持续上涨
        for i in range(40, 80):
            # 稳步上涨
            price[i] = price[i-1] * (1 + np.random.normal(0.01, 0.005))
            volume[i] = np.random.randint(120000, 180000)
        
        # 场景4: 超级买入信号 (80-90天) - 多重条件满足
        for i in range(80, 90):
            # 加速上涨，成交量暴增
            price[i] = price[i-1] * (1 + np.random.normal(0.025, 0.01))
            volume[i] = np.random.randint(300000, 400000)
        
        # 场景5: 高位震荡 (90-120天) - 为卖出信号做准备
        for i in range(90, 120):
            # 高位震荡，成交量适中
            price[i] = price[i-1] * (1 + np.random.normal(0.002, 0.015))
            volume[i] = np.random.randint(100000, 150000)
        
        # 场景6: 卖出信号触发 (120-130天) - V11>=90, V12>0
        for i in range(120, 130):
            # 开始下跌，成交量放大
            price[i] = price[i-1] * (1 + np.random.normal(-0.015, 0.008))
            volume[i] = np.random.randint(180000, 250000)
        
        # 场景7: 下跌阶段 (130-160天)
        for i in range(130, 160):
            # 持续下跌
            price[i] = price[i-1] * (1 + np.random.normal(-0.008, 0.005))
            volume[i] = np.random.randint(120000, 180000)
        
        # 场景8: 再次买入信号 (160-170天)
        for i in range(160, 170):
            # 再次反弹
            price[i] = price[i-1] * (1 + np.random.normal(0.012, 0.006))
            volume[i] = np.random.randint(200000, 280000)
        
        # 场景9: 最终阶段 (170-200天) - 平稳上涨
        for i in range(170, n):
            # 平稳上涨
            price[i] = price[i-1] * (1 + np.random.normal(0.005, 0.003))
            volume[i] = np.random.randint(100000, 150000)
        
        # 生成OHLC数据
        high = price + np.random.rand(n) * 2
        low = price - np.random.rand(n) * 1.5
        open_ = price + np.random.randn(n) * 0.5
        close = price + np.random.randn(n) * 0.3
        
        # 确保OHLC逻辑正确
        for i in range(n):
            high[i] = max(high[i], open_[i], close[i])
            low[i] = min(low[i], open_[i], close[i])
        
        stock_data = pd.DataFrame({
            'Open': open_,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume.astype(int)
        }, index=base)
        
        # 生成指数数据 - 与股票数据相关但有差异
        idx_price = price * 0.8 + np.random.randn(n) * 3  # 指数波动相对较小
        idx_high = idx_price + np.random.rand(n) * 1.5
        idx_low = idx_price - np.random.rand(n) * 1.5
        idx_open = idx_price + np.random.randn(n) * 0.3
        idx_close = idx_price + np.random.randn(n) * 0.2
        
        # 确保指数OHLC逻辑正确
        for i in range(n):
            idx_high[i] = max(idx_high[i], idx_open[i], idx_close[i])
            idx_low[i] = min(idx_low[i], idx_open[i], idx_close[i])
        
        index_data = pd.DataFrame({
            'Open': idx_open,
            'High': idx_high,
            'Low': idx_low,
            'Close': idx_close
        }, index=base)
        
        return stock_data, index_data 

    def get_stock_name(self, symbol: str) -> str:
        """
        根据股票代码获取股票名称
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票名称，如果未找到则返回股票代码本身
        """
        if not YFINANCE_AVAILABLE:
            return symbol
            
        try:
            # 使用yfinance获取股票信息
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 尝试获取公司名称
            if 'longName' in info and info['longName']:
                return f"{info['longName']} ({symbol})"
            elif 'shortName' in info and info['shortName']:
                return f"{info['shortName']} ({symbol})"
            else:
                return symbol
                
        except Exception as e:
            print(f"获取股票 {symbol} 信息时出错: {e}")
            return symbol

    def search_stocks(self, keyword: str) -> list:
        """
        根据关键词搜索股票
        
        Args:
            keyword: 搜索关键词（可以是股票代码、公司名称或中文名称）
            
        Returns:
            匹配的股票列表，每个元素包含代码和名称
        """
        if not YFINANCE_AVAILABLE:
            return []
            
        try:
            # 使用yfinance搜索股票
            import yfinance as yf
            
            # 搜索股票
            search_results = yf.Tickers(keyword)
            
            results = []
            for ticker in search_results.tickers:
                try:
                    info = ticker.info
                    if info and 'symbol' in info:
                        symbol = info['symbol']
                        name = info.get('longName', info.get('shortName', symbol))
                        results.append({
                            'code': symbol,
                            'name': f"{name} ({symbol})"
                        })
                except:
                    continue
                    
            return results[:10]  # 限制返回前10个结果
            
        except Exception as e:
            print(f"搜索股票时出错: {e}")
            return []

    def get_popular_stocks(self, market: str = 'us') -> list:
        """
        获取热门股票列表
        
        Args:
            market: 市场类型 ('us' 或 'cn')
            
        Returns:
            热门股票列表
        """
        if market == 'us':
            # 美股热门股票
            popular_symbols = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'JPM', 'JNJ', 'PG', 'UNH', 'HD', 'MA', 'V', 'PYPL'
            ]
        else:
            # A股热门股票
            popular_symbols = [
                '000001.SZ', '000002.SZ', '600000.SS', '600036.SS', '000858.SZ',
                '002415.SZ', '600519.SS', '000725.SZ', '300750.SZ', '002594.SZ'
            ]
        
        results = []
        for symbol in popular_symbols:
            name = self.get_stock_name(symbol)
            results.append({
                'code': symbol,
                'name': name
            })
        
        return results

    def get_stock_suggestions(self, partial_symbol: str) -> list:
        """
        根据部分股票代码提供建议
        
        Args:
            partial_symbol: 部分股票代码
            
        Returns:
            匹配的股票建议列表
        """
        if not partial_symbol:
            return []
            
        # 常见股票代码模式
        suggestions = []
        
        # 美股模式
        if len(partial_symbol) <= 4 and partial_symbol.isalpha():
            # 可能是美股代码
            common_us_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
            for stock in common_us_stocks:
                if stock.startswith(partial_symbol.upper()):
                    name = self.get_stock_name(stock)
                    suggestions.append({'code': stock, 'name': name})
        
        # A股模式
        elif partial_symbol.isdigit() and len(partial_symbol) <= 6:
            # 可能是A股代码
            if partial_symbol.startswith('6'):
                # 上海证券交易所
                suggestions.append({'code': f"{partial_symbol}.SS", 'name': f"上海股票 {partial_symbol}"})
            elif partial_symbol.startswith('0') or partial_symbol.startswith('3'):
                # 深圳证券交易所
                suggestions.append({'code': f"{partial_symbol}.SZ", 'name': f"深圳股票 {partial_symbol}"})
        
        return suggestions[:5]  # 限制返回前5个建议 