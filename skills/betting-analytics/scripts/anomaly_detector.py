#!/usr/bin/env python3
"""
博彩数据异常点检测工具
Anomaly Detector for Betting Data

功能:
- Z-Score 异常检测
- IQR 离群值检测
- Isolation Forest 机器学习检测
- 多方法集成评分
- 异常报告生成
"""

import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from pathlib import Path


def load_data(data_path: str) -> pd.DataFrame:
    """加载数据文件"""
    path = Path(data_path)
    if path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif path.suffix == '.json':
        df = pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return df


def detect_zscore_anomalies(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """
    Z-Score 异常检测
    
    Args:
        series: 数据序列
        threshold: Z-Score 阈值 (默认 3.0)
    
    Returns:
        异常评分序列 (0-1)
    """
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        return pd.Series(0, index=series.index)
    
    z_scores = np.abs((series - mean) / std)
    # 归一化到 0-1
    anomaly_scores = np.minimum(z_scores / threshold, 1.0)
    
    return anomaly_scores


def detect_iqr_anomalies(series: pd.Series, k: float = 1.5) -> pd.Series:
    """
    IQR (四分位距) 异常检测
    
    Args:
        series: 数据序列
        k: IQR 倍数 (默认 1.5)
    
    Returns:
        异常评分序列 (0-1)
    """
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    
    lower_bound = q1 - k * iqr
    upper_bound = q3 + k * iqr
    
    # 计算距离边界的距离
    distances = np.maximum(lower_bound - series, series - upper_bound, 0)
    
    # 归一化
    range_val = upper_bound - lower_bound
    if range_val > 0:
        anomaly_scores = np.minimum(distances / (k * iqr), 1.0)
    else:
        anomaly_scores = pd.Series(0, index=series.index)
    
    return anomaly_scores


def detect_isolation_forest_anomalies(df: pd.DataFrame, 
                                       contamination: float = 0.1,
                                       n_estimators: int = 100) -> pd.Series:
    """
    Isolation Forest 异常检测
    
    Args:
        df: 数据 DataFrame (数值列)
        contamination: 预期异常比例
        n_estimators: 树的数量
    
    Returns:
        异常评分序列 (0-1)
    """
    # 选择数值列
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in data")
    
    X = df[numeric_cols].dropna()
    
    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Isolation Forest
    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=42,
        n_jobs=-1
    )
    
    # 获取异常评分 (负值表示异常)
    scores = model.decision_function(X_scaled)
    
    # 转换为 0-1 评分 (1 表示最异常)
    min_score = scores.min()
    max_score = scores.max()
    
    if max_score - min_score > 0:
        anomaly_scores = 1 - (scores - min_score) / (max_score - min_score)
    else:
        anomaly_scores = np.zeros(len(scores))
    
    # 返回与原 DataFrame 对齐的 Series
    result = pd.Series(0.0, index=df.index)
    result.loc[X.index] = anomaly_scores
    
    return result


def detect_time_series_anomalies(series: pd.Series, window: int = 20) -> pd.Series:
    """
    时间序列异常检测 (基于滚动统计)
    
    Args:
        series: 时间序列数据
        window: 滚动窗口大小
    
    Returns:
        异常评分序列 (0-1)
    """
    # 计算滚动均值和标准差
    rolling_mean = series.rolling(window=window, center=True, min_periods=1).mean()
    rolling_std = series.rolling(window=window, center=True, min_periods=1).std()
    
    # 计算残差
    residuals = series - rolling_mean
    
    # 处理标准差为 0 的情况
    rolling_std = rolling_std.replace(0, np.nan).fillna(1e-6)
    
    # 计算标准化残差
    z_scores = np.abs(residuals / rolling_std)
    
    # 归一化到 0-1
    threshold = 3.0
    anomaly_scores = np.minimum(z_scores / threshold, 1.0)
    
    return anomaly_scores.fillna(0)


def ensemble_anomaly_detection(df: pd.DataFrame, 
                                methods: list = None,
                                weights: dict = None) -> pd.Series:
    """
    集成异常检测 (多方法加权)
    
    Args:
        df: 数据 DataFrame
        methods: 使用的方法列表
        weights: 各方法权重
    
    Returns:
        综合异常评分序列 (0-1)
    """
    if methods is None:
        methods = ['zscore', 'iqr', 'isolation_forest']
    
    if weights is None:
        weights = {
            'zscore': 0.3,
            'iqr': 0.3,
            'isolation_forest': 0.4
        }
    
    scores = {}
    
    # 选择数值列进行分析
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        
        if 'zscore' in methods:
            zscore_scores = detect_zscore_anomalies(series)
            if col not in scores:
                scores[col] = {}
            scores[col]['zscore'] = zscore_scores
        
        if 'iqr' in methods:
            iqr_scores = detect_iqr_anomalies(series)
            if col not in scores:
                scores[col] = {}
            scores[col]['iqr'] = iqr_scores
    
    # Isolation Forest 使用所有数值列
    if 'isolation_forest' in methods and len(numeric_cols) > 0:
        try:
            if_scores = detect_isolation_forest_anomalies(df[numeric_cols])
            scores['global'] = {'isolation_forest': if_scores}
        except Exception as e:
            print(f"Isolation Forest 检测失败：{e}")
    
    # 时间序列异常检测 (如果有时间列)
    time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if time_cols and len(numeric_cols) > 0:
        df_sorted = df.sort_values(time_cols[0])
        for col in numeric_cols[:3]:  # 只对前 3 个数值列做时间序列分析
            series = df_sorted[col].dropna()
            if len(series) >= 10:
                ts_scores = detect_time_series_anomalies(series)
                if col not in scores:
                    scores[col] = {}
                scores[col]['time_series'] = ts_scores.values
    
    # 综合所有评分
    all_scores = []
    all_weights = []
    
    for col, method_scores in scores.items():
        for method, score_series in method_scores.items():
            if isinstance(score_series, np.ndarray):
                score_series = pd.Series(score_series, index=df.index[:len(score_series)])
            
            # 确保索引对齐
            score_series = score_series.reindex(df.index, fill_value=0)
            all_scores.append(score_series)
            
            weight = weights.get(method, 1.0 / len(methods))
            all_weights.append(weight)
    
    if not all_scores:
        return pd.Series(0.0, index=df.index)
    
    # 加权平均
    weighted_scores = sum(s * w for s, w in zip(all_scores, all_weights))
    total_weight = sum(all_weights)
    
    if total_weight > 0:
        final_scores = weighted_scores / total_weight
    else:
        final_scores = weighted_scores
    
    return final_scores.clip(0, 1)


def analyze_anomalies(df: pd.DataFrame, 
                      method: str = 'ensemble',
                      threshold: float = 0.7) -> dict:
    """
    执行异常分析
    
    Args:
        df: 数据 DataFrame
        method: 检测方法 (zscore/iqr/isolation_forest/ensemble)
        threshold: 异常阈值
    
    Returns:
        分析结果字典
    """
    # 选择数值列
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in data")
    
    # 执行检测
    if method == 'zscore':
        # 对主要数值列进行 Z-Score 检测
        primary_col = numeric_cols[0]
        anomaly_scores = detect_zscore_anomalies(df[primary_col])
    elif method == 'iqr':
        primary_col = numeric_cols[0]
        anomaly_scores = detect_iqr_anomalies(df[primary_col])
    elif method == 'isolation_forest':
        anomaly_scores = detect_isolation_forest_anomalies(df[numeric_cols])
    else:  # ensemble
        anomaly_scores = ensemble_anomaly_detection(df)
    
    # 识别异常点
    anomalies = df[anomaly_scores >= threshold].copy()
    anomalies['anomaly_score'] = anomaly_scores[anomaly_scores >= threshold]
    
    # 统计信息
    results = {
        'total_records': len(df),
        'anomaly_count': len(anomalies),
        'anomaly_rate': len(anomalies) / len(df) if len(df) > 0 else 0,
        'method': method,
        'threshold': threshold,
        'score_stats': {
            'mean': float(anomaly_scores.mean()),
            'std': float(anomaly_scores.std()),
            'max': float(anomaly_scores.max()),
            'min': float(anomaly_scores.min()),
            'median': float(anomaly_scores.median())
        },
        'anomalies': anomalies,
        'scores': anomaly_scores
    }
    
    return results


def generate_report(results: dict, output_path: str = None) -> str:
    """生成异常检测报告"""
    report = []
    report.append("## 🔍 异常点检测报告")
    report.append("")
    report.append(f"**检测方法**: {results['method']}")
    report.append(f"**异常阈值**: {results['threshold']}")
    report.append("")
    
    report.append("### 检测摘要")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 总记录数 | {results['total_records']} |")
    report.append(f"| 异常点数 | {results['anomaly_count']} |")
    report.append(f"| 异常率 | {results['anomaly_rate']:.2%} |")
    report.append("")
    
    report.append("### 评分统计")
    stats = results['score_stats']
    report.append(f"| 统计项 | 数值 |")
    report.append(f"|--------|------|")
    report.append(f"| 平均值 | {stats['mean']:.4f} |")
    report.append(f"| 标准差 | {stats['std']:.4f} |")
    report.append(f"| 最大值 | {stats['max']:.4f} |")
    report.append(f"| 中位数 | {stats['median']:.4f} |")
    report.append("")
    
    anomalies = results['anomalies']
    if len(anomalies) > 0:
        report.append("### 异常点详情")
        report.append("")
        
        # 显示前 10 个异常点
        top_anomalies = anomalies.nlargest(10, 'anomaly_score')
        
        for idx, row in top_anomalies.iterrows():
            report.append(f"**记录 #{idx}** (异常评分：{row['anomaly_score']:.3f})")
            # 显示关键信息
            key_cols = [col for col in row.index if col != 'anomaly_score'][:5]
            for col in key_cols:
                report.append(f"- {col}: {row[col]}")
            report.append("")
    else:
        report.append("### 异常点详情")
        report.append("")
        report.append("未发现异常记录 ✅")
        report.append("")
    
    report.append("### 建议")
    anomaly_rate = results['anomaly_rate']
    if anomaly_rate > 0.1:
        report.append("⚠️ 异常率较高 (>10%)，建议:")
        report.append("1. 检查数据质量和采集流程")
        report.append("2. 调查异常点背后的原因")
        report.append("3. 考虑调整检测阈值")
    elif anomaly_rate > 0.05:
        report.append("⚡ 异常率中等 (5-10%)，建议:")
        report.append("1. 重点关注高评分异常点")
        report.append("2. 分析异常点的时间分布")
    else:
        report.append("✅ 异常率正常 (<5%)，数据质量良好")
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(description='博彩数据异常点检测工具')
    parser.add_argument('--data', required=True, help='输入数据文件路径 (CSV/JSON)')
    parser.add_argument('--method', default='ensemble',
                        choices=['zscore', 'iqr', 'isolation_forest', 'ensemble'],
                        help='检测方法')
    parser.add_argument('--threshold', type=float, default=0.7, 
                        help='异常阈值 (0-1)')
    parser.add_argument('--output', default=None, help='输出报告文件路径')
    parser.add_argument('--save-scores', default=None, 
                        help='保存异常评分到文件')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"加载数据：{args.data}")
    df = load_data(args.data)
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    # 执行异常检测
    print(f"使用 {args.method} 方法执行异常检测...")
    results = analyze_anomalies(df, args.method, args.threshold)
    
    # 生成报告
    report = generate_report(results, args.output)
    print("\n" + report)
    
    # 保存评分
    if args.save_scores:
        scores_df = pd.DataFrame({
            'anomaly_score': results['scores']
        })
        scores_df.to_csv(args.save_scores, index=True)
        print(f"\n异常评分已保存至：{args.save_scores}")
    
    if args.output:
        print(f"\n报告已保存至：{args.output}")


if __name__ == '__main__':
    main()
