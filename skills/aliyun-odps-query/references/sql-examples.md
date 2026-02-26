# ODPS SQL 查询示例

## 基础查询

### 1. 简单查询
```sql
-- 查询前 100 行
SELECT * FROM table_name LIMIT 100;

-- 查询指定列
SELECT col1, col2, col3 FROM table_name;

-- 去重查询
SELECT DISTINCT col1 FROM table_name;
```

### 2. 条件过滤
```sql
-- 等于条件
SELECT * FROM table_name WHERE status = 1;

-- 范围条件
SELECT * FROM table_name WHERE age BETWEEN 18 AND 65;

-- IN 条件
SELECT * FROM table_name WHERE city IN ('Beijing', 'Shanghai', 'Guangzhou');

-- LIKE 模糊匹配
SELECT * FROM table_name WHERE name LIKE '张%';

-- 多条件组合
SELECT * FROM table_name 
WHERE status = 1 
  AND created_date >= '2026-01-01'
  AND amount > 1000;
```

### 3. 排序和分页
```sql
-- 单列排序
SELECT * FROM table_name ORDER BY created_date DESC;

-- 多列排序
SELECT * FROM table_name 
ORDER BY category ASC, price DESC;

-- 分页查询 (ODPS 使用 LIMIT)
SELECT * FROM table_name ORDER BY id LIMIT 100 OFFSET 0;  -- 第一页
SELECT * FROM table_name ORDER BY id LIMIT 100 OFFSET 100; -- 第二页
```

## 聚合统计

### 4. 基础聚合
```sql
-- 计数
SELECT COUNT(*) FROM table_name;
SELECT COUNT(DISTINCT user_id) FROM table_name;

-- 求和
SELECT SUM(amount) as total_amount FROM table_name;

-- 平均值
SELECT AVG(price) as avg_price FROM table_name;

-- 最大/最小值
SELECT MAX(created_date) as latest_date, 
       MIN(created_date) as earliest_date 
FROM table_name;
```

### 5. 分组统计
```sql
-- 单列分组
SELECT category, COUNT(*) as cnt
FROM table_name
GROUP BY category;

-- 多列分组
SELECT category, status, COUNT(*) as cnt, SUM(amount) as total
FROM table_name
GROUP BY category, status;

-- 分组后过滤
SELECT category, COUNT(*) as cnt
FROM table_name
GROUP BY category
HAVING COUNT(*) > 100;

-- 分组排序
SELECT category, COUNT(*) as cnt
FROM table_name
GROUP BY category
ORDER BY cnt DESC
LIMIT 10;
```

## 多表关联

### 6. JOIN 操作
```sql
-- INNER JOIN
SELECT a.user_id, a.name, b.order_id, b.amount
FROM user_info a
INNER JOIN order_detail b ON a.user_id = b.user_id;

-- LEFT JOIN
SELECT a.user_id, a.name, b.order_id
FROM user_info a
LEFT JOIN order_detail b ON a.user_id = b.user_id;

-- 多表关联
SELECT a.user_id, a.name, b.order_id, c.product_name
FROM user_info a
INNER JOIN order_detail b ON a.user_id = b.user_id
INNER JOIN product_info c ON b.product_id = c.product_id;
```

### 7. UNION 操作
```sql
-- UNION (去重)
SELECT user_id FROM table_a
UNION
SELECT user_id FROM table_b;

-- UNION ALL (不去重)
SELECT user_id FROM table_a
UNION ALL
SELECT user_id FROM table_b;
```

## 子查询

### 8. WHERE 子句中的子查询
```sql
-- IN 子查询
SELECT * FROM user_info
WHERE user_id IN (
    SELECT user_id FROM order_detail WHERE amount > 1000
);

-- 比较子查询
SELECT * FROM user_info
WHERE total_amount > (
    SELECT AVG(total_amount) FROM user_info
);
```

### 9. FROM 子句中的子查询
```sql
-- 派生表
SELECT category, avg_price
FROM (
    SELECT category, AVG(price) as avg_price
    FROM product_info
    GROUP BY category
) t
WHERE avg_price > 100;
```

## 日期函数

### 10. 日期处理
```sql
-- 当前日期
SELECT GETDATE() as current_time;

-- 日期格式化
SELECT TO_CHAR(created_date, 'yyyy-mm-dd') as date_str
FROM table_name;

-- 日期计算
SELECT DATE_SUB(GETDATE(), 7) as date_7_days_ago;
SELECT DATE_ADD(GETDATE(), 30) as date_30_days_later;

-- 日期差值
SELECT DATEDIFF(end_date, start_date) as days_diff
FROM table_name;

-- 提取日期部分
SELECT 
    TO_CHAR(created_date, 'yyyy') as year,
    TO_CHAR(created_date, 'mm') as month,
    TO_CHAR(created_date, 'dd') as day
FROM table_name;
```

## 分区表查询

### 11. 分区过滤
```sql
-- 指定分区查询 (减少扫描量)
SELECT * FROM table_name 
WHERE pt = '20260225';

-- 多分区查询
SELECT * FROM table_name 
WHERE pt >= '20260201' AND pt <= '20260225';

-- 分区聚合
SELECT pt, COUNT(*) as cnt
FROM table_name
WHERE pt >= '20260201'
GROUP BY pt
ORDER BY pt;
```

## 常用分析场景

### 12. 用户行为分析
```sql
-- 日活跃用户 (DAU)
SELECT 
    TO_CHAR(created_date, 'yyyy-mm-dd') as date,
    COUNT(DISTINCT user_id) as dau
FROM user_action
WHERE created_date >= DATE_SUB(GETDATE(), 30)
GROUP BY TO_CHAR(created_date, 'yyyy-mm-dd')
ORDER BY date;

-- 用户留存率
SELECT 
    TO_CHAR(a.register_date, 'yyyy-mm-dd') as register_date,
    COUNT(DISTINCT a.user_id) as register_users,
    COUNT(DISTINCT b.user_id) as retained_users,
    COUNT(DISTINCT b.user_id) * 100.0 / COUNT(DISTINCT a.user_id) as retention_rate
FROM user_info a
LEFT JOIN user_action b 
    ON a.user_id = b.user_id 
    AND TO_CHAR(b.created_date, 'yyyy-mm-dd') = TO_CHAR(DATE_ADD(a.register_date, 1), 'yyyy-mm-dd')
WHERE a.register_date >= '2026-01-01'
GROUP BY TO_CHAR(a.register_date, 'yyyy-mm-dd');
```

### 13. 销售分析
```sql
-- 每日销售额
SELECT 
    TO_CHAR(order_date, 'yyyy-mm-dd') as date,
    COUNT(*) as order_count,
    SUM(amount) as total_amount,
    AVG(amount) as avg_amount
FROM order_detail
WHERE order_date >= DATE_SUB(GETDATE(), 30)
GROUP BY TO_CHAR(order_date, 'yyyy-mm-dd')
ORDER BY date;

-- 商品销量排行
SELECT 
    product_id,
    product_name,
    SUM(quantity) as total_quantity,
    SUM(amount) as total_amount
FROM order_detail
WHERE order_date >= DATE_SUB(GETDATE(), 7)
GROUP BY product_id, product_name
ORDER BY total_amount DESC
LIMIT 20;
```

### 14. 漏斗分析
```sql
-- 用户转化漏斗
WITH funnel AS (
    SELECT 
        '1_visit' as stage,
        COUNT(DISTINCT user_id) as users
    FROM user_action WHERE action = 'visit'
    
    UNION ALL
    
    SELECT 
        '2_view_product',
        COUNT(DISTINCT user_id)
    FROM user_action WHERE action = 'view_product'
    
    UNION ALL
    
    SELECT 
        '3_add_cart',
        COUNT(DISTINCT user_id)
    FROM user_action WHERE action = 'add_cart'
    
    UNION ALL
    
    SELECT 
        '4_purchase',
        COUNT(DISTINCT user_id)
    FROM user_action WHERE action = 'purchase'
)
SELECT 
    stage,
    users,
    users * 100.0 / FIRST_VALUE(users) OVER () as conversion_rate
FROM funnel
ORDER BY stage;
```

## 性能优化建议

### 15. 查询优化
```sql
-- 1. 使用分区过滤 (减少扫描量)
SELECT * FROM table_name WHERE pt = '20260225';

-- 2. 只查询需要的列
SELECT user_id, name FROM user_info;  -- 而不是 SELECT *

-- 3. 提前过滤数据
SELECT * FROM (
    SELECT * FROM table_name WHERE pt >= '20260201'
) t WHERE amount > 1000;

-- 4. 使用 MAPJOIN 处理小表关联
SELECT /*+ MAPJOIN(b) */ a.*, b.category_name
FROM large_table a
JOIN small_dict b ON a.category_id = b.category_id;

-- 5. 避免数据倾斜
SELECT 
    COALESCE(user_id, 'default') as user_id,  -- 处理 NULL 值
    COUNT(*) as cnt
FROM table_name
GROUP BY COALESCE(user_id, 'default');
```

## 注意事项

1. **分区表必须指定分区**: 查询分区表时务必在 WHERE 中指定分区，否则全表扫描费用很高
2. **LIMIT 限制**: 建议始终使用 LIMIT 限制结果行数
3. **避免 SELECT ***: 只查询需要的列，减少数据传输
4. **JOIN 优化**: 大表 JOIN 大表容易 OOM，尽量使用 MAPJOIN 或预先聚合
5. **计费说明**: ODPS 按扫描数据量计费，优化查询可以节省费用
