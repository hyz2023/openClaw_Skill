# 趋势分析方法 (Trend Analysis Methods)

本文档详细说明博彩数据趋势分析的各种方法和指标。

## 核心概念

### 什么是趋势分析
趋势分析用于识别数据随时间变化的方向和模式，帮助理解:
- 赔率走势 (上升/下降/盘整)
- 投注量变化
- 市场情绪演变
- 波动率变化

## 移动平均线 (Moving Average)

### 简单移动平均 (SMA)
```python
def sma(series, window):
    return series.rolling(window=window).mean()
```

**常用周期:**
| 周期 | 名称 | 用途 |
|------|------|------|
| 5 | MA5 | 短期趋势 |
| 10 | MA10 | 短中期趋势 |
| 20 | MA20 | 中期趋势 |
| 60 | MA60 | 长期趋势 |

**信号解读:**
- 价格在 MA 上方 → 偏强
- 价格在 MA 下方 → 偏弱
- MA 向上倾斜 → 上升趋势
- MA 向下倾斜 → 下降趋势

### 指数移动平均 (EMA)
```python
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()
```

EMA 给予近期数据更高权重，对最新变化更敏感。

## 趋势线分析

### 线性回归趋势线
```python
import numpy as np

def trend_line(series):
    x = np.arange(len(series))
    y = series.values
    slope, intercept = np.polyfit(x, y, 1)
    trend = slope * x + intercept
    return slope, intercept, trend
```

**斜率解读:**
| 斜率范围 | 趋势强度 |
|---------|---------|
| > 0.05 | 强上升 |
| 0.01 - 0.05 | 温和上升 |
| -0.01 - 0.01 | 盘整 |
| -0.05 - -0.01 | 温和下降 |
| < -0.05 | 强下降 |

### 趋势通道
```python
def trend_channel(series, window=20):
    ma = series.rolling(window).mean()
    std = series.rolling(window).std()
    upper = ma + 2 * std
    lower = ma - 2 * std
    return upper, ma, lower
```

## 动量指标

### RSI (相对强弱指数)
```python
def rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi
```

**RSI 解读:**
| RSI 范围 | 状态 | 含义 |
|---------|------|------|
| > 70 | 超买 | 可能回调 |
| 50-70 | 偏强 | 上升动能 |
| 30-50 | 偏弱 | 下降动能 |
| < 30 | 超卖 | 可能反弹 |

### MACD (移动平均收敛发散)
```python
def macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast).mean()
    ema_slow = series.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
```

**信号解读:**
- MACD 上穿信号线 → 买入信号
- MACD 下穿信号线 → 卖出信号
- 柱状图扩大 → 动能增强

## 波动率分析

### 标准差波动率
```python
def volatility(series, window=20):
    return series.rolling(window).std()
```

### ATR (平均真实波幅)
```python
def atr(high, low, close, window=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window).mean()
```

**波动率解读:**
| 波动率 | 状态 | 策略含义 |
|--------|------|---------|
| 高 | 剧烈波动 | 风险高，机会大 |
| 中 | 正常波动 | 常规分析 |
| 低 | 平静 | 可能即将突破 |

## 支撑位与阻力位

### 识别方法
```python
def support_resistance(series, window=20):
    # 滚动最小值 (支撑)
    support = series.rolling(window, center=True).min()
    # 滚动最大值 (阻力)
    resistance = series.rolling(window, center=True).max()
    return support, resistance
```

### 枢轴点 (Pivot Points)
```python
def pivot_points(high, low, close):
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    return pivot, r1, r2, s1, s2
```

## 趋势强度指标

### ADX (平均趋向指数)
```python
def adx(high, low, close, window=14):
    # +DM 和 -DM
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    # TR
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 平滑
    atr = tr.rolling(window).mean()
    plus_di = 100 * (plus_dm.rolling(window).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window).mean() / atr)
    
    # DX 和 ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window).mean()
    
    return adx, plus_di, minus_di
```

**ADX 解读:**
| ADX 值 | 趋势强度 |
|--------|---------|
| > 40 | 极强趋势 |
| 25-40 | 强趋势 |
| 20-25 | 中等趋势 |
| < 20 | 无趋势 (盘整) |

## 赔率趋势分析特殊考虑

### 赔率归一化
由于不同比赛的赔率范围不同，建议归一化:
```python
def normalize_odds(odds_series):
    return (odds_series - odds_series.min()) / (odds_series.max() - odds_series.min())
```

### 赔率隐含概率
```python
def implied_probability(odds_home, odds_draw, odds_away):
    total = 1/odds_home + 1/odds_draw + 1/odds_away
    prob_home = (1/odds_home) / total
    prob_draw = (1/odds_draw) / total
    prob_away = (1/odds_away) / total
    return prob_home, prob_draw, prob_away
```

### 赔率变化率
```python
def odds_change_rate(odds_series):
    return odds_series.pct_change() * 100
```

## 实战应用

### 赔率趋势分析流程
```python
def analyze_odds_trend(df, odds_col='odds_home'):
    series = df[odds_col]
    
    # 1. 移动平均
    ma5 = sma(series, 5)
    ma20 = sma(series, 20)
    
    # 2. 趋势线
    slope, _, _ = trend_line(series)
    
    # 3. RSI
    rsi_val = rsi(series).iloc[-1]
    
    # 4. 波动率
    vol = volatility(series, 20).iloc[-1]
    
    # 5. 支撑阻力
    support, resistance = support_resistance(series)
    
    return {
        'trend': '上升' if slope > 0.01 else '下降' if slope < -0.01 else '盘整',
        'rsi': rsi_val,
        'volatility': vol,
        'vs_ma20': '高于' if series.iloc[-1] > ma20.iloc[-1] else '低于',
        'support': support.dropna().tail(3).tolist(),
        'resistance': resistance.dropna().tail(3).tolist()
    }
```

### 投注量趋势分析
```python
def analyze_volume_trend(df):
    volume = df['bet_volume']
    
    # 量价关系
    price = df['odds_home']
    correlation = volume.corr(price)
    
    # 成交量变化率
    volume_change = volume.pct_change()
    
    return {
        'volume_trend': '增加' if volume_change.iloc[-1] > 0 else '减少',
        'price_volume_corr': correlation,
        'avg_volume': volume.mean(),
        'volume_spike': volume_change.abs().iloc[-1] > 0.5
    }
```

## 可视化建议

### 趋势图
- 主图：价格/赔率 + MA 线 + 趋势线
- 副图 1: RSI/MACD
- 副图 2: 成交量
- 标注：支撑位/阻力位

### 热力图
- 时间 × 联赛 的赔率变化热力图
- 时间 × 球队 的投注量热力图

## 相关文档

- [data-format.md](data-format.md) - 数据格式规范
- [anomaly-methods.md](anomaly-methods.md) - 异常检测方法
- [attribution-methods.md](attribution-methods.md) - 归因分析方法
