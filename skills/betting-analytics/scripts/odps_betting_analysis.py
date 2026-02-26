#!/usr/bin/env python3
"""
ODPS 投注数据分析脚本
从 ODPS t_order_all 表提取最近一个月数据，进行统计分析

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
import subprocess
import sys


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
        print("\n请设置环境变量后重试:")
        print("  export ALIBABA_ACCESSKEY_ID='your_key_id'")
        print("  export ALIBABA_ACCESSKEY_SECRET='your_key_secret'")
        print("  export ALIBABA_ODPS_PROJECT='your_project'")
        print("  export ALIBABA_ODPS_ENDPOINT='http://service.odps.aliyun.com/api' (可选)")
        return False
    
    return True


def query_odps_data(project: str, days: int = 30) -> pd.DataFrame:
    """
    从 ODPS 查询最近 N 天的投注数据
    
    Args:
        project: ODPS 项目名称
        days: 查询天数 (默认 30 天)
    
    Returns:
        DataFrame with columns: ordersourcetype, user_count, bet_count, bet_amount
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
    
    # SQL 查询：统计不同品类的用户数、投注次数、投注金额
    sql = f"""
    SELECT 
        ordersourcetype AS source_type,
        COUNT(DISTINCT login_name) AS user_count,
        COUNT(*) AS bet_count,
        SUM(bet_amount) AS total_amount,
        AVG(bet_amount) AS avg_amount,
        MIN(bet_amount) AS min_amount,
        MAX(bet_amount) AS max_amount
    FROM 
        t_order_all
    WHERE 
        dt >= '{start_date}'
        AND dt <= '{end_date}'
        AND ordersourcetype IS NOT NULL
    GROUP BY 
        ordersourcetype
    ORDER BY 
        user_count DESC
    """
    
    print(f"执行 SQL 查询 (最近 {days} 天)...")
    print(f"SQL: {sql[:200]}...")
    
    # 执行查询
    with o.execute_sql(sql).open_reader() as reader:
        df = reader.to_pandas()
    
    print(f"查询完成，获取 {len(df)} 个品类数据")
    
    return df


def generate_sample_data() -> pd.DataFrame:
    """生成示例数据 (用于测试)"""
    np.random.seed(42)
    
    source_types = [
        'APP_IOS', 'APP_ANDROID', 'WAP', 'PC', 'H5', 
        'API', 'WECHAT', 'ALIPAY'
    ]
    
    n_sources = len(source_types)
    
    data = {
        'source_type': source_types,
        'user_count': np.random.randint(1000, 50000, n_sources),
        'bet_count': np.random.randint(5000, 200000, n_sources),
        'total_amount': np.random.uniform(100000, 5000000, n_sources),
        'avg_amount': np.random.uniform(50, 500, n_sources),
        'min_amount': np.random.uniform(10, 50, n_sources),
        'max_amount': np.random.uniform(10000, 100000, n_sources)
    }
    
    df = pd.DataFrame(data)
    df['total_amount'] = df['total_amount'].round(2)
    df['avg_amount'] = df['avg_amount'].round(2)
    
    return df


def analyze_betting_data(df: pd.DataFrame, output_dir: str = None) -> dict:
    """
    分析投注数据
    
    Args:
        df: 数据 DataFrame (包含 source_type, user_count, bet_count, total_amount 等列)
        output_dir: 输出目录
    
    Returns:
        分析结果字典
    """
    print("\n" + "="*60)
    print("📊 博彩数据分析报告")
    print("="*60)
    
    results = {}
    
    # 1. 基本统计
    print("\n## 1. 基本统计")
    print("-" * 40)
    
    total_users = df['user_count'].sum()
    total_bets = df['bet_count'].sum()
    total_amount = df['total_amount'].sum()
    
    print(f"总投注用户数：{total_users:,}")
    print(f"总投注次数：{total_bets:,}")
    print(f"总投注金额：{total_amount:,.2f}")
    print(f"品类数量：{len(df)}")
    print(f"平均单品类用户数：{df['user_count'].mean():,.0f}")
    print(f"平均单品类投注额：{df['total_amount'].mean():,.2f}")
    
    results['basic_stats'] = {
        'total_users': total_users,
        'total_bets': total_bets,
        'total_amount': total_amount,
        'source_count': len(df)
    }
    
    # 2. 品类排名分析
    print("\n## 2. 品类排名分析 (按用户数)")
    print("-" * 40)
    
    df_sorted = df.sort_values('user_count', ascending=False)
    
    print("\n| 排名 | 品类 | 用户数 | 占比 | 投注次数 | 投注额 |")
    print("|------|------|--------|------|----------|--------|")
    
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        user_pct = row['user_count'] / total_users * 100
        print(f"| {i} | {row['source_type']} | {row['user_count']:,} | {user_pct:.1f}% | {row['bet_count']:,} | {row['total_amount']:,.0f} |")
    
    results['ranking'] = df_sorted.to_dict('records')
    
    # 3. 集中度分析
    print("\n## 3. 集中度分析")
    print("-" * 40)
    
    # CR3/CR5 集中度
    top3_users = df_sorted.head(3)['user_count'].sum()
    top5_users = df_sorted.head(5)['user_count'].sum()
    
    cr3 = top3_users / total_users * 100
    cr5 = top5_users / total_users * 100
    
    print(f"CR3 (前 3 大品类集中度): {cr3:.1f}%")
    print(f"CR5 (前 5 大品类集中度): {cr5:.1f}%")
    
    # 赫芬达尔指数 (HHI)
    hhi = sum((row['user_count'] / total_users) ** 2 for _, row in df.iterrows()) * 10000
    print(f"赫芬达尔指数 (HHI): {hhi:.0f}")
    
    if hhi < 1500:
        hhi_interpretation = "竞争型市场 (分散)"
    elif hhi < 2500:
        hhi_interpretation = "适度集中"
    else:
        hhi_interpretation = "高度集中"
    
    print(f"市场结构：{hhi_interpretation}")
    
    results['concentration'] = {
        'cr3': cr3,
        'cr5': cr5,
        'hhi': hhi,
        'interpretation': hhi_interpretation
    }
    
    # 4. 趋势分析 (模拟时间序列)
    print("\n## 4. 品类对比分析")
    print("-" * 40)
    
    # 用户价值分析 (ARPU)
    df['arpu'] = df['total_amount'] / df['user_count']
    
    print("\n用户平均价值 (ARPU) 排名:")
    arpu_ranking = df.sort_values('arpu', ascending=False)
    
    for i, (_, row) in enumerate(arpu_ranking.head(5).iterrows(), 1):
        print(f"  {i}. {row['source_type']}: ¥{row['arpu']:.2f}/用户")
    
    # 投注频率分析
    df['bet_freq'] = df['bet_count'] / df['user_count']
    
    print("\n用户投注频率排名:")
    freq_ranking = df.sort_values('bet_freq', ascending=False)
    
    for i, (_, row) in enumerate(freq_ranking.head(5).iterrows(), 1):
        print(f"  {i}. {row['source_type']}: {row['bet_freq']:.1f} 次/用户")
    
    results['arpu_analysis'] = {
        'top_arpu': arpu_ranking.head(5)[['source_type', 'arpu']].to_dict('records'),
        'top_frequency': freq_ranking.head(5)[['source_type', 'bet_freq']].to_dict('records')
    }
    
    # 5. 异常检测
    print("\n## 5. 异常检测")
    print("-" * 40)
    
    # Z-Score 检测异常值
    from scipy import stats
    
    z_scores_users = np.abs(stats.zscore(df['user_count']))
    z_scores_amount = np.abs(stats.zscore(df['total_amount']))
    
    anomalies = []
    
    for i, (_, row) in enumerate(df.iterrows()):
        if z_scores_users[i] > 2 or z_scores_amount[i] > 2:
            anomalies.append({
                'source_type': row['source_type'],
                'user_zscore': z_scores_users[i],
                'amount_zscore': z_scores_amount[i]
            })
    
    if anomalies:
        print(f"发现 {len(anomalies)} 个异常品类:")
        for a in anomalies:
            print(f"  ⚠️  {a['source_type']}: 用户数 Z={a['user_zscore']:.2f}, 金额 Z={a['amount_zscore']:.2f}")
    else:
        print("✅ 未发现显著异常品类")
    
    results['anomalies'] = anomalies
    
    # 6. 可视化数据准备
    print("\n## 6. 可视化建议")
    print("-" * 40)
    print("建议生成以下图表:")
    print("  1. 柱状图：各品类用户数对比")
    print("  2. 饼图：用户数占比分布")
    print("  3. 散点图：ARPU vs 投注频率")
    print("  4. 热力图：品类 × 指标相关性")
    
    # 保存分析结果
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存详细数据
        df.to_csv(output_path / 'source_type_analysis.csv', index=False)
        print(f"\n📁 详细数据已保存：{output_path / 'source_type_analysis.csv'}")
        
        # 保存分析报告
        report_path = output_path / 'analysis_report.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# ODPS 投注数据分析报告\n\n")
            f.write(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## 总览\n")
            f.write(f"- 总用户数：{total_users:,}\n")
            f.write(f"- 总投注次数：{total_bets:,}\n")
            f.write(f"- 总投注金额：{total_amount:,.2f}\n")
            f.write(f"- 品类数量：{len(df)}\n\n")
            f.write(f"## 集中度\n")
            f.write(f"- CR3: {cr3:.1f}%\n")
            f.write(f"- CR5: {cr5:.1f}%\n")
            f.write(f"- HHI: {hhi:.0f} ({hhi_interpretation})\n")
        
        print(f"📁 分析报告已保存：{report_path}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS 投注数据分析')
    parser.add_argument('--project', default=None, help='ODPS 项目名称')
    parser.add_argument('--days', type=int, default=30, help='查询天数 (默认 30)')
    parser.add_argument('--output', default='reports/betting_analysis', help='输出目录')
    parser.add_argument('--sample', action='store_true', help='使用示例数据 (测试用)')
    
    args = parser.parse_args()
    
    # 检查配置或使用示例数据
    if args.sample:
        print("使用示例数据进行分析...\n")
        df = generate_sample_data()
    else:
        if not check_odps_config():
            print("\n切换到示例数据模式...")
            df = generate_sample_data()
        else:
            project = args.project or os.getenv('ALIBABA_ODPS_PROJECT')
            if not project:
                print("请指定 ODPS 项目名称 (--project) 或设置 ALIBABA_ODPS_PROJECT 环境变量")
                sys.exit(1)
            
            df = query_odps_data(project, args.days)
            
            if df is None or len(df) == 0:
                print("查询失败或无数据，使用示例数据...")
                df = generate_sample_data()
    
    # 执行分析
    results = analyze_betting_data(df, args.output)
    
    print("\n" + "="*60)
    print("✅ 分析完成!")
    print("="*60)


if __name__ == '__main__':
    main()
