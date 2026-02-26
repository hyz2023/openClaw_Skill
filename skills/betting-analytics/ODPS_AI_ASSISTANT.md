# ODPS 数据助手 - AI 检索工具

## 🎯 功能

1. **元数据采集**: 自动下载 ODPS 所有表结构、字段、注释
2. **AI 检索**: 根据自然语言查询，推荐相关的表和字段
3. **SQL 生成**: 自动生成查询建议

## 📦 组件

```
skills/betting-analytics/scripts/
├── odps_assistant.py         # 统一入口
├── odps_metadata_crawler.py  # 元数据采集
└── odps_ai_search.py         # AI 检索引擎
```

## 🚀 使用方法

### 1. 采集元数据

```bash
cd /home/ubuntu/.openclaw/workspace
source venv/bin/activate

# 设置环境变量
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"

# 采集元数据 (可能需要几分钟)
python skills/betting-analytics/scripts/odps_assistant.py crawl
```

输出:
- `odps_metadata/metadata_latest.json` - 完整元数据
- `odps_metadata/columns_latest.csv` - 字段清单
- `odps_metadata/summary_*.json` - 统计摘要

### 2. AI 检索

```bash
# 单次查询
python skills/betting-analytics/scripts/odps_assistant.py search \
  -q "查询用户投注数据"

# 交互模式
python skills/betting-analytics/scripts/odps_assistant.py search -i

# 演示模式
python skills/betting-analytics/scripts/odps_assistant.py demo
```

### 3. 示例查询

```
📝 查询：用户投注数据
📊 匹配的表:
1. t_order_all (匹配度：2.8)
   - login_name (STRING) [用户登录名]
   - bet_amount (STRING) [投注金额]
   - ordersourcetype (STRING) [订单来源]

💡 推荐 SQL:
SELECT login_name, bet_amount, ordersourcetype
FROM t_order_all
WHERE pt >= DATE_SUB(GETDATE(), 7)
LIMIT 1000;
```

## 🔍 检索原理

1. **关键词提取**: 从查询中提取中英文关键词
2. **字段名匹配**: 直接匹配字段名 (如 user, bet, amount)
3. **注释匹配**: 匹配表和字段的注释
4. **业务词汇映射**: 自动关联业务术语
   - "用户" → user, login, customer
   - "投注" → bet, wager, order
   - "金额" → amount, money, sum

## 📊 输出示例

### 元数据 JSON 结构
```json
{
  "table_name": "t_order_all",
  "comment": "投注订单表",
  "columns": [
    {
      "name": "login_name",
      "type": "STRING",
      "comment": "用户登录名"
    },
    {
      "name": "bet_amount",
      "type": "STRING",
      "comment": "投注金额"
    }
  ],
  "partitions": [
    {
      "name": "pt",
      "type": "STRING",
      "comment": "分区日期"
    }
  ]
}
```

### AI 检索结果
```json
{
  "query": "查询用户投注金额",
  "keywords": ["user", "bet", "amount", "用户", "投注", "金额"],
  "matched_tables": [
    {
      "table": "t_order_all",
      "score": 3.5,
      "columns": [
        {"name": "login_name", "match_type": "field_name"},
        {"name": "bet_amount", "match_type": "field_name"}
      ]
    }
  ]
}
```

## 💡 使用场景

### 场景 1: 新手探索数据
```
📝 "有哪些表包含用户信息？"
→ 推荐：t_order_all, t_user_info, t_customer
```

### 场景 2: 编写查询 SQL
```
📝 "统计每天的投注总额"
→ 推荐表：t_order_all
→ 推荐字段：pt, bet_amount
→ 生成 SQL: SELECT pt, SUM(bet_amount) FROM ...
```

### 场景 3: 数据字典查询
```
📝 "订单表有哪些字段？"
→ 列出 t_order_all 所有字段及说明
```

## ⚙️ 配置

### 环境变量
```bash
export ALIBABA_ACCESSKEY_ID="..."
export ALIBABA_ACCESSKEY_SECRET="..."
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"
```

### 元数据目录
默认：`odps_metadata/`
可通过 `--metadata-dir` 参数修改

## 📝 注意事项

1. **首次使用**: 必须先运行 `crawl` 采集元数据
2. **元数据更新**: 表结构变化后需重新采集
3. **超时处理**: 表很多时采集可能超时，可分批采集
4. **权限要求**: 需要 ODPS 读权限

## 🔧 故障排除

### 问题：找不到元数据文件
```
❌ FileNotFoundError: 未找到元数据文件
```
**解决**: 先运行 `python odps_assistant.py crawl`

### 问题：采集超时
```
❌ Command timed out
```
**解决**: 
- 增加超时时间 `timeout 300 python ...`
- 或只采集部分表 (修改脚本添加表名过滤)

### 问题：匹配结果不准确
**解决**:
- 检查字段注释是否完整
- 添加更多业务词汇映射 (修改 `_extract_keywords`)

## 📚 相关文件

- [ODPS 分析报告](../../reports/betting_odps_analysis_30d/)
- [元数据说明](../../odps_metadata/README.md)
