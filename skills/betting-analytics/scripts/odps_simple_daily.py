#!/usr/bin/env python3
"""
ODPS 简化日常查询 - 只获取关键指标
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from odps import ODPS

# 加载环境变量
access_id = os.getenv('ALIBABA_ACCESSKEY_ID')
access_key = os.getenv('ALIBABA_ACCESSKEY_SECRET')
project = os.getenv('ALIBABA_ODPS_PROJECT')
endpoint = os.getenv('ALIBABA_ODPS_ENDPOINT', 'http://service.ap-southeast-1.maxcompute.aliyun.com/api')

print(f"连接 ODPS 项目：{project}")

o = ODPS(
    access_id=access_id,
    secret_access_key=access_key,
    project=project,
    endpoint=endpoint
)

# 计算日期范围
days = 30
end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

print(f"查询日期范围：{start_date} 到 {end_date}")

# 简化查询 - 只统计关键指标
sql = f"""
SELECT 
    pt,
    COUNT(DISTINCT login_name) AS user_count,
    CAST(COUNT(*) AS BIGINT) AS bet_count
FROM 
    t_order_all
WHERE 
    pt >= '{start_date}'
    AND login_name IS NOT NULL
GROUP BY 
    pt
ORDER BY 
    pt ASC
LIMIT 100
"""

print(f"执行 SQL 查询...")

try:
    with o.execute_sql(sql).open_reader() as reader:
        df = reader.to_pandas()
        print(f"\n✅ 查询成功！获取 {len(df)} 天数据\n")
        print(df)
        
        # 保存数据
        output_file = 'reports/betting_daily_analysis_real/odps_daily_data.csv'
        import os
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n数据已保存：{output_file}")
        
except Exception as e:
    print(f"❌ 查询失败：{e}")
