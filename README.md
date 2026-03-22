# OpenClaw Skills 技能库

🤖 OpenClaw 专业技能集合 | 博彩分析 · 投资分析 · 数据查询 · 评论分析

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/hyz2023/openClaw_Skill.git
cd openClaw_Skill

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制技能到 OpenClaw 工作区
cp -r skills/<skill-name> /path/to/your/openclaw/workspace/skills/
```

---

## 📦 技能列表

| 技能 | 描述 | 主要依赖 |
|------|------|----------|
| [🎰 **betting-analytics**](#1-博彩数据分析工具) | 博彩数据趋势分析、异常检测、归因分析、下钻分析 | `pandas`, `scikit-learn`, `shap`, `pyodps` |
| [📈 **dividend-stock-analyzer**](#2-股息股分析工具) | A 股/美股股息股投资分析 | `yfinance`, `akshare`, `pandas` |
| [☁️ **aliyun-odps-query**](#3-阿里云-odps-查询工具) | 阿里云 MaxCompute 数据查询 | `pyodps`, `pandas`, `openpyxl` |
| [📱 **app-review-analyzer**](#4-应用评论分析工具) | 应用评论采集与情感分析 | `google-play-scraper`, `app-store-scraper` |

---

## 📚 详细说明

### 1. 博彩数据分析工具

**功能**: 赔率趋势追踪、异常投注检测、胜负归因分析、多维度下钻分析

#### 核心模块

| 模块 | 脚本 | 说明 |
|------|------|------|
| 趋势分析 | `trend_analyzer.py` | 赔率走势、移动平均线、RSI/MACD 动量指标、波动率 |
| 异常检测 | `anomaly_detector.py` | Z-Score / IQR / Isolation Forest / 多方法集成评分 |
| 归因分析 | `attribution_analyzer.py` | SHAP 特征重要性、Random Forest/XGBoost 因子分解 |
| 下钻分析 | `drill_down_analyzer.py` | 联赛→球队→球员→场次 多层级钻取 |

#### ODPS 数据集成

| 脚本 | 说明 |
|------|------|
| `odps_betting_analysis.py` | 从 ODPS 拉取博彩数据分析 |
| `odps_daily_analysis.py` | 每日数据自动化分析 |
| `odps_metadata_crawler.py` | 表元数据爬取与索引 |
| `odps_source_analysis.py` | 数据源类型分析 |
| `odps_ai_search.py` | AI 辅助语义搜索 |

```bash
# 趋势分析
python skills/betting-analytics/scripts/trend_analyzer.py \
  --data input.csv --type odds --window 30

# 异常检测
python skills/betting-analytics/scripts/anomaly_detector.py \
  --data input.csv --method isolation_forest --threshold 0.7

# 归因分析
python skills/betting-analytics/scripts/attribution_analyzer.py \
  --data input.csv --target outcome --method shap

# 下钻分析
python skills/betting-analytics/scripts/drill_down_analyzer.py \
  --data input.csv --dimensions league,team,market
```

📖 **完整文档**: [skills/betting-analytics/SKILL.md](skills/betting-analytics/SKILL.md)

---

### 2. 股息股分析工具

**功能**: 筛选高股息股票、基本面分析、分红确定性评估、目标价计算

```bash
# 筛选美股高股息股票
python skills/dividend-stock-analyzer/scripts/dividend_screener.py \
  --market us --min-yield 3 --years-stable 10

# 分析单只股票
python skills/dividend-stock-analyzer/scripts/fundamental_analyzer.py \
  --symbol KO --market us
```

📖 **完整文档**: [skills/dividend-stock-analyzer/SKILL.md](skills/dividend-stock-analyzer/SKILL.md)

---

### 3. 阿里云 ODPS 查询工具

**功能**: ODPS 表结构查看、SQL 查询执行、数据导出

```bash
# 配置环境变量
export ALIBABA_ACCESSKEY_ID="your_key"
export ALIBABA_ACCESSKEY_SECRET="your_secret"
export ALIBABA_ODPS_PROJECT="your_project"

# 查看表结构
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action describe --project my_project --table user_info

# 执行 SQL 查询
python skills/aliyun-odps-query/scripts/odps_query.py \
  --action query --project my_project \
  --sql "SELECT * FROM user_info WHERE pt = '20260225' LIMIT 10"
```

📖 **完整文档**: [skills/aliyun-odps-query/SKILL.md](skills/aliyun-odps-query/SKILL.md)

---

### 4. 应用评论分析工具

**功能**: App Store / Google Play 评论采集、情感分析、趋势报告

```bash
# 采集 Google Play 评论
python skills/app-review-analyzer/scripts/collect_reviews.py \
  --app "com.example.app" --platform google_play --count 1000

# 分析评论
python skills/app-review-analyzer/scripts/analyze_reviews.py \
  --input reviews.json --output analysis.md
```

📖 **完整文档**: [skills/app-review-analyzer/SKILL.md](skills/app-review-analyzer/SKILL.md)

---

## 🔧 部署指南

### 环境要求

- Python 3.8+
- pip 包管理器
- Git
- OpenClaw（[安装指南](https://docs.openclaw.ai)）

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/hyz2023/openClaw_Skill.git
cd openClaw_Skill

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制技能到 OpenClaw 工作区
# 复制全部
cp -r skills/* /path/to/your/openclaw/workspace/skills/

# 或复制单个
cp -r skills/betting-analytics /path/to/your/openclaw/workspace/skills/

# 4. 配置环境变量（ODPS 相关技能需要）
export ALIBABA_ACCESSKEY_ID="your_key"
export ALIBABA_ACCESSKEY_SECRET="your_secret"
export ALIBABA_ODPS_PROJECT="your_project"
```

---

## 📁 目录结构

```
openClaw_Skill/
├── README.md                       # 本说明文档
├── requirements.txt                # Python 依赖
├── .gitignore                      # Git 忽略规则
└── skills/                         # 技能源码
    ├── betting-analytics/          # 博彩数据分析
    │   ├── SKILL.md
    │   ├── scripts/                # 分析脚本
    │   └── references/             # 方法论文档
    ├── dividend-stock-analyzer/    # 股息股分析
    │   ├── SKILL.md
    │   └── scripts/
    ├── aliyun-odps-query/          # ODPS 查询
    │   ├── SKILL.md
    │   └── scripts/
    └── app-review-analyzer/        # 评论分析
        ├── SKILL.md
        └── scripts/
```

---

## 🔄 更新技能

```bash
cd openClaw_Skill
git pull origin main
cp -r skills/* /path/to/your/openclaw/workspace/skills/
```

---

## ⚠️ 注意事项

1. **数据安全** — 不要将 AccessKey / Token 提交到 Git
2. **ODPS 计费** — 查询时务必使用分区过滤，避免全表扫描产生高额费用
3. **API 限制** — 各平台有请求频率限制，建议添加适当延迟
4. **合规声明** — 博彩分析工具仅用于数据研究，不构成投注建议

---

## 📞 支持与反馈

- 📖 [OpenClaw 官方文档](https://docs.openclaw.ai)
- 🐛 [问题反馈](https://github.com/hyz2023/openClaw_Skill/issues)
- 💬 [OpenClaw 社区](https://discord.com/invite/clawd)

---

## 📝 许可证

MIT License © 2026 hyz2023
