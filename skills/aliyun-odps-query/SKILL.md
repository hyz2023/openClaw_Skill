---
name: aliyun-odps-query
description: "阿里云 ODPS/MaxCompute 数据查询工具。通过 AccessKey 连接 ODPS，读取表结构/元数据，执行 SQL 查询并返回结果。Use for: ODPS table metadata query, SQL execution, data analysis on Alibaba Cloud MaxCompute"
---

# 阿里云 ODPS 查询工具 (Aliyun ODPS Query)

## 快速开始

```bash
# 查看表结构
python scripts/odps_query.py --action describe --project my_project --table user_info

# 列出所有表
python scripts/odps_query.py --action list --project my_project

# 执行 SQL 查询
python scripts/odps_query.py --action query --project my_project --sql "SELECT * FROM user_info LIMIT 10"

# 导出查询结果
python scripts/odps_query.py --action query --project my_project --sql "SELECT count(*) FROM orders" --output csv
```

## 核心功能

### 1. 表元数据查询 (Table Metadata)
- 查看表结构 (字段名、类型、注释)
- 查看分区信息
- 查看表大小、创建时间、最后修改时间
- 查看生命周期设置

### 2. SQL 查询执行 (SQL Execution)
- 支持 SELECT 查询
- 支持聚合统计
- 支持多表 JOIN
- 支持子查询
- 支持 UDF (用户自定义函数)

### 3. 结果导出 (Result Export)
- CSV 格式导出
- JSON 格式导出
- Excel 格式导出
- 直接打印到终端

## 环境配置

### 方式 1: 环境变量 (推荐)
```bash
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
```

### 方式 2: 配置文件
创建 `~/.odps_config.ini`:
```ini
[odps]
access_id = your_access_key_id
access_key = your_access_key_secret
endpoint = http://service.odps.aliyun.com/api
project = your_project_name
```

### 方式 3: 命令行参数
```bash
python scripts/odps_query.py --access-id XXX --access-key XXX --project XXX --action list
```

## 使用示例

### 示例 1: 查看项目中的所有表
```bash
python scripts/odps_query.py --action list --project my_project
```

输出:
```
📊 项目：my_project
找到 15 张表

user_info          用户信息表          2024-01-15
order_detail       订单详情表          2024-02-20
product_catalog    商品目录表          2024-01-10
...
```

### 示例 2: 查看表结构
```bash
python scripts/odps_query.py --action describe --project my_project --table user_info
```

输出:
```
📋 表结构：my_project.user_info

字段名              类型                  注释
user_id            BIGINT               用户 ID
user_name          STRING               用户姓名
email              STRING               邮箱地址
register_date      DATETIME             注册日期
status             INT                  状态 (1 正常/0 禁用)
```

### 示例 3: 执行查询
```bash
python scripts/odps_query.py --action query --project my_project \
  --sql "SELECT user_id, user_name FROM user_info WHERE status = 1 LIMIT 10"
```

### 示例 4: 导出查询结果
```bash
python scripts/odps_query.py --action query --project my_project \
  --sql "SELECT * FROM order_detail WHERE dt >= '20260201'" \
  --output csv --output-file orders_feb.csv
```

## 参数说明

### 必需参数
| 参数 | 说明 | 示例 |
|------|------|------|
| `--action` | 操作类型 | list/describe/query |
| `--project` | ODPS 项目名称 | my_project |

### 可选参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--table` | 表名 (describe 需要) | - |
| `--sql` | SQL 语句 (query 需要) | - |
| `--limit` | 结果行数限制 | 100 |
| `--output` | 输出格式 | table |
| `--output-file` | 输出文件路径 | - |
| `--access-id` | AccessKey ID (覆盖环境变量) | - |
| `--access-key` | AccessKey Secret (覆盖环境变量) | - |
| `--endpoint` | ODPS Endpoint (覆盖环境变量) | - |

## 输出格式

### table (默认)
表格格式，适合终端查看

### csv
逗号分隔值，适合导入 Excel

### json
JSON 格式，适合程序处理

### excel
Excel 文件 (.xlsx)

## 注意事项

1. **权限要求**: AccessKey 需要有对应项目的读取权限
2. **SQL 限制**: 仅支持 SELECT 查询，不支持 DDL/DML
3. **结果限制**: 默认限制 1000 行，避免大量数据传输
4. **计费**: ODPS SQL 查询按扫描数据量计费
5. **超时**: 复杂查询可能超时，建议添加 LIMIT

## 相关文件

- [odps-api-reference.md](references/odps-api-reference.md) - ODPS API 参考
- [sql-examples.md](references/sql-examples.md) - 常用 SQL 示例
- [troubleshooting.md](references/troubleshooting.md) - 常见问题解决

## 依赖安装

```bash
pip install odps pandas openpyxl
```

或

```bash
pip install pyodps pandas openpyxl
```
