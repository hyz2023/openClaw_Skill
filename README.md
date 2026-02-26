# OpenClaw Skills 技能库

🤖 OpenClaw 专业技能集合 | 投资分析 · 数据查询 · 评论分析

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/hyz2023/openClaw_Skill.git
cd OpenClaw_Skill

# 2. 安装依赖
pip install -r requirements.txt

# 3. 复制技能到 OpenClaw 工作区
cp -r skills/* /path/to/your/openclaw/workspace/skills/
```

---

## 📦 技能列表

| 技能 | 描述 | 安装 |
|------|------|------|
| [📈 **dividend-stock-analyzer**](#1-股息股分析工具) | A 股/美股股息股投资分析 | `pip install yfinance akshare pandas` |
| [☁️ **aliyun-odps-query**](#2-阿里云 odps-查询工具) | 阿里云 MaxCompute 数据查询 | `pip install pyodps pandas openpyxl` |
| [📱 **app-review-analyzer**](#3-应用评论分析工具) | 应用评论采集与分析 | `pip install google-play-scraper app-store-scraper` |

---

## 📚 详细说明

### 1. 股息股分析工具

**功能**: 筛选高股息股票、基本面分析、目标价计算

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

### 2. 阿里云 ODPS 查询工具

**功能**: ODPS 表结构查看、SQL 查询、数据导出

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

### 3. 应用评论分析工具

**功能**: App Store/Google Play 评论采集、情感分析

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

### 步骤 1: 克隆仓库
```bash
git clone https://github.com/hyz2023/openClaw_Skill.git
cd OpenClaw_Skill
```

### 步骤 2: 安装依赖
```bash
pip install -r requirements.txt
```

### 步骤 3: 复制技能到 OpenClaw
```bash
# 复制所有技能
cp -r skills/* /path/to/your/openclaw/workspace/skills/

# 或复制单个技能
cp -r skills/dividend-stock-analyzer /path/to/your/openclaw/workspace/skills/
```

### 步骤 4: 配置环境变量 (如需要)
```bash
# ODPS 配置
echo 'export ALIBABA_ACCESSKEY_ID="your_key"' >> ~/.bashrc
echo 'export ALIBABA_ACCESSKEY_SECRET="your_secret"' >> ~/.bashrc
echo 'export ALIBABA_ODPS_PROJECT="your_project"' >> ~/.bashrc
source ~/.bashrc
```

### 步骤 5: 验证安装
```bash
python skills/dividend-stock-analyzer/scripts/dividend_screener.py --help
```

---

## 📁 目录结构

```
OpenClaw_Skill/
├── README.md              # 本说明文档
├── requirements.txt       # Python 依赖
├── *.skill               # 打包的技能文件
└── skills/               # 技能源码
    ├── dividend-stock-analyzer/
    ├── aliyun-odps-query/
    └── app-review-analyzer/
```

---

## 🔄 更新技能

```bash
cd OpenClaw_Skill
git pull origin main
cp -r skills/* /path/to/your/openclaw/workspace/skills/
```

---

## ⚠️ 注意事项

1. **API 限制**: 各平台有请求频率限制，建议添加延迟
2. **数据安全**: 不要将 AccessKey/Token 提交到 Git
3. **ODPS 计费**: 查询时务必使用分区过滤，避免全表扫描

---

## 📞 支持与反馈

- 📖 [OpenClaw 官方文档](https://docs.openclaw.ai)
- 🐛 [问题反馈](https://github.com/hyz2023/openClaw_Skill/issues)
- 📧 联系：hyz2023

---

## 📝 许可证

MIT License © 2026 hyz2023

---

**🎉 享受使用 OpenClaw Skills!**
