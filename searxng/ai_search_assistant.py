#!/usr/bin/env python3
"""
AI 搜索助手 - 演示如何在 AI 应用中集成 SearxNG
提供实时搜索能力，增强 AI 回答的准确性和时效性
"""

import requests
import json
from datetime import datetime

SEARXNG_URL = "http://localhost:8080"

class AISearchAssistant:
    """AI 搜索助手类"""
    
    def __init__(self, base_url: str = SEARXNG_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AI-Search-Assistant/1.0"
        })
    
    def search(self, query: str, max_results: int = 10, engines: list = None, categories: list = None) -> dict:
        """
        执行搜索并返回结构化结果
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            engines: 指定搜索引擎列表
            categories: 指定搜索类别
        
        Returns:
            包含搜索结果和元数据的字典
        """
        params = {
            "q": query,
            "format": "json"
        }
        
        if engines:
            params["engines"] = ",".join(engines)
        
        if categories:
            params["categories"] = ",".join(categories)
        
        try:
            response = self.session.get(f"{self.base_url}/search", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # 提取关键信息
            return {
                "query": data.get("query", query),
                "total_results": data.get("number_of_results", 0),
                "results": data.get("results", [])[:max_results],
                "suggestions": data.get("suggestions", [])[:5],
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
        except Exception as e:
            return {
                "query": query,
                "error": str(e),
                "results": [],
                "success": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_news(self, topic: str, max_results: int = 5) -> dict:
        """获取新闻类搜索结果"""
        return self.search(topic, max_results, categories=["news"])
    
    def get_technical_info(self, topic: str, max_results: int = 10) -> dict:
        """获取技术类搜索结果"""
        return self.search(topic, max_results, categories=["it", "science"])
    
    def format_for_llm(self, search_result: dict) -> str:
        """
        将搜索结果格式化为适合 LLM 的上下文字符串
        
        Args:
            search_result: 搜索结果字典
        
        Returns:
            格式化的上下文字符串
        """
        if not search_result.get("success"):
            return f"搜索失败：{search_result.get('error', '未知错误')}"
        
        lines = [
            f"📊 搜索查询：{search_result['query']}",
            f"⏰ 搜索时间：{search_result['timestamp']}",
            f"📈 结果数量：{search_result['total_results']}",
            "",
            "📚 相关信息："
        ]
        
        for i, result in enumerate(search_result["results"], 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            content = result.get("content", "")
            source = result.get("engine", "unknown")
            
            lines.append(f"\n{i}. {title}")
            lines.append(f"   来源：{source}")
            lines.append(f"   链接：{url}")
            if content:
                # 限制内容长度
                preview = content[:200] + "..." if len(content) > 200 else content
                lines.append(f"   摘要：{preview}")
        
        if search_result.get("suggestions"):
            lines.append(f"\n💡 相关搜索：{', '.join(search_result['suggestions'])}")
        
        return "\n".join(lines)


def demo_ai_workflow():
    """演示 AI 工作流：用户提问 → 搜索 → 生成回答"""
    
    print("=" * 70)
    print("🤖 AI 搜索助手演示")
    print("=" * 70)
    
    assistant = AISearchAssistant()
    
    # 示例 1: 实时新闻查询
    print("\n📰 场景 1: 查询最新科技新闻")
    print("-" * 70)
    
    user_question = "2026 年 AI 领域有什么新突破？"
    print(f"用户提问：{user_question}")
    
    # 搜索相关信息
    search_result = assistant.search("2026 AI breakthrough technology", max_results=5)
    
    # 格式化为 LLM 上下文
    context = assistant.format_for_llm(search_result)
    print("\n" + context)
    
    # 模拟 LLM 回答（实际应用中这里会调用 LLM API）
    print("\n🤖 AI 回答示例:")
    print("根据最新搜索结果，2026 年 AI 领域的主要突破包括：")
    print("1. AI Agent 技术的成熟和广泛应用")
    print("2. 多模态模型的进一步发展")
    print("3. AI 在科学研究中的深度整合")
    print("\n*以上信息基于实时搜索，确保时效性和准确性*")
    
    # 示例 2: 技术问题解答
    print("\n\n💻 场景 2: 技术问题解答")
    print("-" * 70)
    
    tech_question = "如何在 Python 中实现异步编程？"
    print(f"用户提问：{tech_question}")
    
    tech_result = assistant.get_technical_info("Python async programming tutorial", max_results=5)
    context = assistant.format_for_llm(tech_result)
    print("\n" + context)
    
    # 示例 3: 代码示例搜索
    print("\n\n🔧 场景 3: 代码示例搜索")
    print("-" * 70)
    
    code_question = "Python asyncio 最佳实践"
    print(f"搜索：{code_question}")
    
    code_result = assistant.search("Python asyncio best practices example", 
                                   max_results=5, 
                                   engines=["github", "google"])
    
    if code_result["success"]:
        print(f"\n✅ 找到 {len(code_result['results'])} 个相关资源")
        for result in code_result["results"][:3]:
            print(f"  • {result.get('title', 'N/A')} - {result.get('url', 'N/A')[:60]}")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)


def api_usage_example():
    """展示 API 调用示例代码"""
    
    print("\n\n📝 API 调用示例代码:")
    print("-" * 70)
    
    example_code = '''
# 在你的 AI 应用中使用 SearxNG

import requests

def search_with_searxng(query):
    """调用 SearxNG 搜索接口"""
    url = "http://localhost:8080/search"
    params = {
        "q": query,
        "format": "json"
    }
    
    response = requests.get(url, params=params)
    results = response.json()
    
    return results["results"]

# 使用示例
results = search_with_searxng("machine learning tutorials")
for result in results[:5]:
    print(f"标题：{result['title']}")
    print(f"链接：{result['url']}")
    print(f"摘要：{result['content'][:100]}...")
    print("-" * 50)
'''
    
    print(example_code)


if __name__ == "__main__":
    # 检查服务状态
    try:
        response = requests.get(SEARXNG_URL, timeout=5)
        if response.status_code == 200:
            print(f"✅ SearxNG 服务正常：{SEARXNG_URL}")
        else:
            print(f"⚠️  服务响应异常：{response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到 SearxNG: {e}")
        exit(1)
    
    # 运行演示
    demo_ai_workflow()
    api_usage_example()
    
    print("\n💡 提示：将 AISearchAssistant 集成到你的 AI 应用中，")
    print("   可以让 AI 获得实时搜索能力，回答更准确、更及时！")
