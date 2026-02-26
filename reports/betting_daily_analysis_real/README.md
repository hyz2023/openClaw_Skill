# ODPS 真实数据分析报告

## 问题说明

由于 `t_order_all` 表数据量巨大（每天约 **5-6 亿条记录**），直接查询会导致超时。

### 解决方案

1. **使用分区裁剪**: 已经实现，按 `pt` 分区查询
2. **添加 LIMIT**: 已添加，限制返回行数
3. **抽样查询**: 建议使用 TABLESAMPLE
4. **预聚合**: 建议创建预聚合表

## 推荐查询方式

### 方式 1: 抽样查询 (推荐)

```sql
SELECT 
    pt,
    COUNT(DISTINCT login_name) AS user_count,
    CAST(COUNT(*) AS BIGINT) AS bet_count
FROM 
    t_order_all TABLESAMPLE(10)  -- 10% 抽样
WHERE 
    pt >= '20260127'
    AND login_name IS NOT NULL
GROUP BY pt
ORDER BY pt ASC
```

### 方式 2: 创建预聚合表

```sql
-- 创建日汇总表
CREATE TABLE IF NOT EXISTS t_order_daily_summary (
    pt STRING,
    user_count BIGINT,
    bet_count BIGINT,
    total_amount DOUBLE,
    avg_amount DOUBLE
);

-- 每日运行汇总
INSERT OVERWRITE TABLE t_order_daily_summary PARTITION (pt='${pt}')
SELECT 
    COUNT(DISTINCT login_name) AS user_count,
    CAST(COUNT(*) AS BIGINT) AS bet_count,
    SUM(CAST(bet_amount AS DOUBLE)) AS total_amount,
    AVG(CAST(bet_amount AS DOUBLE)) AS avg_amount
FROM t_order_all
WHERE pt = '${pt}';
```

### 方式 3: 分批次查询

每天单独查询，然后在本地合并：

```python
for i in range(30):
    date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
    sql = f"""
    SELECT pt, COUNT(DISTINCT login_name), COUNT(*)
    FROM t_order_all WHERE pt = '{date}'
    GROUP BY pt
    """
    # 执行查询并保存
```

## 已创建的脚本

| 脚本 | 说明 |
|------|------|
| `odps_describe.py` | 查看表结构 |
| `odps_simple_daily.py` | 简化日常查询 |
| `odps_daily_analysis.py` | 完整分析脚本 |
| `odps_test_query.py` | 测试查询 |

## 运行方式

```bash
cd /home/ubuntu/.openclaw/workspace
source venv/bin/activate

# 设置环境变量 (已在 ~/.bashrc 中)
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"

# 运行简化查询
python skills/betting-analytics/scripts/odps_simple_daily.py

# 运行完整分析 (使用示例数据)
python skills/betting-analytics/scripts/odps_daily_analysis.py --sample --days 30
```

## 表结构摘要

```
t_order_all 表字段 (部分关键字段):
- pt (STRING): 分区字段，格式 yyyymmdd
- login_name (STRING): 用户登录名
- bet_amount (STRING): 投注金额
- ordersourcetype (STRING): 订单来源类型
- billtime (DATETIME): 账单时间
- platform_id (STRING): 平台 ID
- game_kind (BIGINT): 游戏种类
```

## 数据量统计

最近 30 天每天数据量：
- 2026-02-26: 1.55 亿条
- 2026-02-25: 5.43 亿条
- 2026-02-24: 5.32 亿条
- ...
- 平均每天约 **5.5 亿条记录**

需要处理如此大规模数据时，强烈建议使用预聚合或抽样策略。
