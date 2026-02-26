#!/usr/bin/env python3
"""
博彩数据下钻分析工具
Drill-Down Analyzer for Betting Data

功能:
- 多维度层级下钻
- 数据聚合与对比
- 维度树导航
- 环比/同比分析
- 可视化输出
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_data(data_path: str) -> pd.DataFrame:
    """加载数据文件"""
    path = Path(data_path)
    if path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif path.suffix == '.json':
        df = pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    # 解析时间列
    time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if time_cols:
        df[time_cols[0]] = pd.to_datetime(df[time_cols[0]])
    
    return df


def get_dimension_hierarchy(dimensions: List[str]) -> Dict[str, List[str]]:
    """
    获取维度层级关系
    
    常见层级:
    - 时间：year > month > day > match
    - 组织：league > team > player
    - 市场：market_type > bet_type
    """
    hierarchy = {}
    
    # 时间维度层级
    time_dims = [d for d in dimensions if d.lower() in ['year', 'month', 'day', 'date', 'time']]
    if time_dims:
        hierarchy['time'] = ['year', 'month', 'day']
    
    # 组织维度层级
    org_dims = [d for d in dimensions if d.lower() in ['league', 'team', 'player', 'club']]
    if org_dims:
        hierarchy['organization'] = ['league', 'team', 'player']
    
    # 市场维度层级
    market_dims = [d for d in dimensions if d.lower() in ['market_type', 'bet_type', 'market']]
    if market_dims:
        hierarchy['market'] = ['market_type', 'bet_type']
    
    return hierarchy


def aggregate_by_dimension(df: pd.DataFrame, 
                           dimension: str, 
                           metrics: List[str] = None) -> pd.DataFrame:
    """
    按维度聚合数据
    
    Args:
        df: 数据 DataFrame
        dimension: 聚合维度
        metrics: 聚合指标列表
    
    Returns:
        聚合后的 DataFrame
    """
    if metrics is None:
        # 自动选择数值列作为指标
        metrics = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if dimension not in df.columns:
        # 尝试从时间列提取
        if dimension.lower() == 'year' and any('time' in col.lower() or 'date' in col.lower() for col in df.columns):
            time_col = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()][0]
            df = df.copy()
            df['year'] = pd.to_datetime(df[time_col]).dt.year
            dimension = 'year'
        elif dimension.lower() == 'month':
            time_col = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()][0]
            df = df.copy()
            df['month'] = pd.to_datetime(df[time_col]).dt.to_period('M').astype(str)
            dimension = 'month'
        elif dimension.lower() == 'day':
            time_col = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()][0]
            df = df.copy()
            df['day'] = pd.to_datetime(df[time_col]).dt.date.astype(str)
            dimension = 'day'
        else:
            raise ValueError(f"Dimension '{dimension}' not found in data")
    
    # 聚合
    agg_dict = {}
    for metric in metrics:
        if metric in df.columns:
            agg_dict[metric] = ['mean', 'sum', 'count', 'std']
    
    if not agg_dict:
        # 如果没有数值指标，只计数
        result = df.groupby(dimension).size().reset_index(name='count')
        return result
    
    result = df.groupby(dimension).agg(agg_dict)
    
    # 扁平化列名
    result.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col 
                      for col in result.columns]
    result = result.reset_index()
    
    return result


def calculate_comparison(df: pd.DataFrame,
                         dimension: str,
                         metrics: List[str],
                         comparison_type: str = '环比') -> pd.DataFrame:
    """
    计算对比指标 (环比/同比)
    
    Args:
        df: 数据 DataFrame
        dimension: 维度列
        metrics: 指标列表
        comparison_type: 对比类型 (环比/同比)
    
    Returns:
        带对比指标的 DataFrame
    """
    result = df.copy()
    
    # 按维度排序
    if dimension in result.columns:
        result = result.sort_values(dimension)
    
    for metric in metrics:
        metric_col = metric if metric in result.columns else f"{metric}_mean"
        
        if metric_col in result.columns:
            # 环比 (与上一期对比)
            result[f'{metric}_mom'] = result[metric_col].pct_change() * 100
            
            # 同比 (如果是时间序列，与去年同期对比)
            if comparison_type == '同比' and 'month' in result.columns:
                result[f'{metric}_yoy'] = result[metric_col] - result[metric_col].shift(12)
    
    return result


def drill_down(df: pd.DataFrame,
               dimensions: List[str],
               metrics: List[str] = None,
               filters: Dict[str, Any] = None) -> Dict[str, pd.DataFrame]:
    """
    执行下钻分析
    
    Args:
        df: 数据 DataFrame
        dimensions: 下钻维度列表
        metrics: 分析指标
        filters: 过滤条件
    
    Returns:
        各层级下钻结果字典
    """
    if metrics is None:
        metrics = df.select_dtypes(include=[np.number]).columns.tolist()[:5]
    
    if filters:
        for col, value in filters.items():
            if col in df.columns:
                df = df[df[col] == value]
    
    results = {}
    
    # 第 0 层：总体统计
    results['total'] = pd.DataFrame({
        'metric': metrics,
        'mean': [df[m].mean() for m in metrics if m in df.columns],
        'sum': [df[m].sum() for m in metrics if m in df.columns],
        'count': [len(df)] * len(metrics),
        'std': [df[m].std() for m in metrics if m in df.columns]
    })
    
    # 逐层下钻
    current_df = df
    for i, dim in enumerate(dimensions):
        if dim not in current_df.columns:
            # 尝试创建时间维度
            if dim.lower() in ['year', 'month', 'day']:
                time_col = [col for col in current_df.columns if 'time' in col.lower() or 'date' in col.lower()]
                if time_col:
                    time_col = time_col[0]
                    current_df = current_df.copy()
                    if dim.lower() == 'year':
                        current_df['year'] = pd.to_datetime(current_df[time_col]).dt.year
                    elif dim.lower() == 'month':
                        current_df['month'] = pd.to_datetime(current_df[time_col]).dt.to_period('M').astype(str)
                    elif dim.lower() == 'day':
                        current_df['day'] = pd.to_datetime(current_df[time_col]).dt.date.astype(str)
            else:
                print(f"警告：维度 '{dim}' 不存在，跳过")
                continue
        
        # 按当前维度聚合
        aggregated = aggregate_by_dimension(current_df, dim, metrics)
        
        # 计算对比指标
        if i > 0:
            aggregated = calculate_comparison(aggregated, dim, metrics)
        
        results[f'level_{i}_{dim}'] = aggregated
    
    return results


def analyze_drill_down(df: pd.DataFrame,
                       dimensions: List[str],
                       metrics: List[str] = None) -> dict:
    """
    执行完整的下钻分析
    
    Args:
        df: 数据 DataFrame
        dimensions: 下钻维度列表
        metrics: 分析指标
    
    Returns:
        分析结果字典
    """
    if metrics is None:
        # 自动选择数值列
        metrics = df.select_dtypes(include=[np.number]).columns.tolist()[:5]
    
    print(f"分析维度：{dimensions}")
    print(f"分析指标：{metrics}")
    
    # 执行下钻
    drill_results = drill_down(df, dimensions, metrics)
    
    # 获取维度层级
    hierarchy = get_dimension_hierarchy(dimensions)
    
    # 计算各维度的统计信息
    dimension_stats = {}
    for dim in dimensions:
        if dim in df.columns:
            dimension_stats[dim] = {
                'unique_values': df[dim].nunique(),
                'top_values': df[dim].value_counts().head(5).to_dict(),
                'missing_rate': df[dim].isna().mean()
            }
    
    results = {
        'dimensions': dimensions,
        'metrics': metrics,
        'hierarchy': hierarchy,
        'dimension_stats': dimension_stats,
        'drill_results': drill_results,
        'total_records': len(df),
        'time_range': {
            'start': str(df.min(numeric_only=True).iloc[0]) if len(df) > 0 else None,
            'end': str(df.max(numeric_only=True).iloc[0]) if len(df) > 0 else None
        } if any('time' in col.lower() or 'date' in col.lower() for col in df.columns) else None
    }
    
    return results


def generate_report(results: dict, output_path: str = None) -> str:
    """生成下钻分析报告"""
    report = []
    report.append("## 🔍 下钻分析报告")
    report.append("")
    report.append(f"**分析维度**: {', '.join(results['dimensions'])}")
    report.append(f"**分析指标**: {', '.join(results['metrics'])}")
    report.append(f"**总记录数**: {results['total_records']}")
    report.append("")
    
    # 维度统计
    report.append("### 维度概览")
    report.append("")
    report.append("| 维度 | 唯一值 | Top 值 | 缺失率 |")
    report.append("|------|--------|--------|--------|")
    
    for dim, stats in results['dimension_stats'].items():
        top_val = list(stats['top_values'].keys())[0] if stats['top_values'] else 'N/A'
        top_count = list(stats['top_values'].values())[0] if stats['top_values'] else 0
        report.append(f"| {dim} | {stats['unique_values']} | {top_val} ({top_count}) | {stats['missing_rate']:.1%} |")
    
    report.append("")
    
    # 总体统计
    report.append("### 总体统计")
    report.append("")
    total = results['drill_results'].get('total')
    if total is not None and len(total) > 0:
        report.append("| 指标 | 平均值 | 总和 | 标准差 | 样本数 |")
        report.append("|------|--------|------|--------|--------|")
        for _, row in total.iterrows():
            report.append(f"| {row['metric']} | {row['mean']:.4f} | {row['sum']:.2f} | {row['std']:.4f} | {int(row['count'])} |")
    report.append("")
    
    # 各层级下钻结果
    report.append("### 下钻详情")
    report.append("")
    
    for key, df_result in results['drill_results'].items():
        if key == 'total':
            continue
        
        report.append(f"#### {key}")
        report.append("")
        
        if df_result is not None and len(df_result) > 0:
            # 显示前 10 行
            display_df = df_result.head(10)
            
            # 转换为 markdown 表格
            columns = display_df.columns.tolist()
            report.append("| " + " | ".join(columns) + " |")
            report.append("|" + "|".join(["------"] * len(columns)) + "|")
            
            for _, row in display_df.iterrows():
                row_values = []
                for val in row:
                    if isinstance(val, float):
                        row_values.append(f"{val:.4f}" if not np.isnan(val) else "N/A")
                    else:
                        row_values.append(str(val))
                report.append("| " + " | ".join(row_values) + " |")
            
            report.append("")
    
    # 关键发现
    report.append("### 关键发现")
    report.append("")
    
    # 找出变化最大的维度
    for key, df_result in results['drill_results'].items():
        if key == 'total' or df_result is None or len(df_result) < 2:
            continue
        
        # 查找有 mom 列的
        mom_cols = [col for col in df_result.columns if 'mom' in col]
        if mom_cols:
            for mom_col in mom_cols[:2]:
                if mom_col in df_result.columns:
                    max_change_idx = df_result[mom_col].abs().idxmax()
                    max_change_row = df_result.loc[max_change_idx]
                    first_col = df_result.columns[0]
                    report.append(f"- **{max_change_row[first_col]}**: {mom_col.replace('_mom', '')} 变化 {max_change_row[mom_col]:.2f}%")
    
    report.append("")
    
    # 建议
    report.append("### 分析建议")
    report.append("")
    report.append("1. **深入分析异常值**: 关注变化幅度大的维度组合")
    report.append("2. **时间趋势**: 如果有时间维度，建议按时间序列深入分析")
    report.append("3. **对比基准**: 建立合理的对比基准 (如联赛平均、历史平均)")
    report.append("4. **可视化**: 建议使用旭日图、树状图展示层级关系")
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(description='博彩数据下钻分析工具')
    parser.add_argument('--data', required=True, help='输入数据文件路径 (CSV/JSON)')
    parser.add_argument('--dimensions', required=True, 
                        help='下钻维度列表 (逗号分隔，如：league,team,market)')
    parser.add_argument('--metrics', default=None,
                        help='分析指标列表 (逗号分隔，默认自动选择数值列)')
    parser.add_argument('--filters', default=None,
                        help='过滤条件 (格式：col1=val1,col2=val2)')
    parser.add_argument('--output', default=None, help='输出报告文件路径')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"加载数据：{args.data}")
    df = load_data(args.data)
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    # 解析维度
    dimensions = [d.strip() for d in args.dimensions.split(',')]
    
    # 解析指标
    metrics = None
    if args.metrics:
        metrics = [m.strip() for m in args.metrics.split(',')]
    
    # 解析过滤条件
    filters = None
    if args.filters:
        filters = {}
        for f in args.filters.split(','):
            if '=' in f:
                k, v = f.split('=', 1)
                filters[k.strip()] = v.strip()
    
    # 执行下钻分析
    print("执行下钻分析...")
    results = analyze_drill_down(df, dimensions, metrics)
    
    # 生成报告
    report = generate_report(results, args.output)
    print("\n" + report)
    
    if args.output:
        print(f"\n报告已保存至：{args.output}")


if __name__ == '__main__':
    main()
