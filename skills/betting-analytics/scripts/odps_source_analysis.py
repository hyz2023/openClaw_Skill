#!/usr/bin/env python3
"""
ODPS 投注数据品类分析
按 pt (日期) 和 ordersourcetype (品类) 分组统计，使用抽样查询

环境变量:
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from odps import ODPS


def query_odps_source_data(days: int = 30, sample_percent: float = 1.0) -> pd.DataFrame:
    """
    从 ODPS 查询按日期和品类分组的投注数据
    
    Args:
        days: 查询天数 (默认 30 天)
        sample_percent: 抽样比例 (1.0=100%, 0.1=10%)
    
    Returns:
        DataFrame with columns: pt, ordersourcetype, user_count, bet_count
    """
    # 加载环境变量
    access_id = os.getenv('ALIBABA_ACCESSKEY_ID')
    access_key = os.getenv('ALIBABA_ACCESSKEY_SECRET')
    project = os.getenv('ALIBABA_ODPS_PROJECT', 'superengineproject')
    endpoint = os.getenv('ALIBABA_ODPS_ENDPOINT', 'http://service.ap-southeast-1.maxcompute.aliyun.com/api')
    
    print(f"连接 ODPS 项目：{project}")
    print(f"查询天数：{days} 天")
    print(f"抽样比例：{sample_percent*100:.1f}%")
    
    o = ODPS(
        access_id=access_id,
        secret_access_key=access_key,
        project=project,
        endpoint=endpoint
    )
    
    # 计算日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
    
    # 构建 SQL (使用抽样)
    if sample_percent < 1.0:
        sample_clause = f"TABLESAMPLE({sample_percent*100:.1f} PERCENT)"
    else:
        sample_clause = ""
    
    sql = f"""
    SELECT 
        pt,
        ordersourcetype,
        COUNT(DISTINCT login_name) AS user_count,
        CAST(COUNT(*) AS BIGINT) AS bet_count
    FROM 
        t_order_all {sample_clause}
    WHERE 
        pt >= '{start_date}'
        AND pt <= '{end_date}'
        AND login_name IS NOT NULL
        AND ordersourcetype IS NOT NULL
    GROUP BY 
        pt, ordersourcetype
    ORDER BY 
        pt ASC, ordersourcetype ASC
    LIMIT 100000
    """
    
    print(f"\n执行 SQL 查询...")
    print(f"SQL 预览：{sql[:300]}...")
    
    try:
        with o.execute_sql(sql).open_reader() as reader:
            df = reader.to_pandas()
        
        print(f"\n✅ 查询成功！获取 {len(df)} 行数据")
        return df
        
    except Exception as e:
        print(f"❌ 查询失败：{e}")
        return None


def analyze_source_data(df: pd.DataFrame, output_dir: str = None) -> dict:
    """
    分析品类数据
    """
    print("\n" + "="*60)
    print("📊 ODPS 投注品类分析报告")
    print("="*60)
    
    results = {}
    
    # 数据概览
    print(f"\n## 数据概览")
    print(f"- 总记录数：{len(df):,}")
    print(f"- 日期范围：{df['pt'].min()} 到 {df['pt'].max()}")
    print(f"- 品类数量：{df['ordersourcetype'].nunique()}")
    print(f"- 品类列表：{', '.join(df['ordersourcetype'].unique()[:10])}")
    
    results['overview'] = {
        'total_records': len(df),
        'date_range': (df['pt'].min(), df['pt'].max()),
        'source_count': df['ordersourcetype'].nunique(),
        'sources': df['ordersourcetype'].unique().tolist()
    }
    
    # 总体统计
    print(f"\n## 总体统计")
    total_users = df['user_count'].sum()
    total_bets = df['bet_count'].sum()
    print(f"- 总用户数：{total_users:,}")
    print(f"- 总投注次数：{total_bets:,}")
    
    results['total'] = {
        'total_users': total_users,
        'total_bets': total_bets
    }
    
    # 品类排名
    print(f"\n## 品类排名 (按用户数)")
    print("-" * 60)
    
    source_summary = df.groupby('ordersourcetype').agg({
        'user_count': 'sum',
        'bet_count': 'sum'
    }).sort_values('user_count', ascending=False)
    
    print(f"\n| 排名 | 品类 | 用户数 | 占比 | 投注次数 |")
    print(f"|------|------|--------|------|----------|")
    
    for i, (source, row) in enumerate(source_summary.iterrows(), 1):
        pct = row['user_count'] / total_users * 100
        print(f"| {i} | {source} | {row['user_count']:,} | {pct:.1f}% | {row['bet_count']:,} |")
    
    results['source_ranking'] = source_summary.to_dict()
    
    # 每日趋势分析
    print(f"\n## 每日趋势分析")
    print("-" * 60)
    
    daily_summary = df.groupby('pt').agg({
        'user_count': 'sum',
        'bet_count': 'sum'
    }).reset_index()
    
    # 计算移动平均
    daily_summary['user_ma7'] = daily_summary['user_count'].rolling(7).mean()
    daily_summary['bet_ma7'] = daily_summary['bet_count'].rolling(7).mean()
    
    # 趋势判断
    recent_7d = daily_summary.tail(7)['user_count'].mean()
    previous_7d = daily_summary.iloc[-14:-7]['user_count'].mean() if len(daily_summary) >= 14 else daily_summary.head(7)['user_count'].mean()
    trend_change = (recent_7d - previous_7d) / previous_7d * 100
    
    print(f"- 最近 7 天日均用户：{recent_7d:,.0f}")
    print(f"- 前 7 天日均用户：{previous_7d:,.0f}")
    print(f"- 趋势变化：{trend_change:+.1f}%")
    
    results['daily_trend'] = {
        'recent_7d_avg': recent_7d,
        'previous_7d_avg': previous_7d,
        'trend_change': trend_change
    }
    
    # 异常检测
    print(f"\n## 异常检测")
    print("-" * 60)
    
    # 按日期检测异常
    daily_summary['user_zscore'] = (daily_summary['user_count'] - daily_summary['user_count'].mean()) / daily_summary['user_count'].std()
    anomalies = daily_summary[abs(daily_summary['user_zscore']) > 2]
    
    if len(anomalies) > 0:
        print(f"发现 {len(anomalies)} 个异常日期:")
        for _, row in anomalies.iterrows():
            level = "⚠️ 异常高" if row['user_zscore'] > 0 else "🔻 异常低"
            print(f"  - {row['pt']}: 用户数 {row['user_count']:,} (Z-Score: {row['user_zscore']:.2f}, {level})")
    else:
        print("✅ 未发现显著异常日期")
    
    results['anomalies'] = anomalies[['pt', 'user_count', 'user_zscore']].to_dict('records') if len(anomalies) > 0 else []
    
    # 品类 × 日期 热力图数据
    print(f"\n## 品类 × 日期 分布")
    print("-" * 60)
    
    pivot_data = df.pivot_table(
        index='pt',
        columns='ordersourcetype',
        values='user_count',
        aggfunc='sum',
        fill_value=0
    )
    
    print("品类分布相关性矩阵 (Top 5):")
    top_sources = source_summary.head(5).index.tolist()
    if len(top_sources) >= 2:
        corr_matrix = pivot_data[top_sources].corr()
        print(corr_matrix.round(2))
    
    # 保存数据
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存详细数据
        df.to_csv(output_path / 'source_daily_data.csv', index=False)
        print(f"\n📁 详细数据已保存：{output_path / 'source_daily_data.csv'}")
        
        # 保存汇总数据
        source_summary.to_csv(output_path / 'source_summary.csv')
        print(f"📁 汇总数据已保存：{output_path / 'source_summary.csv'}")
        
        # 保存每日数据
        daily_summary.to_csv(output_path / 'daily_summary.csv', index=False)
        print(f"📁 每日数据已保存：{output_path / 'daily_summary.csv'}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS 投注品类分析')
    parser.add_argument('--days', type=int, default=30, help='查询天数 (默认 30)')
    parser.add_argument('--sample', type=float, default=1.0, help='抽样比例 (0.01-1.0, 默认 1.0)')
    parser.add_argument('--output', default='reports/betting_odps_analysis', help='输出目录')
    
    args = parser.parse_args()
    
    # 查询数据
    df = query_odps_source_data(args.days, args.sample)
    
    if df is None or len(df) == 0:
        print("查询失败或无数据")
        return
    
    # 分析数据
    results = analyze_source_data(df, args.output)
    
    print("\n" + "="*60)
    print("✅ 分析完成!")
    print("="*60)


if __name__ == '__main__':
    main()
