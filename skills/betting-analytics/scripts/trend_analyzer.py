#!/usr/bin/env python3
"""
博彩数据趋势分析工具
Trend Analyzer for Betting Data

功能:
- 赔率走势分析
- 投注量趋势
- 移动平均线
- 趋势线拟合
- 支撑位/阻力位识别
"""

import argparse
import pandas as pd
import numpy as np
from datetime import datetime
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
    
    # 解析时间列
    time_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
    if time_cols:
        df[time_cols[0]] = pd.to_datetime(df[time_cols[0]])
        df = df.sort_values(time_cols[0])
    
    return df


def calculate_moving_average(series: pd.Series, window: int) -> pd.Series:
    """计算移动平均线"""
    return series.rolling(window=window, min_periods=1).mean()


def calculate_trend_line(series: pd.Series) -> tuple:
    """计算趋势线 (线性回归)"""
    x = np.arange(len(series))
    y = series.values
    
    # 处理 NaN 值
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return None, None
    
    x_valid = x[mask]
    y_valid = y[mask]
    
    # 线性回归
    slope, intercept = np.polyfit(x_valid, y_valid, 1)
    trend_line = slope * x + intercept
    
    return slope, trend_line


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """计算 RSI 指标"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def identify_support_resistance(series: pd.Series, window: int = 20) -> tuple:
    """识别支撑位和阻力位"""
    rolling_min = series.rolling(window=window, center=True).min()
    rolling_max = series.rolling(window=window, center=True).max()
    
    # 找到局部最低点 (支撑位)
    support_mask = (series == rolling_min) & (rolling_min.notna())
    support_levels = series[support_mask].dropna()
    
    # 找到局部最高点 (阻力位)
    resistance_mask = (series == rolling_max) & (rolling_max.notna())
    resistance_levels = series[resistance_mask].dropna()
    
    return support_levels, resistance_levels


def calculate_volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """计算波动率 (滚动标准差)"""
    return series.rolling(window=window).std()


def analyze_trend(df: pd.DataFrame, target_col: str = None, window: int = 30) -> dict:
    """
    执行趋势分析
    
    Args:
        df: 数据 DataFrame
        target_col: 目标分析列 (如 odds_home, bet_volume)
        window: 分析窗口大小
    
    Returns:
        分析结果字典
    """
    # 自动选择目标列
    if target_col is None:
        odds_cols = [col for col in df.columns if 'odds' in col.lower()]
        if odds_cols:
            target_col = odds_cols[0]
        else:
            target_col = df.columns[-1]
    
    if target_col not in df.columns:
        raise ValueError(f"Column '{target_col}' not found in data")
    
    series = df[target_col].astype(float)
    
    # 计算各项指标
    ma5 = calculate_moving_average(series, 5)
    ma10 = calculate_moving_average(series, 10)
    ma20 = calculate_moving_average(series, 20)
    
    slope, trend_line = calculate_trend_line(series)
    
    rsi = calculate_rsi(series)
    
    support_levels, resistance_levels = identify_support_resistance(series)
    
    volatility = calculate_volatility(series)
    
    # 计算趋势方向
    if slope is not None:
        if slope > 0.01:
            trend_direction = "上升"
        elif slope < -0.01:
            trend_direction = "下降"
        else:
            trend_direction = "盘整"
    else:
        trend_direction = "数据不足"
    
    # 计算最新值相对于 MA 的位置
    latest_value = series.iloc[-1] if not np.isnan(series.iloc[-1]) else series.dropna().iloc[-1]
    latest_ma20 = ma20.iloc[-1] if not np.isnan(ma20.iloc[-1]) else ma20.dropna().iloc[-1]
    
    if latest_value > latest_ma20 * 1.02:
        position = "高于均线 (偏强)"
    elif latest_value < latest_ma20 * 0.98:
        position = "低于均线 (偏弱)"
    else:
        position = "围绕均线 (中性)"
    
    # 构建结果
    results = {
        'target_column': target_col,
        'data_points': len(series.dropna()),
        'trend_direction': trend_direction,
        'trend_slope': slope if slope else 0,
        'position_vs_ma': position,
        'latest_value': latest_value,
        'ma5': ma5.iloc[-1] if not np.isnan(ma5.iloc[-1]) else None,
        'ma10': ma10.iloc[-1] if not np.isnan(ma10.iloc[-1]) else None,
        'ma20': ma20.iloc[-1] if not np.isnan(ma20.iloc[-1]) else None,
        'latest_rsi': rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else None,
        'latest_volatility': volatility.iloc[-1] if not np.isnan(volatility.iloc[-1]) else None,
        'support_levels': support_levels.tail(3).tolist() if len(support_levels) > 0 else [],
        'resistance_levels': resistance_levels.tail(3).tolist() if len(resistance_levels) > 0 else [],
        'time_range': {
            'start': str(df.iloc[0].iloc[0]) if len(df) > 0 else None,
            'end': str(df.iloc[-1].iloc[0]) if len(df) > 0 else None
        }
    }
    
    return results


def generate_report(results: dict, output_path: str = None) -> str:
    """生成分析报告"""
    report = []
    report.append("## 📊 趋势分析报告")
    report.append("")
    report.append(f"**分析指标**: {results['target_column']}")
    report.append(f"**数据点数**: {results['data_points']}")
    report.append("")
    
    report.append("### 趋势概览")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 趋势方向 | {results['trend_direction']} |")
    report.append(f"| 趋势斜率 | {results['trend_slope']:.4f} |")
    report.append(f"| 当前位置 | {results['position_vs_ma']} |")
    report.append(f"| 最新值 | {results['latest_value']:.4f} |")
    report.append("")
    
    report.append("### 移动平均线")
    report.append(f"| 周期 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| MA5 | {results['ma5']:.4f}" if results['ma5'] else "| MA5 | N/A |")
    report.append(f"| MA10 | {results['ma10']:.4f}" if results['ma10'] else "| MA10 | N/A |")
    report.append(f"| MA20 | {results['ma20']:.4f}" if results['ma20'] else "| MA20 | N/A |")
    report.append("")
    
    if results['latest_rsi']:
        rsi_status = "超买" if results['latest_rsi'] > 70 else "超卖" if results['latest_rsi'] < 30 else "中性"
        report.append("### RSI 指标")
        report.append(f"- 最新 RSI: {results['latest_rsi']:.2f} ({rsi_status})")
        report.append("")
    
    if results['support_levels'] or results['resistance_levels']:
        report.append("### 支撑位与阻力位")
        if results['support_levels']:
            report.append(f"- 支撑位: {', '.join([f'{x:.2f}' for x in results['support_levels']])}")
        if results['resistance_levels']:
            report.append(f"- 阻力位: {', '.join([f'{x:.2f}' for x in results['resistance_levels']])}")
        report.append("")
    
    if results['latest_volatility']:
        vol_status = "高" if results['latest_volatility'] > 0.1 else "中" if results['latest_volatility'] > 0.05 else "低"
        report.append("### 波动率")
        report.append(f"- 当前波动率：{results['latest_volatility']:.4f} ({vol_status})")
        report.append("")
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(description='博彩数据趋势分析工具')
    parser.add_argument('--data', required=True, help='输入数据文件路径 (CSV/JSON)')
    parser.add_argument('--type', dest='target_col', default=None, 
                        help='目标分析列 (如 odds_home, bet_volume)')
    parser.add_argument('--window', type=int, default=30, help='分析窗口大小 (天数)')
    parser.add_argument('--output', default=None, help='输出报告文件路径')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"加载数据：{args.data}")
    df = load_data(args.data)
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    # 执行趋势分析
    print("执行趋势分析...")
    results = analyze_trend(df, args.target_col, args.window)
    
    # 生成报告
    report = generate_report(results, args.output)
    print("\n" + report)
    
    if args.output:
        print(f"\n报告已保存至：{args.output}")


if __name__ == '__main__':
    main()
