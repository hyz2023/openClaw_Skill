# 归因分析方法 (Attribution Analysis Methods)

本文档详细说明博彩数据归因分析的各种方法和解释技术。

## 核心概念

### 什么是归因分析
归因分析用于识别和量化影响目标变量的关键因素，回答:
- 哪些因素对比赛结果影响最大？
- 赔率变化主要由什么驱动？
- 各因素的贡献度是多少？

### 归因分析类型
| 类型 | 目标 | 方法 |
|------|------|------|
| 特征重要性 | 排序影响因素 | RF、XGBoost 重要性 |
| 贡献度分解 | 量化各因素贡献 | SHAP、LIME |
| 因果推断 | 确定因果关系 | Granger 因果、DAG |

## 特征重要性方法

### 基于树模型的重要性

```python
from sklearn.ensemble import RandomForestClassifier

def feature_importance_rf(X, y, n_estimators=100):
    model = RandomForestClassifier(n_estimators=n_estimators, random_state=42)
    model.fit(X, y)
    
    importance = pd.Series(
        model.feature_importances_,
        index=X.columns,
        name='importance'
    ).sort_values(ascending=False)
    
    return importance, model
```

**原理:** 基于特征在树分裂中减少的不纯度 (Gini/Entropy)

**优点:**
- 计算快速
- 易于理解
- 捕捉非线性关系

**缺点:**
- 偏向高基数特征
- 无法显示影响方向

### 排列重要性 (Permutation Importance)

```python
from sklearn.inspection import permutation_importance

def permutation_importance(model, X, y, n_repeats=10):
    result = permutation_importance(model, X, y, n_repeats=n_repeats, random_state=42)
    
    importance = pd.Series(
        result.importances_mean,
        index=X.columns,
        name='permutation_importance'
    ).sort_values(ascending=False)
    
    return importance
```

**原理:** 随机打乱某特征的值，观察模型性能下降程度

**优点:**
- 模型无关
- 更可靠的重要性估计
- 考虑特征相关性

**缺点:**
- 计算成本高
- 需要额外验证集

## SHAP 值方法

### SHAP 基础

SHAP (SHapley Additive exPlanations) 基于博弈论的 Shapley 值，提供:
- 局部解释 (单个预测)
- 全局解释 (整体特征重要性)
- 一致的理论基础

```python
import shap

def shap_analysis(model, X, n_samples=100):
    # 创建解释器
    explainer = shap.TreeExplainer(model)
    
    # 采样
    if len(X) > n_samples:
        X_sample = X.sample(n=n_samples, random_state=42)
    else:
        X_sample = X
    
    # 计算 SHAP 值
    shap_values = explainer.shap_values(X_sample)
    
    return shap_values, explainer
```

### SHAP 摘要图

```python
def shap_summary(shap_values, X):
    """生成 SHAP 摘要图数据"""
    # 对于二分类，取正类的 SHAP 值
    if isinstance(shap_values, list):
        shap_val = shap_values[1]
    else:
        shap_val = shap_values
    
    # 计算每个特征的平均绝对 SHAP 值
    shap_importance = np.abs(shap_val).mean(axis=0)
    
    importance_df = pd.DataFrame({
        'feature': X.columns,
        'shap_importance': shap_importance
    }).sort_values('shap_importance', ascending=False)
    
    return importance_df
```

### SHAP 依赖图

```python
def shap_dependence(shap_values, X, feature_name):
    """分析某特征的 SHAP 依赖关系"""
    if isinstance(shap_values, list):
        shap_val = shap_values[1]
    else:
        shap_val = shap_values
    
    feature_idx = list(X.columns).index(feature_name)
    
    return {
        'feature_values': X[feature_name].values,
        'shap_values': shap_val[:, feature_idx]
    }
```

**解读:**
- X 轴：特征值
- Y 轴：SHAP 值 (对预测的影响)
- 颜色：另一特征的值 (交互效应)

### SHAP 力导图

```python
def shap_force(shap_values, X, sample_idx=0):
    """单个样本的 SHAP 力导图数据"""
    if isinstance(shap_values, list):
        shap_val = shap_values[1][sample_idx]
    else:
        shap_val = shap_values[sample_idx]
    
    base_value = explainer.expected_value
    
    return {
        'base_value': base_value,
        'features': X.columns.tolist(),
        'shap_values': shap_val,
        'feature_values': X.iloc[sample_idx].tolist()
    }
```

## 贡献度分解

### 加法分解

```python
def additive_decomposition(model, X, sample_idx=0):
    """加法贡献度分解"""
    prediction = model.predict_proba(X.iloc[[sample_idx]])[0, 1]
    base_pred = model.predict_proba(X)[0, 1].mean()
    
    # 使用 SHAP 值作为贡献度
    shap_vals = shap_values[sample_idx]
    
    decomposition = {
        'base_prediction': base_pred,
        'final_prediction': prediction,
        'total_change': prediction - base_pred,
        'contributions': dict(zip(X.columns, shap_vals))
    }
    
    return decomposition
```

### 特征分组归因

```python
def grouped_attribution(shap_values, X, groups):
    """
    将特征分组计算归因
    
    groups: dict, 如 {'基本面': ['home_rank', 'away_rank'], 
                     '赔率': ['odds_home', 'odds_draw'],
                     '投注': ['volume_home', 'volume_away']}
    """
    grouped = {}
    
    for group_name, features in groups.items():
        available_features = [f for f in features if f in X.columns]
        if available_features:
            feature_indices = [list(X.columns).index(f) for f in available_features]
            group_shap = np.abs(shap_values[:, feature_indices]).sum(axis=1).mean()
            grouped[group_name] = group_shap
    
    # 归一化
    total = sum(grouped.values())
    if total > 0:
        grouped = {k: v/total for k, v in grouped.items()}
    
    return grouped
```

## 因果推断方法

### Granger 因果检验

```python
from statsmodels.tsa.stattools import grangercausalitytests

def granger_causality_test(df, target_col, test_cols, max_lag=4):
    """
    Granger 因果检验
    
    原假设：test_col 不 Granger-cause target_col
    """
    results = {}
    
    for col in test_cols:
        if col == target_col:
            continue
        
        data = df[[target_col, col]].dropna()
        if len(data) < 50:
            continue
        
        try:
            test_result = grangercausalitytests(data, max_lag=max_lag, verbose=False)
            # 取各滞后阶数的最小 p 值
            min_pvalue = min(test_result[lag][0]['ssr_chi2test'][1] 
                           for lag in test_result)
            results[col] = {
                'p_value': min_pvalue,
                'is_causal': min_pvalue < 0.05
            }
        except:
            results[col] = {'p_value': None, 'is_causal': False}
    
    return results
```

### 因果图 (DAG)

```python
# 使用 causalnex 库构建因果图
from causalnex.structure import StructureModel

def build_causal_dag(df):
    """构建因果 DAG"""
    sm = StructureModel()
    
    # 从数据学习结构
    sm.add_edges_from_random_variable()
    
    return sm
```

## 博彩数据归因实践

### 比赛结果归因

```python
def match_outcome_attribution(df):
    """分析影响比赛结果的因素"""
    
    # 准备特征
    feature_cols = [
        'odds_home', 'odds_draw', 'odds_away',
        'home_rank', 'away_rank',
        'home_form', 'away_form',
        'h2h_home_wins', 'h2h_away_wins',
        'bet_volume_home', 'bet_volume_away'
    ]
    
    X = df[[col for col in feature_cols if col in df.columns]].dropna()
    y = df.loc[X.index, 'outcome']
    
    # 训练模型
    importance, model = feature_importance_rf(X, y)
    
    # SHAP 分析
    shap_values, explainer = shap_analysis(model, X)
    shap_importance = shap_summary(shap_values, X)
    
    return {
        'feature_importance': importance,
        'shap_importance': shap_importance,
        'model_accuracy': model.score(X, y),
        'top_factors': importance.head(5).to_dict()
    }
```

### 赔率变化归因

```python
def odds_change_attribution(df):
    """分析赔率变化的驱动因素"""
    
    # 计算赔率变化
    df = df.copy()
    df['odds_change'] = df['odds_home'].pct_change()
    
    # 特征
    feature_cols = [
        'volume_change', 'news_sentiment', 
        'injury_report', 'weather_change'
    ]
    
    X = df[[col for col in feature_cols if col in df.columns]].dropna()
    y = df.loc[X.index, 'odds_change'].dropna()
    
    # 对齐索引
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]
    
    # 回归分析
    from sklearn.ensemble import RandomForestRegressor
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    importance = pd.Series(
        model.feature_importances_,
        index=X.columns
    ).sort_values(ascending=False)
    
    return {
        'importance': importance,
        'r2_score': model.score(X, y),
        'top_drivers': importance.head(3).to_dict()
    }
```

### 投注量归因

```python
def volume_attribution(df):
    """分析投注量的影响因素"""
    
    feature_cols = [
        'match_importance', 'team_popularity',
        'odds_home', 'time_to_match',
        'marketing_spend', 'day_of_week'
    ]
    
    X = df[[col for col in feature_cols if col in df.columns]].dropna()
    y = df.loc[X.index, 'bet_volume']
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    # SHAP 分析
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    
    return {
        'importance': pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False),
        'shap_summary': shap_summary(shap_values, X),
        'model_r2': model.score(X, y)
    }
```

## 结果解释框架

### 重要性分级
| 重要性值 | 等级 | 说明 |
|---------|------|------|
| > 0.20 | 极高 | 核心驱动因素 |
| 0.10-0.20 | 高 | 重要因素 |
| 0.05-0.10 | 中 | 有一定影响 |
| < 0.05 | 低 | 影响较小 |

### 影响方向解读
- SHAP 值 > 0: 特征值增加 → 目标值增加
- SHAP 值 < 0: 特征值增加 → 目标值减少

### 交互效应
```python
def interaction_effect(shap_values, X, feature1, feature2):
    """分析两特征的交互效应"""
    idx1 = list(X.columns).index(feature1)
    idx2 = list(X.columns).index(feature2)
    
    # 分箱分析
    X1_bins = pd.qcut(X[feature1], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
    
    interaction_data = []
    for bin_val in X1_bins.unique():
        mask = X1_bins == bin_val
        avg_shap2 = shap_values[mask, idx2].mean()
        interaction_data.append({
            'bin': bin_val,
            'avg_shap': avg_shap2
        })
    
    return interaction_data
```

## 报告生成模板

```python
def generate_attribution_report(results):
    report = []
    report.append("## 归因分析报告")
    report.append("")
    report.append("### 模型性能")
    report.append(f"- 准确率：{results['model_accuracy']:.2%}")
    report.append("")
    report.append("### Top 5 影响因素")
    report.append("")
    report.append("| 排名 | 特征 | 重要性 | SHAP 重要性 |")
    report.append("|------|------|--------|------------|")
    
    for i, (feature, imp) in enumerate(results['top_factors'].items(), 1):
        shap_imp = results['shap_importance'].loc[feature] if feature in results['shap_importance'].index else 0
        report.append(f"| {i} | {feature} | {imp:.4f} | {shap_imp:.4f} |")
    
    return '\n'.join(report)
```

## 相关文档

- [data-format.md](data-format.md) - 数据格式规范
- [trend-methods.md](trend-methods.md) - 趋势分析方法
- [anomaly-methods.md](anomaly-methods.md) - 异常检测方法
- [drill-down-guide.md](drill-down-guide.md) - 下钻分析指南
