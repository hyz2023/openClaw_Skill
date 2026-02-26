#!/usr/bin/env python3
"""查看 ODPS 表结构"""

import os
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

# 查看表结构
table_name = 't_order_all'
print(f"\n查看表结构：{table_name}")

table = o.get_table(table_name)
print(f"表名：{table.name}")
print(f"分区：{table.partitions if table.partitions else '非分区表'}")

print("\n字段列表:")
print("-" * 60)
print(f"{'字段名':<30} {'类型':<20} {'注释'}")
print("-" * 60)

for col in table.table_schema.columns:
    comment = col.comment if hasattr(col, 'comment') and col.comment else ''
    print(f"{col.name:<30} {str(col.type):<20} {comment}")

# 如果有分区，显示最新分区
if table.partitions:
    print("\n最新分区:")
    partitions = list(table.partitions)
    for pt in partitions[:10]:
        print(f"  {pt.name}")

# 预览数据
print("\n预览数据 (LIMIT 5):")
print("-" * 60)

try:
    # 尝试使用分区查询
    if table.partitions:
        latest_pt = partitions[0]
        sql = f"SELECT * FROM {table_name} LIMIT 5"
    else:
        sql = f"SELECT * FROM {table_name} LIMIT 5"
    
    with o.execute_sql(sql).open_reader() as reader:
        for row in reader:
            print(row)
except Exception as e:
    print(f"预览失败：{e}")
