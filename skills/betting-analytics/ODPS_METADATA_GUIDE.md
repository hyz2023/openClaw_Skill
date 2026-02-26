# ODPS 元数据采集指南

## 🎯 功能特性

### 1. 完整元数据采集
- ✅ 表基本信息（名称、注释、创建时间、大小）
- ✅ 字段详情（名称、类型、注释、是否可空）
- ✅ 分区信息（分区字段、分区值）
- ✅ **最新有数据的分区**（新增）

### 2. 进度实时汇报
- ✅ **每 30 秒自动汇报进度**（新增）
- ✅ 显示已处理表数、百分比
- ✅ 预计剩余时间
- ✅ 处理速度统计

### 3. 增量更新
- ✅ **智能判断表是否更新**（新增）
- ✅ 表大小未变则跳过
- ✅ 只更新有变化的表
- ✅ 支持定期执行（如每周）

## 🚀 使用方法

### 首次全量采集

```bash
cd /home/ubuntu/.openclaw/workspace
source venv/bin/activate

# 设置环境变量
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"

# 全量采集（约 30-40 分钟）
timeout 3600 python skills/betting-analytics/scripts/odps_metadata_crawler.py \
  --output odps_metadata \
  --full
```

### 增量更新（推荐定期执行）

```bash
# 增量更新（只更新有变化的表）
timeout 3600 python skills/betting-analytics/scripts/odps_metadata_crawler.py \
  --output odps_metadata
```

### 跳过分区检查（更快）

```bash
# 如果不需要分区信息，可以跳过（速度快很多）
timeout 600 python skills/betting-analytics/scripts/odps_metadata_crawler.py \
  --output odps_metadata \
  --no-partition-check
```

## 📊 进度汇报示例

```
⏰ [0:00:30] 进度：53/3141 (1.7%)
   当前：ads_bp_user_churn_features_active_di_0212
   预计剩余：29.1 分钟
   处理速度：106.0 表/分钟

⏰ [0:01:00] 进度：85/3141 (2.7%)
   当前：ads_gp_activity_white_data_di
   预计剩余：36.0 分钟
   处理速度：85.0 表/分钟
```

## 📁 输出文件

### 1. 完整元数据 (JSON)
```
odps_metadata/metadata_20260226_050000.json
odps_metadata/metadata_latest.json  (符号链接)
```

结构：
```json
{
  "table_name": "t_order_all",
  "comment": "投注订单表",
  "size": 1234567890,
  "create_time": "2024-01-01 00:00:00",
  "last_modified_time": "2026-02-26 00:00:00",
  "columns": [
    {
      "name": "login_name",
      "type": "STRING",
      "comment": "用户登录名",
      "is_nullable": true
    }
  ],
  "partition_status": {
    "is_partitioned": true,
    "partition_count": 365,
    "has_data": true,
    "latest_partition": {
      "name": "pt='20260226'",
      "value": "20260226",
      "size": 12345678,
      "records": 500000000
    }
  }
}
```

### 2. 字段清单 (CSV)
```
odps_metadata/columns_20260226_050000.csv
odps_metadata/columns_latest.csv  (符号链接)
```

列：
- table_name: 表名
- column_name: 字段名
- column_type: 字段类型
- comment: 字段注释
- is_nullable: 是否可空

### 3. 统计摘要 (JSON)
```
odps_metadata/summary_20260226_050000.json
```

包含：
- 总表数、总字段数
- 分区表数量
- 有数据的表数量
- 更新/跳过的表数量
- Top 10 字段最多的表
- 最新分区示例

### 4. 进度备份
```
odps_metadata/metadata_progress.json
```
每 50 张表自动保存一次进度，中断后可恢复

## 🔄 增量更新策略

### 判断逻辑
1. 加载已有元数据
2. 对每个表：
   - 获取当前表大小
   - 如果大小与已有元数据相同 → **跳过**
   - 如果大小不同或无历史记录 → **重新采集**
3. 分区信息始终检查（判断是否有新数据）

### 更新场景
| 场景 | 是否更新 | 说明 |
|------|---------|------|
| 表大小变化 | ✅ 更新 | 数据有增删 |
| 表大小不变 | ❌ 跳过 | 数据未变化 |
| 新增表 | ✅ 更新 | 新表 |
| 删除表 | - | 自动忽略 |
| 分区新增 | ✅ 更新 | 有新分区数据 |

### 定期执行建议

**每周更新**（推荐）：
```bash
# 添加到 crontab
0 2 * * 0 cd /home/ubuntu/.openclaw/workspace && \
    source venv/bin/activate && \
    export ALIBABA_ACCESSKEY_ID="..." && \
    export ALIBABA_ACCESSKEY_SECRET="..." && \
    export ALIBABA_ODPS_PROJECT="superengineproject" && \
    python skills/betting-analytics/scripts/odps_metadata_crawler.py \
      --output odps_metadata >> odps_metadata_cron.log 2>&1
```

**每天更新**（仅关键表）：
```bash
# 修改脚本，只采集指定表
# 在 list_all_tables 后添加过滤
table_names = [t for t in table_names if t.startswith('t_order')]
```

## 📈 性能优化

### 影响速度的因素
1. **表数量**: 3000 张表约需 30-40 分钟
2. **分区检查**: 每个表的分区列表查询耗时
3. **网络延迟**: ODPS API 响应时间
4. **并发限制**: ODPS API 调用频率限制

### 优化建议
1. **首次全量，后续增量**: 第一次后每周增量更新
2. **跳过分区检查**: 如不需要分区信息，使用 `--no-partition-check`
3. **分批采集**: 修改脚本按前缀分批采集
4. **后台运行**: 使用 `nohup` 或 `screen` 后台运行

### 后台运行示例
```bash
# 使用 nohup
nohup timeout 3600 python skills/betting-analytics/scripts/odps_metadata_crawler.py \
  --output odps_metadata > odps_metadata.log 2>&1 &

# 查看进度
tail -f odps_metadata.log

# 查看后台进程
ps aux | grep odps_metadata
```

## 🔍 使用采集的元数据

### 1. AI 检索
```bash
python skills/betting-analytics/scripts/odps_assistant.py search \
  -q "查询用户投注数据"
```

### 2. 查看最新分区
```python
import json

with open('odps_metadata/metadata_latest.json') as f:
    data = json.load(f)

for table in data['tables'][:10]:
    latest_pt = table.get('partition_status', {}).get('latest_partition')
    if latest_pt:
        print(f"{table['table_name']}: 最新分区 {latest_pt['value']}")
```

### 3. 查找有数据的表
```python
tables_with_data = [
    t for t in data['tables']
    if t.get('partition_status', {}).get('has_data')
]
print(f"有数据的表：{len(tables_with_data)}/{len(data['tables'])}")
```

## ⚠️ 注意事项

1. **超时设置**: 大量表采集需要足够超时时间
2. **中断恢复**: 中断后重新运行会自动增量继续
3. **磁盘空间**: 完整元数据约 10-50MB
4. **API 限制**: 避免高频并发调用

## 📝 故障排除

### 问题：采集速度太慢
**解决**: 
- 使用 `--no-partition-check` 跳过分区检查
- 或只采集特定前缀的表

### 问题：中途断开
**解决**:
- 重新运行即可，会自动从断点继续（增量模式）
- 或从 `metadata_progress.json` 恢复

### 问题：内存不足
**解决**:
- 分批采集（修改脚本添加表名过滤）
- 或增加系统内存

## 📚 相关文件

- [ODPS AI 检索工具](ODPS_AI_ASSISTANT.md)
- [元数据输出目录](../../odps_metadata/)
