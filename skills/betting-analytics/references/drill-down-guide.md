# 下钻分析指南 (Drill-Down Analysis Guide)

本文档详细说明博彩数据下钻分析的方法、维度和最佳实践。

## 核心概念

### 什么是下钻分析
下钻分析 (Drill-Down) 是从汇总数据逐层深入细节的分析方法:
- 从总体 → 分类 → 子分类 → 个体
- 从宏观趋势 → 微观模式
- 从 "是什么" → "为什么"

### 下钻分析价值
- 发现隐藏模式
- 定位问题根源
- 支持精细化决策
- 验证汇总结论

## 维度层级设计

### 时间维度层级
```
年 (Year)
└── 季度 (Quarter)
    └── 月 (Month)
        └── 周 (Week)
            └── 日 (Day)
                └── 时段 (Hour)
                    └── 比赛 (Match)
```

**实现:**
```python
def extract_time_hierarchy(df, time_col='match_date'):
    df = df.copy()
    df['year'] = pd.to_datetime(df[time_col]).dt.year
    df['quarter'] = pd.to_datetime(df[time_col]).dt.quarter
    df['month'] = pd.to_datetime(df[time_col]).dt.to_period('M').astype(str)
    df['week'] = pd.to_datetime(df[time_col]).dt.isocalendar().week
    df['day'] = pd.to_datetime(df[time_col]).dt.date
    df['hour'] = pd.to_datetime(df[time_col]).dt.hour
    return df
```

### 组织维度层级
```
体育类型 (Sport)
└── 联赛 (League)
    └── 球队 (Team)
        └── 球员 (Player)
```

### 市场维度层级
```
市场类型 (Market Type)
└── 盘口类型 (Bet Type)
    └── 具体选项 (Option)
```

**示例:**
```
1X2
├── 主胜 (Home)
├── 平局 (Draw)
└── 客胜 (Away)

大小球 (OU)
├── 大球 (Over 2.5)
└── 小球 (Under 2.5)

亚盘 (AH)
├── 上盘 (Home -0.5)
└── 下盘 (Away +0.5)
```

### 地理维度层级
```
洲 (Continent)
└── 国家 (Country)
    └── 城市 (City)
        └── 球场 (Stadium)
```

## 下钻操作类型

### 1. 向下钻取 (Drill Down)
从汇总层深入到细节层

```python
def drill_down(df, from_level, to_level, filters=None):
    """
    向下钻取
    
    Args:
        from_level: 起始层级 (如 'league')
        to_level: 目标层级 (如 'team')
        filters: 过滤条件 (如 {'league': 'Premier League'})
    """
    result = df.copy()
    
    if filters:
        for col, val in filters.items():
            result = result[result[col] == val]
    
    # 按目标层级聚合
    metrics = result.select_dtypes(include=[np.number]).columns
    aggregated = result.groupby(to_level)[metrics].agg(['mean', 'sum', 'count', 'std'])
    
    return aggregated
```

### 2. 向上卷取 (Roll Up)
从细节层汇总到更高层

```python
def roll_up(df, from_level, to_level):
    """
    向上卷取
    
    Args:
        from_level: 起始层级 (如 'team')
        to_level: 目标层级 (如 'league')
    """
    metrics = df.select_dtypes(include=[np.number]).columns
    aggregated = df.groupby(to_level)[metrics].agg(['mean', 'sum', 'count'])
    return aggregated
```

### 3. 切片 (Slice)
在某一层级选择特定值

```python
def slice_data(df, dimension, value):
    """
    数据切片
    
    Args:
        dimension: 维度名
        value: 选定值
    """
    return df[df[dimension] == value]
```

### 4. 切块 (Dice)
选择多个维度的特定值组合

```python
def dice_data(df, filters):
    """
    数据切块
    
    Args:
        filters: 多维度过滤条件
                 {'league': 'Premier League', 'month': '2024-01'}
    """
    result = df.copy()
    for col, val in filters.items():
        result = result[result[col] == val]
    return result
```

### 5. 旋转 (Pivot)
改变维度的展示方向

```python
def pivot_data(df, rows, cols, values, aggfunc='mean'):
    """
    数据透视
    
    Args:
        rows: 行维度
        cols: 列维度
        values: 值字段
        aggfunc: 聚合函数
    """
    return df.pivot_table(index=rows, columns=cols, values=values, aggfunc=aggfunc)
```

## 对比分析

### 环比对比 (MoM)
与上一周期对比

```python
def mom_comparison(df, dimension, metric):
    """
    环比对比
    
    Args:
        dimension: 时间维度 (如 'month')
        metric: 指标名
    """
    aggregated = df.groupby(dimension)[metric].mean()
    mom_change = aggregated.pct_change() * 100
    
    return pd.DataFrame({
        f'{metric}_value': aggregated,
        f'{metric}_mom': mom_change
    })
```

### 同比对比 (YoY)
与去年同期对比

```python
def yoy_comparison(df, time_col, metric):
    """
    同比对比
    
    需要至少两年的数据
    """
    df = df.copy()
    df['year'] = pd.to_datetime(df[time_col]).dt.year
    df['month'] = pd.to_datetime(df[time_col]).dt.month
    
    # 按年 - 月聚合
    monthly = df.groupby(['year', 'month'])[metric].mean().unstack(level=0)
    
    # 计算同比
    yoy_change = (monthly.iloc[:, -1] / monthly.iloc[:, -2] - 1) * 100
    
    return pd.DataFrame({
        'current_year': monthly.iloc[:, -1],
        'previous_year': monthly.iloc[:, -2],
        'yoy_change': yoy_change
    })
```

### 与基准对比
与平均值/目标值对比

```python
def vs_baseline(df, dimension, metric, baseline='mean'):
    """
    与基准对比
    
    Args:
        baseline: 'mean' / 'median' / 具体数值
    """
    aggregated = df.groupby(dimension)[metric].mean()
    
    if baseline == 'mean':
        baseline_val = aggregated.mean()
    elif baseline == 'median':
        baseline_val = aggregated.median()
    else:
        baseline_val = baseline
    
    diff = aggregated - baseline_val
    diff_pct = (diff / baseline_val) * 100
    
    return pd.DataFrame({
        f'{metric}_value': aggregated,
        f'vs_baseline': diff,
        f'vs_baseline_pct': diff_pct
    })
```

## 下钻分析流程

### 标准流程
```python
def standard_drill_down_analysis(df, dimensions, metrics):
    """
    标准下钻分析流程
    
    Args:
        dimensions: 维度列表 ['league', 'team', 'match']
        metrics: 指标列表 ['odds_home', 'bet_volume']
    """
    results = {}
    
    # Level 0: 总体统计
    results['total'] = {
        metric: {
            'mean': df[metric].mean(),
            'sum': df[metric].sum(),
            'count': len(df),
            'std': df[metric].std()
        }
        for metric in metrics if metric in df.columns
    }
    
    # Level 1+: 逐层下钻
    current_df = df
    for i, dim in enumerate(dimensions):
        if dim not in current_df.columns:
            continue
        
        level_results = {}
        
        # 按当前维度聚合
        for dim_val in current_df[dim].unique():
            subset = current_df[current_df[dim] == dim_val]
            
            level_results[dim_val] = {
                'count': len(subset),
                'metrics': {
                    metric: {
                        'mean': subset[metric].mean(),
                        'sum': subset[metric].sum(),
                        'std': subset[metric].std()
                    }
                    for metric in metrics if metric in subset.columns
                }
            }
        
        results[f'level_{i}_{dim}'] = level_results
        current_df = current_df  # 可以继续过滤深入
    
    return results
```

### 异常下钻
发现异常后深入调查

```python
def anomaly_drill_down(df, anomaly_mask, drill_dimensions):
    """
    异常下钻分析
    
    Args:
        anomaly_mask: 异常数据掩码
        drill_dimensions: 下钻维度列表
    """
    anomaly_df = df[anomaly_mask]
    normal_df = df[~anomaly_mask]
    
    comparison = {}
    
    for dim in drill_dimensions:
        if dim not in df.columns:
            continue
        
        # 异常组分布
        anomaly_dist = anomaly_df[dim].value_counts(normalize=True)
        # 正常组分布
        normal_dist = normal_df[dim].value_counts(normalize=True)
        
        # 计算分布差异
        all_values = set(anomaly_dist.index) | set(normal_dist.index)
        diff = {}
        for val in all_values:
            anom_pct = anomaly_dist.get(val, 0)
            norm_pct = normal_dist.get(val, 0)
            diff[val] = anom_pct - norm_pct
        
        comparison[dim] = {
            'anomaly_distribution': anomaly_dist.to_dict(),
            'normal_distribution': normal_dist.to_dict(),
            'difference': diff
        }
    
    return comparison
```

## 可视化模式

### 旭日图 (Sunburst)
展示层级结构和占比

```python
def sunburst_data(df, hierarchy, metric):
    """
    准备旭日图数据
    
    Args:
        hierarchy: 层级列表 ['league', 'team']
        metric: 指标名
    """
    # 按层级聚合
    grouped = df.groupby(hierarchy)[metric].sum().reset_index()
    
    return grouped
```

### 树状图 (Treemap)
展示层级和大小

```python
def treemap_data(df, hierarchy, metric):
    """
    准备树状图数据
    """
    grouped = df.groupby(hierarchy)[metric].sum().reset_index()
    return grouped
```

### 热力图 (Heatmap)
展示二维对比

```python
def heatmap_data(df, row_dim, col_dim, metric):
    """
    准备热力图数据
    """
    pivot = df.pivot_table(
        index=row_dim,
        columns=col_dim,
        values=metric,
        aggfunc='mean'
    )
    return pivot
```

### 漏斗图 (Funnel)
展示转化/过滤过程

```python
def funnel_data(df, dimension, metric):
    """
    准备漏斗图数据
    """
    aggregated = df.groupby(dimension)[metric].sum().sort_values(ascending=False)
    return aggregated
```

## 实战案例

### 案例 1: 联赛赔率下钻分析
```python
def league_odds_drill_down(df):
    """联赛赔率下钻分析"""
    
    results = {}
    
    # Level 1: 联赛层面
    league_stats = df.groupby('league').agg({
        'odds_home': ['mean', 'std', 'count'],
        'bet_volume': ['sum', 'mean']
    })
    results['league_level'] = league_stats
    
    # Level 2: 球队层面 (按联赛过滤)
    team_stats = {}
    for league in df['league'].unique():
        league_df = df[df['league'] == league]
        team_stats[league] = league_df.groupby('home_team').agg({
            'odds_home': 'mean',
            'bet_volume': 'sum'
        })
    results['team_level'] = team_stats
    
    # Level 3: 时间趋势 (按联赛)
    time_trends = {}
    for league in df['league'].unique():
        league_df = df[df['league'] == league]
        league_df['month'] = pd.to_datetime(league_df['match_date']).dt.to_period('M')
        time_trends[league] = league_df.groupby('month')['odds_home'].mean()
    results['time_trend'] = time_trends
    
    return results
```

### 案例 2: 投注量异常下钻
```python
def volume_anomaly_drill_down(df, volume_threshold=0.95):
    """投注量异常下钻分析"""
    
    # 识别高投注量比赛
    threshold = df['bet_volume'].quantile(volume_threshold)
    high_volume = df[df['bet_volume'] >= threshold]
    
    analysis = {
        'total_high_volume_matches': len(high_volume),
        'threshold': threshold,
        
        # 联赛分布
        'league_distribution': high_volume['league'].value_counts().to_dict(),
        
        # 时间分布
        'time_distribution': high_volume.groupby(
            pd.to_datetime(high_volume['match_date']).dt.hour
        ).size().to_dict(),
        
        # 赔率特征
        'odds_stats': {
            'mean_home_odds': high_volume['odds_home'].mean(),
            'mean_away_odds': high_volume['odds_away'].mean()
        }
    }
    
    return analysis
```

## 最佳实践

### 1. 维度设计原则
- 层级清晰，避免交叉
- 每层 3-7 个子项为宜
- 命名一致，易于理解

### 2. 性能优化
- 预聚合常用层级
- 使用物化视图
- 缓存中间结果

### 3. 分析策略
- 从汇总开始，逐步深入
- 发现异常立即下钻
- 对比正常与异常模式

### 4. 结果呈现
- 保持上下文 (显示当前层级路径)
- 提供导航 (面包屑)
- 支持快速跳转

## 相关文档

- [data-format.md](data-format.md) - 数据格式规范
- [trend-methods.md](trend-methods.md) - 趋势分析方法
- [anomaly-methods.md](anomaly-methods.md) - 异常检测方法
- [attribution-methods.md](attribution-methods.md) - 归因分析方法
