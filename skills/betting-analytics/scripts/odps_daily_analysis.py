#!/usr/bin/env python3
"""
ODPS 投注数据日常分析脚本
统计最近一个月每天的投注数据，进行趋势分析和异常检测

使用前配置环境变量:
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 引入趋势分析和异常检测模块
sys.path.insert(0, str(Path(__file__).parent))
from trend_analyzer import analyze_trend, generate_report as trend_report
from anomaly_detector import analyze_anomalies, generate_report as anomaly_report
from drill_down_analyzer import analyze_drill_down, generate_report as drilldown_report


def check_odps_config():
    """检查 ODPS 配置"""
    required_vars = [
        'ALIBABA_ACCESSKEY_ID',
        'ALIBABA_ACCESSKEY_SECRET',
        'ALIBABA_ODPS_PROJECT'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print("❌ 缺少 ODPS 配置环境变量:")
        for var in missing:
            print(f"   - {var}")
        print("\n请设置环境变量后重试")
        return False
    
    return True


def query_odps_daily_data(project: str, days: int = 30) -> pd.DataFrame:
    """
    从 ODPS 查询最近 N 天每天的投注数据
    
    Args:
        project: ODPS 项目名称
        days: 查询天数 (默认 30 天)
    
    Returns:
        DataFrame with columns: dt, user_count, bet_count, total_amount
    """
    try:
        from odps import ODPS
    except ImportError:
        print("请安装 ODPS 库：pip install odps")
        return None
    
    # 初始化 ODPS 客户端
    access_id = os.getenv('ALIBABA_ACCESSKEY_ID')
    access_key = os.getenv('ALIBABA_ACCESSKEY_SECRET')
    endpoint = os.getenv('ALIBABA_ODPS_ENDPOINT', 'http://service.odps.aliyun.com/api')
    
    print(f"连接 ODPS 项目：{project}")
    
    o = ODPS(
        access_id=access_id,
        secret_access_key=access_key,
        project=project,
        endpoint=endpoint
    )
    
    # 计算日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    # SQL 查询：统计每天的投注数据
    sql = f"""
    SELECT 
        dt AS date,
        COUNT(DISTINCT login_name) AS user_count,
        COUNT(*) AS bet_count,
        SUM(bet_amount) AS total_amount,
        AVG(bet_amount) AS avg_amount,
        COUNT(DISTINCT ordersourcetype) AS source_count
    FROM 
        t_order_all
    WHERE 
        dt >= '{start_date}'
        AND dt <= '{end_date}'
        AND login_name IS NOT NULL
    GROUP BY 
        dt
    ORDER BY 
        dt ASC
    """
    
    print(f"执行 SQL 查询 (最近 {days} 天)...")
    
    # 执行查询
    with o.execute_sql(sql).open_reader() as reader:
        df = reader.to_pandas()
    
    # 转换日期列
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'].astype(str))
        df = df.set_index('date')
    
    print(f"查询完成，获取 {len(df)} 天的数据")
    
    return df


def generate_sample_daily_data(days: int = 30) -> pd.DataFrame:
    """生成示例日常数据 (用于测试)"""
    np.random.seed(42)
    
    # 生成日期序列
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # 生成基础数据 (带有趋势和周期性)
    trend = np.linspace(10000, 12000, days)  # 上升趋势
    weekly_pattern = np.sin(np.arange(days) * 2 * np.pi / 7) * 2000  # 周周期
    noise = np.random.normal(0, 1500, days)  # 随机噪声
    
    user_count = (trend + weekly_pattern + noise).astype(int)
    user_count = np.maximum(user_count, 1000)  # 确保非负
    
    # 投注次数 (与用户数相关，但有额外波动)
    bet_count = (user_count * np.random.uniform(3, 6, days)).astype(int)
    
    # 投注金额
    total_amount = user_count * np.random.uniform(100, 300, days)
    
    # 平均投注额
    avg_amount = total_amount / bet_count
    
    # 添加几个异常点
    anomaly_days = np.random.choice(days, 3)
    for day in anomaly_days:
        user_count[day] *= np.random.choice([0.3, 2.5])  # 异常低或异常高
        bet_count[day] = int(bet_count[day] * np.random.choice([0.4, 2.0]))
        total_amount[day] *= np.random.choice([0.5, 1.8])
    
    df = pd.DataFrame({
        'user_count': user_count,
        'bet_count': bet_count,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'source_count': np.random.randint(5, 10, days)
    }, index=dates)
    
    return df


def daily_trend_analysis(df: pd.DataFrame, output_dir: str = None) -> dict:
    """
    日常数据趋势分析
    """
    print("\n" + "="*60)
    print("📈 日常趋势分析")
    print("="*60)
    
    results = {}
    
    for metric in ['user_count', 'bet_count', 'total_amount']:
        if metric not in df.columns:
            continue
        
        print(f"\n## {metric} 趋势分析")
        print("-" * 40)
        
        series = df[metric]
        
        # 计算趋势指标
        ma7 = series.rolling(7).mean()
        ma14 = series.rolling(14).mean()
        
        # 趋势方向
        recent_7_avg = series.tail(7).mean()
        previous_7_avg = series.iloc[-14:-7].mean() if len(series) >= 14 else series.iloc[:7].mean()
        
        trend_change = (recent_7_avg - previous_7_avg) / previous_7_avg * 100
        
        if trend_change > 5:
            trend_direction = "上升"
        elif trend_change < -5:
            trend_direction = "下降"
        else:
            trend_direction = "平稳"
        
        # 波动率
        volatility = series.tail(7).std() / series.tail(7).mean() * 100
        
        print(f"最近 7 天平均值：{recent_7_avg:,.0f}")
        print(f"前 7 天平均值：{previous_7_avg:,.0f}")
        print(f"趋势变化：{trend_change:+.1f}% ({trend_direction})")
        print(f"近期波动率：{volatility:.1f}%")
        
        # 最高/最低值
        max_date = series.idxmax()
        min_date = series.idxmin()
        
        print(f"最高值：{series.max():,.0f} ({max_date.strftime('%Y-%m-%d')})")
        print(f"最低值：{series.min():,.0f} ({min_date.strftime('%Y-%m-%d')})")
        
        results[metric] = {
            'trend_direction': trend_direction,
            'trend_change': trend_change,
            'volatility': volatility,
            'max_value': series.max(),
            'max_date': str(max_date),
            'min_value': series.min(),
            'min_date': str(min_date),
            'recent_7d_avg': recent_7_avg,
            'ma7': ma7.tail(1).values[0] if not ma7.tail(1).empty else None,
            'ma14': ma14.tail(1).values[0] if not ma14.tail(1).empty else None
        }
    
    # 可视化数据
    print("\n## 可视化建议")
    print("-" * 40)
    print("建议生成以下图表:")
    print("  1. 折线图：每日用户数 + 7 日移动平均线")
    print("  2. 柱状图：每日投注金额")
    print("  3. 面积图：投注次数趋势")
    
    return results


def daily_anomaly_detection(df: pd.DataFrame, threshold: float = 0.7) -> dict:
    """
    日常数据异常检测
    """
    print("\n" + "="*60)
    print("🔍 异常点检测")
    print("="*60)
    
    results = {}
    all_anomalies = []
    
    for metric in ['user_count', 'bet_count', 'total_amount']:
        if metric not in df.columns:
            continue
        
        print(f"\n## {metric} 异常检测")
        print("-" * 40)
        
        series = df[metric].dropna()
        
        # Z-Score 方法
        mean = series.mean()
        std = series.std()
        z_scores = np.abs((series - mean) / std)
        
        # IQR 方法
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        # 识别异常点
        zscore_anomalies = z_scores > 2.5
        iqr_anomalies = (series < lower_bound) | (series > upper_bound)
        
        # 综合判断
        anomalies = zscore_anomalies | iqr_anomalies
        
        anomaly_dates = series.index[anomalies]
        
        if len(anomaly_dates) > 0:
            print(f"⚠️  发现 {len(anomaly_dates)} 个异常日期:")
            for date in anomaly_dates:
                value = series.loc[date]
                z = z_scores.loc[date]
                
                # 判断是异常高还是异常低
                if value > upper_bound:
                    level = "异常高"
                elif value < lower_bound:
                    level = "异常低"
                else:
                    level = "偏离均值"
                
                print(f"  - {date.strftime('%Y-%m-%d')}: {value:,.0f} (Z-Score: {z:.2f}, {level})")
                
                all_anomalies.append({
                    'date': str(date),
                    'metric': metric,
                    'value': value,
                    'z_score': float(z),
                    'level': level
                })
        else:
            print("✅ 未发现显著异常")
        
        results[metric] = {
            'anomaly_count': len(anomaly_dates),
            'anomaly_dates': [str(d) for d in anomaly_dates],
            'zscore_threshold': 2.5,
            'iqr_bounds': (lower_bound, upper_bound)
        }
    
    results['all_anomalies'] = all_anomalies
    
    if all_anomalies:
        print(f"\n📊 总计发现 {len(all_anomalies)} 个异常记录")
    else:
        print("\n✅ 所有指标均无显著异常")
    
    return results


def drill_down_on_anomaly(df: pd.DataFrame, anomaly_dates: list) -> dict:
    """
    对异常日期进行下钻分析
    """
    if not anomaly_dates:
        print("\n无需下钻分析 (无异常日期)")
        return {}
    
    print("\n" + "="*60)
    print("🔬 异常日期下钻分析")
    print("="*60)
    
    # 转换日期字符串为 datetime
    anomaly_dates_dt = [pd.to_datetime(d) for d in anomaly_dates]
    
    # 正常日期
    normal_dates = [d for d in df.index if d not in anomaly_dates_dt]
    
    if not normal_dates:
        print("⚠️  无法获取正常日期作为对比基准")
        return {}
    
    results = {}
    
    for anomaly_date in anomaly_dates_dt[:3]:  # 最多分析前 3 个异常日期
        print(f"\n## {anomaly_date.strftime('%Y-%m-%d')} 下钻分析")
        print("-" * 40)
        
        # 获取异常日数据
        anomaly_data = df.loc[[anomaly_date]]
        
        # 获取正常日平均数据
        normal_avg = df.loc[normal_dates].mean()
        
        # 对比分析
        print("\n与正常日均值对比:")
        for metric in ['user_count', 'bet_count', 'total_amount', 'avg_amount']:
            if metric in anomaly_data.columns and metric in normal_avg.index:
                anomaly_val = anomaly_data[metric].values[0]
                normal_val = normal_avg[metric]
                change = (anomaly_val - normal_val) / normal_val * 100
                
                if abs(change) > 20:
                    flag = "⚠️" if change > 0 else "🔻" if change < 0 else "➡️"
                else:
                    flag = "➡️"
                
                print(f"  {flag} {metric}: {anomaly_val:,.0f} (vs 正常 {normal_val:,.0f}, 变化 {change:+.1f}%)")
        
        # 分析可能的原因
        print("\n可能原因分析:")
        
        # 检查是否是周末/工作日
        day_of_week = anomaly_date.day_name()
        is_weekend = anomaly_date.weekday() >= 5
        
        if is_weekend:
            print(f"  - 该日期是 {day_of_week} (周末)，通常流量较高")
        else:
            print(f"  - 该日期是 {day_of_week} (工作日)")
        
        # 检查月初/月末效应
        day_of_month = anomaly_date.day
        if day_of_month <= 5:
            print(f"  - 月初 ({day_of_month}日)，可能有月初效应")
        elif day_of_month >= 25:
            print(f"  - 月末 ({day_of_month}日)，可能有月末效应")
        
        # 检查是否是节假日 (简化版)
        # 实际应用中应该接入节假日 API
        
        results[str(anomaly_date)] = {
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'day_of_month': day_of_month,
            'metrics_comparison': {
                metric: {
                    'anomaly_value': float(anomaly_data[metric].values[0]),
                    'normal_avg': float(normal_avg[metric]),
                    'change_pct': float((anomaly_data[metric].values[0] - normal_avg[metric]) / normal_avg[metric] * 100)
                }
                for metric in ['user_count', 'bet_count', 'total_amount']
                if metric in anomaly_data.columns
            }
        }
    
    return results


def generate_summary_report(trend_results: dict, anomaly_results: dict, 
                           drilldown_results: dict, output_path: str = None):
    """生成综合分析报告"""
    report = []
    report.append("# ODPS 投注数据日常分析报告")
    report.append("")
    report.append(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 趋势摘要
    report.append("## 📈 趋势摘要")
    report.append("")
    
    for metric, data in trend_results.items():
        if metric in ['user_count', 'bet_count', 'total_amount']:
            report.append(f"### {metric}")
            report.append(f"- 趋势方向：{data['trend_direction']}")
            report.append(f"- 趋势变化：{data['trend_change']:+.1f}%")
            report.append(f"- 近期波动率：{data['volatility']:.1f}%")
            report.append(f"- 最近 7 天均值：{data['recent_7d_avg']:,.0f}")
            report.append("")
    
    # 异常摘要
    report.append("## 🔍 异常检测摘要")
    report.append("")
    
    all_anomalies = anomaly_results.get('all_anomalies', [])
    
    if all_anomalies:
        report.append(f"**发现 {len(all_anomalies)} 个异常记录**:")
        report.append("")
        report.append("| 日期 | 指标 | 数值 | Z-Score | 类型 |")
        report.append("|------|------|------|---------|------|")
        
        for anomaly in all_anomalies:
            report.append(f"| {anomaly['date']} | {anomaly['metric']} | {anomaly['value']:,.0f} | {anomaly['z_score']:.2f} | {anomaly['level']} |")
    else:
        report.append("✅ 所有指标均无显著异常")
    
    report.append("")
    
    # 下钻分析摘要
    if drilldown_results:
        report.append("## 🔬 下钻分析摘要")
        report.append("")
        
        for date, data in drilldown_results.items():
            report.append(f"### {date}")
            report.append(f"- 星期：{data['day_of_week']} ({'周末' if data['is_weekend'] else '工作日'})")
            report.append(f"- 日期：{data['day_of_month']}日")
            report.append("")
            report.append("| 指标 | 异常值 | 正常均值 | 变化 |")
            report.append("|------|--------|---------|------|")
            
            for metric, comparison in data['metrics_comparison'].items():
                change = comparison['change_pct']
                arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                report.append(f"| {metric} | {comparison['anomaly_value']:,.0f} | {comparison['normal_avg']:,.0f} | {arrow} {change:+.1f}% |")
            
            report.append("")
    
    # 建议
    report.append("## 💡 建议")
    report.append("")
    
    if all_anomalies:
        report.append("1. **调查异常日期**: 检查是否有特殊事件、系统问题或数据质量问题")
        report.append("2. **监控趋势变化**: 如果趋势持续上升/下降，需要分析原因")
        report.append("3. **建立预警机制**: 对异常波动设置自动告警")
    else:
        report.append("1. **持续监控**: 保持日常数据监控")
        report.append("2. **建立基线**: 基于历史数据建立正常波动范围")
        report.append("3. **定期分析**: 建议每周/每月进行深度分析")
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n📁 综合报告已保存：{output_path}")
    
    return report_text


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS 投注数据日常分析')
    parser.add_argument('--project', default=None, help='ODPS 项目名称')
    parser.add_argument('--days', type=int, default=30, help='查询天数 (默认 30)')
    parser.add_argument('--output', default='reports/betting_daily_analysis', help='输出目录')
    parser.add_argument('--sample', action='store_true', help='使用示例数据 (测试用)')
    parser.add_argument('--anomaly-threshold', type=float, default=0.7, help='异常检测阈值')
    
    args = parser.parse_args()
    
    # 检查配置或使用示例数据
    if args.sample:
        print("使用示例数据进行分析...\n")
        df = generate_sample_daily_data(args.days)
    else:
        if not check_odps_config():
            print("\n切换到示例数据模式...")
            df = generate_sample_daily_data(args.days)
        else:
            project = args.project or os.getenv('ALIBABA_ODPS_PROJECT')
            if not project:
                print("请指定 ODPS 项目名称 (--project) 或设置 ALIBABA_ODPS_PROJECT 环境变量")
                sys.exit(1)
            
            df = query_odps_daily_data(project, args.days)
            
            if df is None or len(df) == 0:
                print("查询失败或无数据，使用示例数据...")
                df = generate_sample_daily_data(args.days)
    
    # 创建输出目录
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 1. 趋势分析
    trend_results = daily_trend_analysis(df)
    
    # 2. 异常检测
    anomaly_results = daily_anomaly_detection(df, args.anomaly_threshold)
    
    # 3. 下钻分析 (如果有异常)
    anomaly_dates = anomaly_results.get('all_anomalies', [])
    anomaly_date_list = [a['date'] for a in anomaly_dates]
    drilldown_results = drill_down_on_anomaly(df, anomaly_date_list)
    
    # 4. 生成综合报告
    report = generate_summary_report(
        trend_results, 
        anomaly_results, 
        drilldown_results,
        output_path / 'daily_analysis_report.md'
    )
    
    # 保存详细数据
    df.to_csv(output_path / 'daily_data.csv')
    print(f"📁 详细数据已保存：{output_path / 'daily_data.csv'}")
    
    # 打印报告
    print("\n" + "="*60)
    print("📋 综合分析报告")
    print("="*60)
    print(report)
    
    print("\n" + "="*60)
    print("✅ 分析完成!")
    print("="*60)


if __name__ == '__main__':
    main()
