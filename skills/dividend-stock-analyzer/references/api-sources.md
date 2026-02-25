# 数据源与 API 使用指南

## 一、A 股数据源

### 1. AkShare (推荐)
**安装**: `pip install akshare`

**特点**: 免费、开源、数据全面

```python
import akshare as ak

# 获取股票基本信息
stock_info = ak.stock_info_a_code_name()

# 获取历史行情
stock_hist = ak.stock_zh_a_hist(symbol="000001", period="daily")

# 获取分红信息
stock_dividend = ak.stock_history_dividend(symbol="000001")

# 获取财务指标
stock_financial = ak.stock_financial_analysis_indicator(symbol="000001")
```

**数据覆盖**:
- 实时/历史行情
- 分红配股
- 财务指标
- 股东人数
- 机构持仓

### 2. Tushare
**安装**: `pip install tushare`
**注册**: https://tushare.pro (需要 token)

```python
import tushare as ts

ts.set_token('your_token')
pro = ts.pro_api()

# 获取股票列表
stocks = pro.stock_basic()

# 获取分红数据
dividend = pro.dividend(ts_code='000001.SZ')

# 获取财务指标
financial = pro.fina_indicator(ts_code='000001.SZ')
```

**积分制度**: 基础数据免费，高级数据需要积分

### 3. 东方财富 API
```python
# 实时行情
import requests
url = "http://push2.eastmoney.com/api/qt/stock/get"
params = {
    'secid': '1.000001',  # 1=沪市，0=深市
    'fields': 'f43,f44,f45,f46'  # 股息相关字段
}
```

## 二、美股数据源

### 1. Yahoo Finance (yfinance)
**安装**: `pip install yfinance`

```python
import yfinance as yf

# 获取股票信息
stock = yf.Ticker("AAPL")

# 获取分红历史
dividends = stock.dividends

# 获取财务数据
info = stock.info
print(info['dividendYield'])  # 股息率
print(info['payoutRatio'])    # 派息比率
print(info['fiveYearAvgDividendYield'])  # 5 年平均股息率

# 获取财务报表
financials = stock.financials
cashflow = stock.cashflow
```

**优点**: 免费、简单易用
**缺点**: 数据可能有延迟

### 2. Alpha Vantage
**注册**: https://www.alphavantage.co (免费 API key)

```python
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData

api_key = 'your_api_key'

# 获取分红数据
ts = TimeSeries(key=api_key)
dividends = ts.get_dividends(symbol='AAPL')

# 获取财务数据
fd = FundamentalData(key=api_key)
financials = fd.get_income_statement_annual(symbol='AAPL')
```

**限制**: 免费账户 5 次/分钟，25 次/天

### 3. Financial Modeling Prep
**注册**: https://financialmodelingprep.com

```python
import requests

api_key = 'your_api_key'

# 获取分红历史
url = f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_dividend/AAPL?apikey={api_key}"
dividends = requests.get(url).json()

# 获取财务比率
ratios_url = f"https://financialmodelingprep.com/api/v3/ratios/AAPL?apikey={api_key}"
ratios = requests.get(ratios_url).json()
```

**免费层**: 每日 250 次请求

## 三、数据获取脚本模板

### A 股数据获取
```python
#!/usr/bin/env python3
"""A 股数据获取模块"""

import akshare as ak
import pandas as pd

def get_stock_dividend_history(symbol: str) -> pd.DataFrame:
    """获取 A 股分红历史"""
    try:
        dividend = ak.stock_history_dividend(symbol=symbol)
        return dividend
    except Exception as e:
        print(f"Error fetching dividend for {symbol}: {e}")
        return pd.DataFrame()

def get_financial_metrics(symbol: str) -> dict:
    """获取财务指标"""
    try:
        metrics = ak.stock_financial_analysis_indicator(symbol=symbol)
        return metrics.iloc[0].to_dict()
    except Exception as e:
        print(f"Error fetching metrics for {symbol}: {e}")
        return {}

def get_stock_price(symbol: str) -> float:
    """获取当前股价"""
    try:
        price = ak.stock_zh_a_spot_em()
        current = price[price['代码'] == symbol]
        return current['最新价'].values[0] if len(current) > 0 else None
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None
```

### 美股数据获取
```python
#!/usr/bin/env python3
"""美股数据获取模块"""

import yfinance as yf
import pandas as pd

def get_stock_dividend_history(symbol: str) -> pd.Series:
    """获取美股分红历史"""
    try:
        stock = yf.Ticker(symbol)
        return stock.dividends
    except Exception as e:
        print(f"Error fetching dividend for {symbol}: {e}")
        return pd.Series()

def get_financial_metrics(symbol: str) -> dict:
    """获取财务指标"""
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            'dividend_yield': info.get('dividendYield', 0),
            'payout_ratio': info.get('payoutRatio', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'market_cap': info.get('marketCap', 0),
            'debt_to_equity': info.get('debtToEquity', 0),
            'free_cashflow': info.get('freeCashflow', 0),
        }
    except Exception as e:
        print(f"Error fetching metrics for {symbol}: {e}")
        return {}

def get_stock_price(symbol: str) -> float:
    """获取当前股价"""
    try:
        stock = yf.Ticker(symbol)
        return stock.history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None
```

## 四、API 限制与最佳实践

### 请求频率限制
| 数据源 | 免费限制 | 建议间隔 |
|--------|----------|----------|
| AkShare | 无明确限制 | 1 秒/请求 |
| Tushare | 根据积分 | 0.5 秒/请求 |
| Yahoo Finance | 非正式 ~2000/天 | 2 秒/请求 |
| Alpha Vantage | 5/分钟，25/天 | 12 秒/请求 |
| FMP | 250/天 | 5 秒/请求 |

### 最佳实践
1. **批量获取**: 一次性获取多只股票数据
2. **缓存优先**: 先查缓存，再调 API
3. **错误处理**: API 失败时优雅降级
4. **错峰调用**: 避开市场开盘高峰期
5. **数据验证**: 检查数据完整性和合理性

## 五、数据质量检查

```python
def validate_stock_data(data: dict) -> bool:
    """验证数据质量"""
    checks = [
        data.get('price', 0) > 0,
        data.get('market_cap', 0) > 0,
        data.get('dividend_yield', 0) >= 0,
        data.get('dividend_yield', 0) < 0.20,  # <20% 排除异常
        data.get('payout_ratio', 0) >= 0,
        data.get('payout_ratio', 1) <= 2.0,  # <=200% 排除异常
    ]
    return all(checks)
```
