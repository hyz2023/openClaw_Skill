---
name: betting-analytics
description: 博彩数据分析工具，提供趋势分析、异常点检测、归因分析、下钻分析。Use for: betting data trend analysis, anomaly detection, attribution analysis, drill-down analysis, odds movement tracking, betting pattern recognition
---

# 博彩数据分析工具 (Betting Analytics)

## 快速开始

```bash
# 趋势分析 - 分析赔率/数据走势
python scripts/trend_analyzer.py --data input.csv --type odds --window 30

# 异常点检测 - 识别异常投注模式
python scripts/anomaly_detector.py --data input.csv --method isolation_forest

# 归因分析 - 分析影响结果的关键因素
python scripts/attribution_analyzer.py --data input.csv --target outcome

# 下钻分析 - 多维度深入分析
python scripts/drill_down_analyzer.py --data input.csv --dimensions league,team,market
```

## 核心功能

### 1. 趋势分析 (Trend Analysis)
- 赔率走势追踪与可视化
- 投注量变化趋势
- 市场情绪指标
- 移动平均线与趋势线
- 支撑位/阻力位识别

### 2. 异常点检测 (Anomaly Detection)
- 异常赔率波动识别
- 可疑投注模式检测
- 离群值统计分析
- 时间序列异常点
- 多维度异常评分

### 3. 归因分析 (Attribution Analysis)
- 胜负结果因素分解
- 赔率变化归因
- 投注量影响分析
- SHAP 值特征重要性
- 贡献度量化

### 4. 下钻分析 (Drill-Down Analysis)
- 多维度数据下钻
- 联赛/球队/球员层级分析
- 时间粒度下钻 (月→周→日→场次)
- 盘口类型细分
- 对比分析

## 使用流程

1. **数据准备** → 准备 CSV/JSON 格式的博彩数据
2. **趋势分析** → 识别整体走势和市场方向
3. **异常检测** → 标记异常数据点供进一步调查
4. **归因分析** → 理解影响结果的关键因素
5. **下钻分析** → 深入特定维度获取细节洞察
6. **生成报告** → 综合所有分析生成分析报告

## 数据格式要求

详见 [references/data-format.md](references/data-format.md)

### 标准输入格式 (CSV)
```csv
match_id,league,home_team,away_team,match_time,market_type,odds_home,odds_draw,odds_away,bet_volume,outcome
1001,Premier League,Arsenal,Chelsea,2024-01-15 15:00,1X2,2.10,3.40,3.50,150000,1
1002,La Barca,Real Madrid,Barcelona,2024-01-15 20:00,1X2,2.50,3.20,2.80,280000,2
```

### 必填字段
| 字段 | 说明 | 类型 |
|------|------|------|
| match_id | 比赛唯一标识 | string/int |
| match_time | 比赛时间 | datetime |
| market_type | 盘口类型 (1X2, OU, AH 等) | string |
| odds_* | 赔率数据 | float |
| outcome | 比赛结果 | int/string |

### 可选字段
- league: 联赛名称
- home_team/away_team: 球队名称
- bet_volume: 投注量
- odds_history: 赔率历史 (JSON)

## 分析方法详解

### 趋势分析
详见 [references/trend-methods.md](references/trend-methods.md)

- **移动平均**: MA5, MA10, MA20, MA60
- **趋势线**: 线性回归拟合
- **动量指标**: RSI, MACD 适配
- **波动率**: 标准差、ATR

### 异常检测
详见 [references/anomaly-methods.md](references/anomaly-methods.md)

- **统计方法**: Z-Score, IQR
- **机器学习**: Isolation Forest, One-Class SVM
- **时间序列**: STL 分解残差
- **集成评分**: 多方法加权

### 归因分析
详见 [references/attribution-methods.md](references/attribution-methods.md)

- **特征重要性**: Random Forest, XGBoost
- **SHAP 值**: 局部和全局解释
- **贡献分解**: 加法/乘法分解
- **因果推断**: Granger 因果检验

### 下钻分析
详见 [references/drill-down-guide.md](references/drill-down-guide.md)

- **维度层级**: 定义维度树结构
- **聚合规则**: SUM, AVG, COUNT 等
- **对比基准**: 环比、同比、 vs 平均
- **可视化**: 旭日图、树状图

## 输出示例

```markdown
## 📊 博彩数据分析报告

### 趋势分析摘要
| 指标 | 数值 | 趋势 |
|------|------|------|
| 平均赔率变化 | -2.3% | 📉 下降 |
| 投注量趋势 | +15% | 📈 上升 |
| 市场波动率 | 0.08 | ⚠️ 中等 |

### 异常点检测
发现 3 个异常记录:
- Match #1042: 赔率异常波动 (Z-Score: 3.2)
- Match #1087: 投注量异常 (Isolation Forest 评分：0.89)
- Match #1103: 结果与赔率严重偏离

### 归因分析 (胜负预测)
Top 5 影响因素:
1. 主队近期胜率 (SHAP: 0.23)
2. 历史交锋记录 (SHAP: 0.18)
3. 赔率初始值 (SHAP: 0.15)
4. 投注量分布 (SHAP: 0.12)
5. 联赛排名差 (SHAP: 0.09)

### 下钻分析 (按联赛)
| 联赛 | 场次 | 平均赔率 | 异常率 |
|------|------|----------|--------|
| Premier League | 45 | 2.45 | 2.2% |
| La Liga | 38 | 2.52 | 3.1% |
| Bundesliga | 32 | 2.38 | 1.8% |
```

## 脚本说明

### trend_analyzer.py
```bash
python scripts/trend_analyzer.py \
  --data input.csv \
  --type odds \          # odds/volume/volatility
  --window 30 \          # 分析窗口 (天)
  --output report.html
```

### anomaly_detector.py
```bash
python scripts/anomaly_detector.py \
  --data input.csv \
  --method isolation_forest \  # zscore/iqr/isolation_forest/ensemble
  --threshold 0.7 \
  --output anomalies.csv
```

### attribution_analyzer.py
```bash
python scripts/attribution_analyzer.py \
  --data input.csv \
  --target outcome \
  --method shap \
  --output attribution_report.html
```

### drill_down_analyzer.py
```bash
python scripts/drill_down_analyzer.py \
  --data input.csv \
  --dimensions league,team,market \
  --metrics odds,volume \
  --output drilldown_report.html
```

## 可视化输出

支持以下图表类型:
- 📈 趋势线图 (赔率/投注量随时间变化)
- 📊 柱状图 (维度对比)
- 🔥 热力图 (异常点分布)
- 🎯 散点图 (归因分析)
- 🌳 旭日图 (下钻层级)
- 📉 箱线图 (分布与离群值)

## 注意事项

1. **数据质量** - 确保数据完整性和准确性，异常检测对噪声敏感
2. **合规性** - 本工具仅用于数据分析和研究，不构成投注建议
3. **样本量** - 归因分析需要足够样本量 (建议≥100 条记录)
4. **过拟合风险** - 机器学习模型需交叉验证
5. **时效性** - 博彩数据变化快，分析结果需及时更新

## 扩展功能

- **实时分析**: 接入实时数据流进行在线分析
- **预警系统**: 异常点自动告警
- **模型训练**: 基于历史数据训练预测模型
- **API 服务**: 提供 RESTful API 供其他系统调用

## 相关文件

- [data-format.md](references/data-format.md) - 数据格式详解
- [trend-methods.md](references/trend-methods.md) - 趋势分析方法
- [anomaly-methods.md](references/anomaly-methods.md) - 异常检测方法
- [attribution-methods.md](references/attribution-methods.md) - 归因分析方法
- [drill-down-guide.md](references/drill-down-guide.md) - 下钻分析指南
- [api-reference.md](references/api-reference.md) - Python API 参考
