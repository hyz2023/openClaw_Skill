# SearxNG 自托管搜索引擎

为 AI 应用提供隐私保护的实时搜索能力。

## 🚀 快速访问

- **Web 界面**: http://localhost:8080
- **API 端点**: http://localhost:8080/search?q=关键词&format=json

## 📦 部署结构

```
searxng/
├── docker-compose.yml      # Docker Compose 配置
├── .env                    # 环境变量（密钥）
├── searxng/
│   └── settings.yml        # SearxNG 配置文件
├── test_search.py          # 基础测试脚本
├── ai_search_assistant.py  # AI 集成示例
└── README.md               # 本文档
```

## 🔧 管理命令

```bash
# 查看服务状态
cd /home/ubuntu/.openclaw/workspace/searxng
sudo docker-compose ps

# 查看日志
sudo docker-compose logs -f searxng

# 重启服务
sudo docker-compose restart

# 停止服务
sudo docker-compose down

# 启动服务
sudo docker-compose up -d
```

## 📡 API 使用

### 基本搜索

```bash
curl "http://localhost:8080/search?q=Python+programming&format=json"
```

### 指定搜索引擎

```bash
curl "http://localhost:8080/search?q=AI&format=json&engines=google,wikipedia,github"
```

### 分类搜索

```bash
# 技术类
curl "http://localhost:8080/search?q=machine+learning&format=json&categories=it"

# 新闻类
curl "http://localhost:8080/search?q=tech+news&format=json&categories=news"

# 科学类
curl "http://localhost:8080/search?q=quantum+computing&format=json&categories=science"
```

## 🤖 AI 应用集成

### Python 示例

```python
import requests

def search_with_searxng(query, engines=None):
    """调用 SearxNG 搜索接口"""
    url = "http://localhost:8080/search"
    params = {
        "q": query,
        "format": "json"
    }
    
    if engines:
        params["engines"] = ",".join(engines)
    
    response = requests.get(url, params=params)
    return response.json()

# 使用示例
results = search_with_searxng("machine learning tutorials")
for result in results["results"][:5]:
    print(f"标题：{result['title']}")
    print(f"链接：{result['url']}")
    print(f"摘要：{result['content'][:100]}...")
    print("-" * 50)
```

### 集成到 AI 工作流

```python
from ai_search_assistant import AISearchAssistant

# 创建助手实例
assistant = AISearchAssistant()

# 执行搜索
search_result = assistant.search("2026 AI trends", max_results=10)

# 格式化为 LLM 上下文
context = assistant.format_for_llm(search_result)

# 将 context 传递给 LLM 生成回答
# response = llm.generate(f"基于以下信息回答问题:\n{context}\n\n问题：{user_question}")
```

## 🧪 测试脚本

### 基础测试
```bash
python3 test_search.py
```

### AI 助手演示
```bash
python3 ai_search_assistant.py
```

## ⚙️ 已配置搜索引擎

- **通用搜索**: Google, Bing, DuckDuckGo, Brave, Startpage
- **知识库**: Wikipedia
- **代码**: GitHub
- **学术**: Google Scholar（可选）

## 🔒 隐私特性

- ✅ 不记录搜索历史
- ✅ 不追踪用户行为
- ✅ 去除搜索结果中的追踪参数
- ✅ 支持 Tor 出口节点
- ✅ 自托管，数据完全可控

## 📊 性能优化

- Redis 缓存已启用（减少重复搜索）
- 镜像代理已开启（保护隐私）
- 默认启用 5 个主流搜索引擎

## 🛠️ 故障排查

### 服务无法启动
```bash
# 检查 Docker 容器状态
sudo docker-compose ps

# 查看详细日志
sudo docker-compose logs searxng

# 重新创建容器
sudo docker-compose down
sudo docker-compose up -d
```

### 搜索返回空结果
1. 检查网络连接
2. 查看引擎状态：访问 http://localhost:8080/preferences
3. 某些引擎可能被目标网站限流，可调整 `settings.yml` 中的引擎配置

### 端口冲突
如果 8080 端口被占用，修改 `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # 改为其他端口
```

## 📚 相关资源

- [SearxNG 官方文档](https://docs.searxng.org/)
- [SearxNG GitHub](https://github.com/searxng/searxng)
- [引擎列表](https://docs.searxng.org/admin/engines/engines.html)

---

**部署时间**: 2026-02-24  
**版本**: SearxNG 2026.2.23  
**状态**: ✅ 运行正常
