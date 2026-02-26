# 阿里云 ODPS 查询工具

## 安装依赖

```bash
# 安装 ODPS 客户端和数据处理库
pip install pyodps pandas openpyxl
```

或

```bash
# 使用 requirements.txt
pip install -r requirements.txt
```

## 配置环境变量

在 `~/.bashrc` 或 `~/.zshrc` 中添加:

```bash
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_ENDPOINT="http://service.odps.aliyun.com/api"
export ALIBABA_ODPS_PROJECT="your_project_name"
```

然后执行:
```bash
source ~/.bashrc
```

## 使用示例

### 1. 列出所有表
```bash
python scripts/odps_query.py --action list --project my_project
```

### 2. 查看表结构
```bash
python scripts/odps_query.py --action describe --project my_project --table user_info
```

### 3. 执行 SQL 查询
```bash
python scripts/odps_query.py --action query --project my_project \
  --sql "SELECT * FROM user_info LIMIT 10"
```

### 4. 导出查询结果
```bash
python scripts/odps_query.py --action query --project my_project \
  --sql "SELECT * FROM order_detail WHERE pt >= '20260201'" \
  --output csv --output-file orders.csv
```

## 注意事项

1. **权限**: AccessKey 需要有对应 ODPS 项目的读取权限
2. **SQL 限制**: 仅支持 SELECT 查询
3. **计费**: ODPS 按扫描数据量计费，建议使用分区过滤
4. **结果限制**: 默认限制 100 行，可通过 --limit 调整

## 故障排查

### 问题 1: 找不到 odps 模块
```bash
pip install pyodps
```

### 问题 2: 认证失败
检查 AccessKey ID 和 Secret 是否正确，是否有对应项目权限

### 问题 3: 连接超时
检查网络连接，或尝试更换 endpoint:
```bash
python scripts/odps_query.py --endpoint http://service.odps.aliyun.com/api ...
```

### 问题 4: 表不存在
确认表名和项目名称是否正确，注意大小写
