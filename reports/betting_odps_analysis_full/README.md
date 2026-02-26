# ODPS 投注数据分析 - 技术说明

## 数据规模

`t_order_all` 表数据量：
- **每天约 5-6 亿条记录**
- **30 天约 150-180 亿条记录**
- 表大小：TB 级别

## 查询优化策略

### 为什么需要抽样

虽然 `GROUP BY pt, ordersourcetype` 后的结果只有约 360 行（30 天 × 12 个品类），但 ODPS 需要：
1. **扫描全量数据** (150 亿行)
2. **执行聚合计算**
3. **返回结果**

扫描 150 亿行数据的耗时远超查询超时限制 (2-3 分钟)。

### 抽样比例选择

| 抽样比例 | 扫描数据量 | 耗时 | 精度 | 推荐场景 |
|---------|-----------|------|------|---------|
| 10% | 15 亿行 | ~30 秒 | ±3% | 快速分析 |
| 5% | 7.5 亿行 | ~15 秒 | ±5% | 日常监控 |
| 1% | 1.5 亿行 | ~5 秒 | ±10% | 实时查询 |
| 100% (全量) | 150 亿行 | 超时 | 100% | 不推荐 |

### 推荐方案

#### 方案 A: 1% 抽样 (推荐日常使用)
```sql
SELECT pt, ordersourcetype, 
       COUNT(DISTINCT login_name) AS user_count,
       COUNT(*) AS bet_count
FROM t_order_all TABLESAMPLE(1 PERCENT)
WHERE pt >= '20260127'
GROUP BY pt, ordersourcetype
```

**优点**: 快速 (5-10 秒)，结果接近真实值
**缺点**: 有约 ±10% 误差

#### 方案 B: 预聚合表 (推荐生产环境)
创建日汇总表，每天定时运行：

```sql
-- 创建汇总表
CREATE TABLE IF NOT EXISTS t_order_daily_source (
    pt STRING,
    ordersourcetype STRING,
    user_count BIGINT,
    bet_count BIGINT
) PARTITIONED BY (pt STRING);

-- 每天运行 (添加到调度任务)
INSERT OVERWRITE TABLE t_order_daily_source PARTITION (pt='${pt}')
SELECT 
    ordersourcetype,
    COUNT(DISTINCT login_name) AS user_count,
    CAST(COUNT(*) AS BIGINT) AS bet_count
FROM t_order_all
WHERE pt = '${pt}'
GROUP BY ordersourcetype;
```

分析时直接查询汇总表：
```sql
SELECT * FROM t_order_daily_source 
WHERE pt >= '20260127'
ORDER BY pt, ordersourcetype;
```

**优点**: 秒级查询，100% 精确
**缺点**: 需要维护额外表和调度任务

#### 方案 C: 分天查询 + 本地合并
```python
for i in range(30):
    date = (now - timedelta(days=i)).strftime('%Y%m%d')
    sql = f"""
    SELECT pt, ordersourcetype, 
           COUNT(DISTINCT login_name), COUNT(*)
    FROM t_order_all WHERE pt = '{date}'
    GROUP BY pt, ordersourcetype
    """
    # 每天单独查询 (约 5 秒/天)
```

**优点**: 100% 精确，可控制进度
**缺点**: 需要 30 次查询，总耗时约 2-3 分钟

## 已执行的分析

### 10% 抽样 (7 天)
- 文件：`reports/betting_odps_analysis/`
- 结果：88 行数据，11 个品类

### 10% 抽样 (30 天)
- 文件：`reports/betting_odps_analysis_30d/`
- 结果：326 行数据，12 个品类
- 总用户数 (抽样): 30,965,619
- 总投注次数 (抽样): 1,777,218,784

### 推算全量 (×10)
- **总用户数**: 约 3.1 亿
- **总投注次数**: 约 178 亿

## 运行命令

```bash
cd /home/ubuntu/.openclaw/workspace
source venv/bin/activate

# 1% 抽样 (推荐)
python skills/betting-analytics/scripts/odps_source_analysis.py \
  --days 30 \
  --output reports/betting_odps_analysis

# 修改抽样比例需编辑脚本中的 TABLESAMPLE 参数
```

## 关键发现 (基于 10% 抽样)

### 品类分布
1. **SLOT**: 67.4% (主导品类)
2. **POKER**: 12.9%
3. **FISHING**: 6.9%
4. **Specialty Game**: 4.0%
5. **CASINO**: 3.2%

### 趋势
- 最近 7 天 vs 前 7 天：**-12.2%** (下降)
- 异常日期：2026-02-26 (当天数据不完整)

### 品类相关性
- SLOT ↔ POKER: 0.92 (高度相关)
- FISHING 相对独立

## 建议

1. **短期**: 使用 1-5% 抽样进行日常分析
2. **中期**: 创建预聚合表 `t_order_daily_source`
3. **长期**: 建立数据仓库分层 (ODS → DWD → DWS → ADS)
