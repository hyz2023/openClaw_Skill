# OpenClaw Skills 技能库

🤖 为 OpenClaw 框架开发的专业技能集合，提供投资分析、数据查询、用户评论分析等功能。

---

## 📦 技能列表

| 技能 | 描述 | 适用场景 | 状态 |
|------|------|----------|------|
| [**dividend-stock-analyzer**](#1-dividend-stock-analyzer-股息股分析工具) | A 股/美股股息股投资分析 | 筛选高股息股票、基本面分析、目标价计算 | ✅ 完成 |
| [**aliyun-odps-query**](#2-aliyun-odps-query-阿里云 odps-查询工具) | 阿里云 MaxCompute 数据查询 | ODPS 表结构查看、SQL 查询执行、数据导出 | ✅ 完成 |
| [**app-review-analyzer**](#3-app-review-analyzer-应用评论分析工具) | 移动应用评论采集分析 | App Store/Google Play 评论收集、情感分析 | ✅ 完成 |

---

## 🚀 快速开始

### 方式一：克隆整个技能库 (推荐)

```bash
# 1. 克隆仓库
git clone https://github.com/hyz2023/openClaw_Skill.git
cd OpenClaw_Skill

# 2. 将技能复制到 OpenClaw 工作区
cp -r skills/* /path/to/your/openclaw/workspace/skills/

# 3. 安装依赖
pip install -r requirements.txt
```

### 方式二：单独下载某个技能

```bash
# 下载单个技能 (以 dividend-stock-analyzer 为例)
git clone --depth 1 --filter=blob:none --sparse https://github.com/hyz2023/openClaw_Skill.git
cd OpenClaw_Skill
git sparse-checkout set skills/dividend-stock-analyzer

# 复制到 OpenClaw 工作区
cp -r skills/dividend-stock-analyzer /path/to/your/openclaw/workspace/skills/
```

### 方式三：使用 .skill 包 (如果 OpenClaw 支持)

仓库中包含打包好的 `.skill` 文件，可直接安装：
- `dividend-stock-analyzer.skill`
- `aliyun-odps-query.skill`
- `app-review-analyzer-v2.1.zip`

---

## 📚 技能详细说明

### 1. **dividend-stock-analyzer** - 股息股分析工具

📈 **A 股/美股股息股投资分析工具**

#### 功能特性
- ✅ 筛选连续多年稳定分红的高股息股票
- ✅ 基本面分析 (财务健康度、ROE、负债率等)
- ✅ 分红确定性评分 (0-100 分)
- ✅ 目标价位计算 (股息率/DCF/历史估值)
- ✅ 安全边际建议

#### 安装依赖
```bash
pip install yfinance akshare pandas
```

#### 使用示例

**筛选美股高股息股票:**
```bash
python skills/dividend-stock-analyzer/scripts/dividend_screener.py \
  --market us --min-yield 3 --years-stable 10
```

**筛选 A 股高股息股票:**
```bash
python skills/dividend-stock-analyzer/scripts/dividend_screener.py \
  --market cn --min-yield 4 --years-stable 5
```

**分析单只股票基本面:**
```bash
python skills/dividend-stock-analyzer/scripts/fundamental_analyzer.py \
  --symbol KO --market us
```

**计算目标价位:**
```bash
python skills/dividend-stock-analyzer/scripts/target_price_calculator.py \
  --symbol 601088 --market cn --target-yield 6
```

#### 输出示例
```markdown
## 📊 股票分析：可口可乐 (KO)

### 核心指标
| 指标 | 数值 | 评级 |
|------|------|------|
| 当前股价 | $62.50 | - |
| 股息率 | 3.2% | ✅ |
| 连续分红 | 61 年 | ✅✅✅ |
| 派息比率 | 68% | ⚠️ |

### 分红确定性：85/100 (高)
### 目标买入价：$58.00 (安全边际 7%)
```

#### 相关文件
- [SKILL.md](skills/dividend-stock-analyzer/SKILL.md) - 技能说明
- [USAGE.md](skills/dividend-stock-analyzer/USAGE.md) - 使用指南
- [dividend-metrics.md](skills/dividend-stock-analyzer/references/dividend-metrics.md) - 指标详解

---

### 2. **aliyun-odps-query** - 阿里云 ODPS 查询工具

☁️ **阿里云 MaxCompute (ODPS) 数据查询工具**

#### 功能特性
- ✅ 列出项目中的所有表
- ✅ 查看表结构/元数据 (字段、分区、大小)
- ✅ 执行 SQL 查询 (仅 SELECT)
- ✅ 导出查询结果 (CSV/JSON/Excel)
- ✅ 支持分区过滤 (节省费用)

#### 安装依赖
```bash
pip install pyodps pandas openpyxl
```

#### 环境配置

**方式 1: 环境变量 (推荐)**
```bash
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service-ap-southeast-1.maxcompute.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
```

**方式 2: 命令行参数**
```bash
python scripts/odps_query.py --access-id XXX --access-key XXX --project XXX
```

#### 使用示例

**列出所有表:**
```bash
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action list --project my_project
```

**查看表结构:**
```bash
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action describe --project my_project --table user_info
```

**执行 SQL 查询:**
```bash
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action query --project my_project \
  --sql "SELECT * FROM user_info WHERE pt = '20260225' LIMIT 10"
```

**导出查询结果:**
```bash
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action query --project my_project \
  --sql "SELECT count(*) FROM orders WHERE pt = '20260225'" \
  --output csv --output-file orders.csv
```

#### 输出示例
```
📋 表结构：my_project.user_info

字段 (10 列):
--------------------------------------------------------------------------------
字段名                              类型                   注释                            
--------------------------------------------------------------------------------
user_id                             STRING               用户 ID                          
user_name                           STRING               用户姓名                        
register_date                       DATETIME             注册日期                        
...
```

#### 常用 SQL 示例
详见：[sql-examples.md](skills/aliyun-odps-query/references/sql-examples.md)

```sql
-- 分区过滤查询 (节省费用)
SELECT * FROM table_name WHERE pt = '20260225';

-- 聚合统计
SELECT category, COUNT(*) as cnt 
FROM table_name 
WHERE pt >= '20260201' 
GROUP BY category;

-- 多表关联
SELECT a.user_id, a.name, b.order_id 
FROM user_info a 
JOIN order_detail b ON a.user_id = b.user_id 
WHERE a.pt = '20260225';
```

#### 注意事项
⚠️ **ODPS 按扫描数据量计费**，查询时务必：
1. 使用分区过滤 (`WHERE pt = 'YYYYMMDD'`)
2. 添加 LIMIT 限制结果行数
3. 只查询需要的列，避免 `SELECT *`

---

### 3. **app-review-analyzer** - 应用评论分析工具

📱 **移动应用评论采集与分析工具**

#### 功能特性
- ✅ 采集 Apple App Store 评论
- ✅ 采集 Google Play Store 评论
- ✅ 采集 Trustpilot 等平台评论
- ✅ 情感分析 (正面/负面/中性)
- ✅ 评分统计、关键词提取
- ✅ 生成分析报告

#### 安装依赖
```bash
pip install google-play-scraper app-store-scraper pandas textblob
```

#### 使用示例

**采集 Google Play 评论:**
```bash
python skills/app-review-analyzer/scripts/collect_reviews.py \
  --app "com.playtime.entertainment" \
  --platform google_play \
  --count 1000 \
  --output playtime_reviews.json
```

**采集 App Store 评论:**
```bash
python skills/app-review-analyzer/scripts/collect_reviews.py \
  --app "playtime-entertainment" \
  --platform app_store \
  --country ph \
  --count 500
```

**分析评论:**
```bash
python skills/app-review-analyzer/scripts/analyze_reviews.py \
  --input playtime_reviews.json \
  --output playtime_analysis.md \
  --language en
```

#### 输出示例
```markdown
# 📊 应用评论分析报告：PlayTime Entertainment

## 总体评分
- 平均分：4.2/5.0 ⭐⭐⭐⭐
- 总评论数：1,234 条
- 情感分布：正面 65% | 中性 20% | 负面 15%

## 关键词云
🎮 游戏 | 💰 奖励 | 🎁 活动 | 📱 界面 | ⚡ 流畅

## 用户反馈 Top 5
1. ✅ "游戏很有趣，奖励丰富"
2. ✅ "界面设计精美，操作简单"
3. ⚠️ "希望能增加更多活动"
4. ❌ "偶尔会闪退"
5. ❌ "客服响应慢"
```

#### 支持的平台
| 平台 | 参数 | 支持国家 |
|------|------|----------|
| Google Play | `google_play` | 全球 |
| Apple App Store | `app_store` | 全球 |
| Trustpilot | `trustpilot` | 部分国家 |

---

## 🔧 通用配置

### Python 环境要求
- Python 3.8+
- pip 包管理器

### 安装所有依赖
```bash
# 方式 1: 使用 requirements.txt
pip install -r requirements.txt

# 方式 2: 手动安装
pip install yfinance akshare pandas pyodps openpyxl
pip install google-play-scraper app-store-scraper textblob
```

### 验证安装
```bash
# 测试股息股分析工具
python skills/dividend-stock-analyzer/scripts/dividend_screener.py --help

# 测试 ODPS 查询工具
python skills/aliyun-odps-query/scripts/odps_query.py --help

# 测试评论分析工具
python skills/app-review-analyzer/scripts/collect_reviews.py --help
```

---

## 📁 目录结构

```
OpenClaw_Skill/
├── README.md                           # 本说明文档
├── requirements.txt                    # Python 依赖
├── skills/                             # 技能目录
│   ├── dividend-stock-analyzer/        # 股息股分析工具
│   │   ├── SKILL.md
│   │   ├── USAGE.md
│   │   ├── references/
│   │   └── scripts/
│   ├── aliyun-odps-query/              # ODPS 查询工具
│   │   ├── SKILL.md
│   │   ├── README.md
│   │   ├── references/
│   │   └── scripts/
│   └── app-review-analyzer/            # 评论分析工具
│       ├── SKILL.md
│       └── scripts/
├── dividend-stock-analyzer.skill       # 打包文件
└── aliyun-odps-query.skill             # 打包文件
```

---

## 🔄 更新技能

### 拉取最新技能
```bash
cd OpenClaw_Skill
git pull origin main

# 复制到 OpenClaw 工作区
cp -r skills/* /path/to/your/openclaw/workspace/skills/
```

### 贡献新技能
1. Fork 本仓库
2. 创建新分支：`git checkout -b feature/new-skill`
3. 添加技能到 `skills/` 目录
4. 提交：`git commit -m "Add new-skill"`
5. 推送：`git push origin feature/new-skill`
6. 提交 Pull Request

---

## ⚠️ 注意事项

### 1. API 限制
- **Yahoo Finance**: 非正式限制 ~2000 次/天
- **阿里云 ODPS**: 按扫描数据量计费
- **App Store/Google Play**: 建议添加请求延迟

### 2. 数据安全
- ⚠️ **不要** 将 AccessKey/Token 提交到 Git
- ✅ 使用环境变量或配置文件
- ✅ 在 `.gitignore` 中排除敏感文件

### 3. 许可证
本仓库技能遵循 MIT 许可证，可自由使用和修改。

---

## 📞 问题反馈

遇到问题或有建议？

1. 查看 [Issues](https://github.com/hyz2023/openClaw_Skill/issues)
2. 提交新 Issue
3. 联系作者：hyz2023

---

## 📝 更新日志

### v1.0.0 (2026-02-26)
- ✅ 初始版本发布
- ✅ dividend-stock-analyzer v1.0
- ✅ aliyun-odps-query v1.0
- ✅ app-review-analyzer v2.1

---

## 🔗 相关链接

- [OpenClaw 官方文档](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [技能市场](https://clawhub.com)

---

**🎉 享受使用 OpenClaw Skills!**
