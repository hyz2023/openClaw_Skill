# 股息股分析工具 - 使用指南

## 安装依赖

```bash
# A 股数据
pip install akshare pandas

# 美股数据
pip install yfinance pandas
```

## 快速使用

### 1. 筛选高股息股票

**美股筛选:**
```bash
python scripts/dividend_screener.py --market us --min-yield 3 --years-stable 10
```

**A 股筛选:**
```bash
python scripts/dividend_screener.py --market cn --min-yield 2.5 --years-stable 5
```

**参数说明:**
- `--market`: 市场类型 (us/cn)
- `--min-yield`: 最小股息率 (%)
- `--years-stable`: 最小连续分红年数
- `--max-payout`: 最大派息比率 (%)
- `--output`: 输出格式 (table/csv/json)

### 2. 分析单只股票基本面

**美股:**
```bash
python scripts/fundamental_analyzer.py --symbol KO --market us
```

**A 股:**
```bash
python scripts/fundamental_analyzer.py --symbol 601398 --market cn
```

**输出:** 生成详细的 Markdown 分析报告，包含股息指标、财务健康度、分红确定性评分

### 3. 计算目标价位

**美股:**
```bash
python scripts/target_price_calculator.py --symbol KO --market us --target-yield 4
```

**A 股:**
```bash
python scripts/target_price_calculator.py --symbol 601398 --market cn
```

**输出:** 综合多种估值方法，给出安全买入价位和建议

## 完整工作流程示例

### 示例 1: 寻找美股高股息股票

```bash
# 步骤 1: 筛选股息率>4%，连续分红>10 年的股票
python scripts/dividend_screener.py --market us --min-yield 4 --years-stable 10 --output csv

# 步骤 2: 对感兴趣的股票进行深入分析
python scripts/fundamental_analyzer.py --symbol KO --market us --output report.md

# 步骤 3: 计算合理买入价格
python scripts/target_price_calculator.py --symbol KO --market us --margin 0.15
```

### 示例 2: 分析 A 股银行股

```bash
# 步骤 1: 筛选银行股
python scripts/dividend_screener.py --market cn --min-yield 5 --years-stable 5 --symbols 601398,601288,601939

# 步骤 2: 分析工商银行
python scripts/fundamental_analyzer.py --symbol 601398 --market cn

# 步骤 3: 计算目标价
python scripts/target_price_calculator.py --symbol 601398 --market cn --target-yield 6
```

## 输出文件

- **CSV 输出**: 适合导入 Excel 进一步分析
- **JSON 输出**: 适合程序化处理
- **Markdown 报告**: 适合阅读和分享

## 评分说明

### 分红确定性评分 (0-100)

| 分数 | 评级 | 操作建议 |
|------|------|----------|
| 90-100 | 极高 | 核心持仓，重仓配置 |
| 75-89 | 高 | 重点配置，适量买入 |
| 60-74 | 中等 | 标准配置，观察买入 |
| 40-59 | 低 | 少量配置，谨慎 |
| <40 | 极低 | 避免或清仓 |

### 投资建议

- **强烈买入**: 当前价 < 安全价×0.8
- **买入**: 当前价 < 安全价
- **观望**: 接近合理价位，可分批建仓
- **持有**: 略高于合理价，持有观望
- **卖出/避免**: 价格显著高于合理价

## 注意事项

1. **数据延迟**: 免费 API 数据可能有 15 分钟延迟
2. **财报季节**: 财报发布后数据更准确
3. **分散投资**: 不要重仓单只股票
4. **定期复查**: 每季度重新评估持仓
5. **风险提示**: 工具仅供参考，不构成投资建议

## 常见问题

**Q: 为什么某些股票获取不到数据？**
A: 可能是数据源限制或股票代码错误，请检查代码格式

**Q: A 股和美股筛选标准为什么不同？**
A: 两个市场分红政策和投资者结构不同，A 股整体分红率较低

**Q: 如何自定义筛选条件？**
A: 修改脚本中的默认参数，或直接传递命令行参数

## 技能包

已打包为 `.skill` 文件，可在 OpenClaw 中安装使用:
```
dividend-stock-analyzer.skill
```
