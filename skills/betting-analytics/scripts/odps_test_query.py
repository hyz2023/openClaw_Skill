#!/usr/bin/env python3
"""测试 ODPS 查询"""

import os
from odps import ODPS

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

# 简单查询测试
sql = """
SELECT 
    pt,
    COUNT(*) as cnt
FROM 
    t_order_all
WHERE 
    pt >= '20260127'
GROUP BY pt
ORDER BY pt DESC
LIMIT 30
"""

print(f"执行 SQL...")
print(sql)

try:
    with o.execute_sql(sql).open_reader() as reader:
        df = reader.to_pandas()
        print(f"\n查询成功！获取 {len(df)} 行")
        print(df)
except Exception as e:
    print(f"查询失败：{e}")
