# 异常检测方法 (Anomaly Detection Methods)

本文档详细说明博彩数据异常点检测的各种方法和应用场景。

## 核心概念

### 什么是异常点
异常点 (Anomaly/Outlier) 是指与大多数数据显著不同的观测值，可能表示:
- 数据录入错误
- 异常市场行为
- 可疑投注模式
- 重大事件影响

### 异常检测挑战
- 正常与异常的边界模糊
- 异常类型多样 (点异常、上下文异常、集体异常)
- 数据分布可能随时间变化

## 统计方法

### Z-Score 方法

**原理:** 计算数据点距离均值的标准差数

```python
def zscore_anomaly(series, threshold=3.0):
    mean = series.mean()
    std = series.std()
    z_scores = np.abs((series - mean) / std)
    anomalies = z_scores > threshold
    return anomalies, z_scores
```

**参数选择:**
| 阈值 | 覆盖范围 | 敏感度 |
|------|---------|--------|
| 2.0 | 95% | 高 (更多误报) |
| 2.5 | 98% | 中 |
| 3.0 | 99.7% | 低 (更少误报) |

**适用场景:**
- 数据近似正态分布
- 快速初步筛查
- 单变量异常检测

**局限性:**
- 对非正态分布效果差
- 对多个异常值敏感 (均值和标准差会被拉偏)

### IQR (四分位距) 方法

**原理:** 基于四分位数识别离群值

```python
def iqr_anomaly(series, k=1.5):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    anomalies = (series < lower_bound) | (series > upper_bound)
    return anomalies, lower_bound, upper_bound
```

**参数选择:**
| k 值 | 异常范围 | 敏感度 |
|------|---------|--------|
| 1.5 | 标准 | 中等 |
| 3.0 | 极端 | 低 (只检测极端值) |

**适用场景:**
- 非正态分布数据
- 有偏斜的数据
- 稳健性要求高

**优势:**
- 不受极端值影响
- 无需假设数据分布

## 机器学习方法

### Isolation Forest (孤立森林)

**原理:** 通过随机分割隔离数据点，异常点更容易被隔离

```python
from sklearn.ensemble import IsolationForest

def isolation_forest_anomaly(df, contamination=0.1, n_estimators=100):
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    # -1 表示异常，1 表示正常
    predictions = model.fit_predict(df)
    # 转换为异常评分 (0-1)
    scores = model.decision_function(df)
    scores = 1 - (scores - scores.min()) / (scores.max() - scores.min())
    
    return predictions == -1, scores
```

**参数选择:**
| 参数 | 建议值 | 说明 |
|------|--------|------|
| contamination | 0.01-0.1 | 预期异常比例 |
| n_estimators | 100-200 | 树的数量 |
| max_samples | 'auto' | 每棵树的样本数 |

**适用场景:**
- 高维数据
- 多变量联合异常
- 非线性关系

**优势:**
- 计算效率高
- 无需假设数据分布
- 适合高维数据

### One-Class SVM

**原理:** 在特征空间中找到一个超平面，将正常数据与原点分开

```python
from sklearn.svm import OneClassSVM

def one_class_svm_anomaly(df, nu=0.1, kernel='rbf'):
    model = OneClassSVM(nu=nu, kernel=kernel, gamma='auto')
    predictions = model.fit_predict(df)
    scores = model.decision_function(df)
    
    return predictions == -1, scores
```

**适用场景:**
- 小样本
- 复杂边界
- 需要精确边界

## 时间序列方法

### STL 分解残差

**原理:** 将时间序列分解为趋势、季节性和残差，残差中的极端值为异常

```python
from statsmodels.tsa.seasonal import STL

def stl_anomaly(series, period=7):
    # STL 分解
    stl = STL(series, period=period)
    result = stl.fit()
    
    # 残差
    residuals = result.resid
    
    # 残差的 Z-Score
    z_scores = np.abs((residuals - residuals.mean()) / residuals.std())
    
    return z_scores > 3, z_scores
```

**适用场景:**
- 有明显季节性的数据
- 需要区分趋势异常和季节异常

### 滚动统计方法

```python
def rolling_anomaly(series, window=20, threshold=3):
    rolling_mean = series.rolling(window, center=True).mean()
    rolling_std = series.rolling(window, center=True).std()
    
    z_scores = np.abs((series - rolling_mean) / rolling_std.replace(0, np.nan))
    anomalies = z_scores > threshold
    
    return anomalies, z_scores
```

**适用场景:**
- 非平稳时间序列
- 局部异常检测

## 集成方法

### 多方法投票

```python
def ensemble_voting(df, methods=['zscore', 'iqr', 'isolation_forest']):
    scores = {}
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        series = df[col].dropna()
        
        if 'zscore' in methods:
            _, z = zscore_anomaly(series)
            scores[f'{col}_zscore'] = z / z.max()
        
        if 'iqr' in methods:
            # IQR 评分
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            dist = np.maximum(lower - series, series - upper, 0)
            iqr_score = dist / (1.5 * iqr)
            scores[f'{col}_iqr'] = iqr_score.clip(0, 1)
    
    if 'isolation_forest' in methods:
        _, if_score = isolation_forest_anomaly(df[numeric_cols])
        scores['global_if'] = pd.Series(if_score, index=df.index)
    
    # 平均所有评分
    score_df = pd.DataFrame(scores)
    ensemble_score = score_df.mean(axis=1)
    
    return ensemble_score
```

### 加权集成

```python
def weighted_ensemble(df, weights=None):
    if weights is None:
        weights = {
            'zscore': 0.2,
            'iqr': 0.2,
            'isolation_forest': 0.4,
            'time_series': 0.2
        }
    
    scores = {}
    total_weight = 0
    
    # 计算各方法评分
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    _, z = zscore_anomaly(df[numeric_cols[0]])
    scores['zscore'] = (z / z.max()).clip(0, 1)
    total_weight += weights['zscore']
    
    _, if_score = isolation_forest_anomaly(df[numeric_cols])
    scores['if'] = pd.Series(if_score, index=df.index)
    total_weight += weights['isolation_forest']
    
    # 加权平均
    weighted_score = sum(scores[k] * weights[k] for k in scores.keys()) / total_weight
    
    return weighted_score
```

## 博彩数据特定异常类型

### 赔率异常

```python
def odds_anomaly(df):
    anomalies = {}
    
    # 1. 赔率突变
    for col in ['odds_home', 'odds_draw', 'odds_away']:
        if col in df.columns:
            change = df[col].pct_change().abs()
            anomalies[f'{col}_spike'] = change > 0.2  # 20% 变化
    
    # 2. 赔率倒挂 (主胜赔率高于客胜但主队更强)
    if all(col in df.columns for col in ['odds_home', 'odds_away']):
        anomalies['inversion'] = (df['odds_home'] > df['odds_away'] * 1.5)
    
    # 3. 赔率和异常 (通常应在 1.05-1.15 之间)
    if all(col in df.columns for col in ['odds_home', 'odds_draw', 'odds_away']):
        odds_sum = 1/df['odds_home'] + 1/df['odds_draw'] + 1/df['odds_away']
        anomalies['margin_anomaly'] = (odds_sum < 0.85) | (odds_sum > 1.2)
    
    return anomalies
```

### 投注量异常

```python
def volume_anomaly(df):
    anomalies = {}
    
    if 'bet_volume' not in df.columns:
        return anomalies
    
    volume = df['bet_volume']
    
    # 1. 投注量突增
    volume_change = volume.pct_change()
    anomalies['volume_spike'] = volume_change > 2.0  # 200% 增长
    
    # 2. 投注量与赔率变化背离
    if 'odds_home' in df.columns:
        corr = volume.rolling(20).corr(df['odds_home'])
        anomalies['volume_price_divergence'] = corr.abs() > 0.7
    
    # 3. 异常时间投注
    if 'timestamp' in df.columns:
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
        anomalies['odd_hour'] = (df['hour'] < 6) | (df['hour'] > 23)
    
    return anomalies
```

### 结果异常

```python
def outcome_anomaly(df):
    anomalies = {}
    
    if all(col in df.columns for col in ['odds_home', 'outcome']):
        # 大冷门 (低概率事件发生)
        implied_prob = 1 / df['odds_home']
        anomalies['upset'] = (implied_prob < 0.3) & (df['outcome'] == 2)  # 主胜概率<30% 但客胜
    
    return anomalies
```

## 异常评分解释

### 评分等级
| 评分范围 | 等级 | 行动建议 |
|---------|------|---------|
| 0.9-1.0 | 极高 | 立即调查 |
| 0.7-0.9 | 高 | 优先审查 |
| 0.5-0.7 | 中 | 关注 |
| 0.3-0.5 | 低 | 记录 |
| 0.0-0.3 | 正常 | 无需行动 |

### 误报处理
- 调整阈值
- 增加上下文信息
- 使用集成方法降低单一方法偏差
- 人工复核确认

## 实战流程

```python
def complete_anomaly_analysis(df):
    """完整的异常分析流程"""
    
    # 1. 数据预处理
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    
    # 2. 多方法检测
    results = {}
    
    # 统计方法
    for col in numeric_df.columns[:5]:  # 前 5 个数值列
        anomalies, scores = zscore_anomaly(numeric_df[col])
        results[f'{col}_zscore'] = scores
    
    # 机器学习方法
    if len(numeric_df.columns) >= 2:
        anomalies, scores = isolation_forest_anomaly(numeric_df)
        results['isolation_forest'] = scores
    
    # 3. 集成评分
    score_df = pd.DataFrame({k: pd.Series(v, index=df.index) for k, v in results.items()})
    ensemble_score = score_df.mean(axis=1)
    
    # 4. 识别异常
    threshold = 0.7
    anomaly_mask = ensemble_score >= threshold
    
    # 5. 汇总报告
    report = {
        'total_records': len(df),
        'anomaly_count': anomaly_mask.sum(),
        'anomaly_rate': anomaly_mask.mean(),
        'anomaly_indices': df.index[anomaly_mask].tolist(),
        'scores': ensemble_score,
        'method_scores': results
    }
    
    return report
```

## 相关文档

- [data-format.md](data-format.md) - 数据格式规范
- [trend-methods.md](trend-methods.md) - 趋势分析方法
- [attribution-methods.md](attribution-methods.md) - 归因分析方法
