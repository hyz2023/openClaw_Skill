# 数据格式规范 (Data Format Specification)

本文档定义博彩数据分析工具支持的数据格式和字段规范。

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| CSV | `.csv` | 逗号分隔值，推荐用于表格数据 |
| JSON | `.json` | JSON 数组格式，支持嵌套结构 |
| Excel | `.xlsx` | Excel 工作表 (需安装 openpyxl) |

## 标准数据模型

### 比赛/赛事数据 (Match Data)

```csv
match_id,league,season,match_date,home_team,away_team,home_score,away_score,status
1001,Premier League,2024-25,2024-01-15 15:00,Arsenal,Chelsea,2,1,FT
1002,La Liga,2024-25,2024-01-15 20:00,Real Madrid,Barcelona,1,1,FT
```

**必填字段:**
- `match_id`: 比赛唯一标识 (string/int)
- `match_date`: 比赛时间 (datetime)
- `home_team`: 主队名称 (string)
- `away_team`: 客队名称 (string)

**可选字段:**
- `league`: 联赛名称 (string)
- `season`: 赛季 (string)
- `home_score`: 主队得分 (int)
- `away_score`: 客队得分 (int)
- `status`: 比赛状态 (FT/HT/POSTPONED 等)

### 赔率数据 (Odds Data)

```csv
match_id,bookmaker,market_type,odds_home,odds_draw,odds_away,timestamp
1001,Bet365,1X2,2.10,3.40,3.50,2024-01-14 10:00:00
1001,Bet365,1X2,2.05,3.50,3.60,2024-01-15 14:00:00
```

**必填字段:**
- `match_id`: 比赛 ID (string/int)
- `market_type`: 盘口类型 (1X2/OU/AH 等)
- 至少一个赔率字段 (`odds_home`/`odds_away`/`odds_over`等)

**可选字段:**
- `bookmaker`: 博彩公司名称 (string)
- `timestamp`: 赔率时间戳 (datetime)
- `odds_draw`: 平局赔率 (float)

### 投注量数据 (Bet Volume Data)

```csv
match_id,market_type,bet_type,volume_home,volume_draw,volume_away,total_volume,timestamp
1001,1X2,Match Winner,150000,45000,80000,275000,2024-01-15 14:00:00
```

**必填字段:**
- `match_id`: 比赛 ID
- `market_type`: 盘口类型
- 至少一个投注量字段

**可选字段:**
- `bet_type`: 投注类型
- `timestamp`: 时间戳

### 综合数据 (Combined Data)

```csv
match_id,league,match_date,home_team,away_team,market_type,odds_home,odds_draw,odds_away,bet_volume,outcome
1001,Premier League,2024-01-15 15:00,Arsenal,Chelsea,1X2,2.10,3.40,3.50,275000,1
1002,La Liga,2024-01-15 20:00,Real Madrid,Barcelona,1X2,2.50,3.20,2.80,420000,2
```

## 盘口类型说明

### 1X2 (胜平负)
| 值 | 说明 |
|----|------|
| 1 | 主胜 |
| X | 平局 |
| 2 | 客胜 |

### OU (大小球)
| 值 | 说明 |
|----|------|
| Over | 大球 |
| Under | 小球 |

字段：`odds_over`, `odds_under`, `handicap`(让球数)

### AH (亚盘/让球)
| 值 | 说明 |
|----|------|
| Home | 上盘 (主队) |
| Away | 下盘 (客队) |

字段：`odds_home`, `odds_away`, `handicap`(让球数)

## 结果字段编码

### outcome 字段
| 值 | 1X2 含义 | 说明 |
|----|---------|------|
| 1 | 1 | 主胜 |
| 0/X | X | 平局 |
| 2 | 2 | 客胜 |

### 胜负编码
```python
# 足球
outcome = 1 if home_score > away_score else (0 if home_score == away_score else 2)

# 篮球 (无平局)
outcome = 1 if home_score > away_score else 2
```

## 数据质量要求

### 完整性
- 必填字段缺失率 < 5%
- 关键时间字段必须有值
- ID 字段必须唯一

### 准确性
- 赔率值 > 1.0
- 投注量 >= 0
- 比分 >= 0

### 一致性
- 时间格式统一 (ISO 8601 推荐)
- 队伍名称标准化
- 联赛名称统一

## 数据预处理建议

### 时间列处理
```python
df['match_date'] = pd.to_datetime(df['match_date'])
df['year'] = df['match_date'].dt.year
df['month'] = df['match_date'].dt.month
df['day'] = df['match_date'].dt.day
```

### 分类变量编码
```python
from sklearn.preprocessing import LabelEncoder

le = LabelEncoder()
df['league_encoded'] = le.fit_transform(df['league'])
df['home_team_encoded'] = le.fit_transform(df['home_team'])
```

### 缺失值处理
```python
# 数值列：用中位数填充
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

# 分类列：用众数填充
category_cols = df.select_dtypes(include=['object']).columns
df[category_cols] = df[category_cols].fillna(df[category_cols].mode().iloc[0])
```

## 示例数据生成

```python
import pandas as pd
import numpy as np

# 生成示例数据
np.random.seed(42)
n_matches = 1000

data = {
    'match_id': range(1, n_matches + 1),
    'league': np.random.choice(['Premier League', 'La Liga', 'Bundesliga'], n_matches),
    'match_date': pd.date_range('2024-01-01', periods=n_matches, freq='H'),
    'home_team': np.random.choice(['Team A', 'Team B', 'Team C', 'Team D'], n_matches),
    'away_team': np.random.choice(['Team E', 'Team F', 'Team G', 'Team H'], n_matches),
    'odds_home': np.random.uniform(1.5, 3.5, n_matches),
    'odds_draw': np.random.uniform(2.5, 4.5, n_matches),
    'odds_away': np.random.uniform(2.0, 5.0, n_matches),
    'bet_volume': np.random.uniform(50000, 500000, n_matches),
    'outcome': np.random.choice([1, 0, 2], n_matches, p=[0.45, 0.25, 0.30])
}

df = pd.DataFrame(data)
df.to_csv('sample_betting_data.csv', index=False)
```

## 数据验证

使用以下脚本验证数据格式:

```python
def validate_data(df):
    errors = []
    
    # 检查必填字段
    required_cols = ['match_id', 'match_date']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"缺少必填字段：{col}")
    
    # 检查赔率范围
    odds_cols = [col for col in df.columns if 'odds' in col.lower()]
    for col in odds_cols:
        if df[col].min() < 1.0:
            errors.append(f"{col} 存在小于 1.0 的值")
    
    # 检查时间格式
    if 'match_date' in df.columns:
        try:
            pd.to_datetime(df['match_date'])
        except:
            errors.append("match_date 格式不正确")
    
    return errors
```

## 相关文档

- [trend-methods.md](trend-methods.md) - 趋势分析方法
- [anomaly-methods.md](anomaly-methods.md) - 异常检测方法
- [attribution-methods.md](attribution-methods.md) - 归因分析方法
- [drill-down-guide.md](drill-down-guide.md) - 下钻分析指南
