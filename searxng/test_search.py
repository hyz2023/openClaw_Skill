#!/usr/bin/env python3
"""
SearxNG 搜索接口测试应用
用于测试自托管搜索引擎的 API 调用
"""

import requests
import json
from typing import List, Dict, Any

SEARXNG_URL = "http://localhost:8080"

def search(query: str, engines: List[str] = None, categories: List[str] = None) -> Dict[str, Any]:
    """
    执行搜索请求
    
    Args:
        query: 搜索关键词
        engines: 指定搜索引擎列表 (可选)
        categories: 指定搜索类别 (可选)
    
    Returns:
        搜索结果字典
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
        response = requests.get(f"{SEARXNG_URL}/search", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "results": []}


def display_results(results: Dict[str, Any], limit: int = 10) -> None:
    """
    格式化显示搜索结果
    
    Args:
        results: 搜索结果字典
        limit: 显示结果数量限制
    """
    if "error" in results:
        print(f"❌ 搜索失败：{results['error']}")
        return
    
    query = results.get("query", "")
    total = results.get("number_of_results", 0)
    search_results = results.get("results", [])
    suggestions = results.get("suggestions", [])
    
    print(f"\n🔍 搜索查询：{query}")
    print(f"📊 结果数量：{total}")
    print("=" * 60)
    
    for i, result in enumerate(search_results[:limit], 1):
        title = result.get("title", "无标题")
        url = result.get("url", "")
        content = result.get("content", "")
        engine = result.get("engine", "unknown")
        
        print(f"\n{i}. {title}")
        print(f"   🔗 {url}")
        if content:
            # 截断过长的内容
            content_preview = content[:150] + "..." if len(content) > 150 else content
            print(f"   📝 {content_preview}")
        print(f"   🛠️  来源：{engine}")
    
    if suggestions:
        print(f"\n💡 相关建议：{', '.join(suggestions[:5])}")
    
    print("=" * 60)


def test_basic_search():
    """测试基本搜索功能"""
    print("\n🧪 测试 1: 基本搜索")
    results = search("人工智能最新发展")
    display_results(results, limit=5)


def test_multi_engine():
    """测试多引擎搜索"""
    print("\n🧪 测试 2: 指定搜索引擎 (Google + Wikipedia)")
    results = search("Python programming", engines=["google", "wikipedia"])
    display_results(results, limit=5)


def test_category_search():
    """测试分类搜索"""
    print("\n🧪 测试 3: 技术类搜索")
    results = search("machine learning", categories=["it"])
    display_results(results, limit=5)


def test_json_output():
    """测试 JSON 输出格式"""
    print("\n🧪 测试 4: 原始 JSON 输出 (前 3 条结果)")
    results = search("open source")
    
    if "error" not in results:
        print(json.dumps(results["results"][:3], indent=2, ensure_ascii=False))


def ai_integration_example():
    """
    AI 应用集成示例
    演示如何在 AI 应用中调用搜索接口获取实时信息
    """
    print("\n🤖 AI 应用集成示例")
    print("=" * 60)
    
    # 模拟 AI 应用需要实时信息的场景
    user_question = "2026 年最新的人工智能技术有哪些？"
    print(f"用户问题：{user_question}")
    
    # 从 SearxNG 获取实时信息
    search_results = search("2026 AI technology trends", engines=["google", "bing"])
    
    if "error" not in search_results and search_results.get("results"):
        print(f"\n📚 从搜索引擎获取到 {len(search_results['results'])} 条相关信息")
        
        # 提取关键信息供 AI 使用
        context = []
        for result in search_results["results"][:5]:
            context.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", "")
            })
        
        print("\n📋 提取的上下文信息:")
        for i, info in enumerate(context, 1):
            print(f"{i}. {info['title']}")
            print(f"   {info['snippet'][:100]}...")
        
        # 这里可以将 context 传递给 LLM 生成回答
        print("\n✅ 这些搜索结果可以作为 LLM 的上下文，生成准确的回答")
    else:
        print("❌ 搜索失败")
    
    print("=" * 60)


if __name__ == "__main__":
    print("🚀 SearxNG 搜索接口测试")
    print(f"📍 服务地址：{SEARXNG_URL}")
    
    # 检查服务是否可用
    try:
        response = requests.get(SEARXNG_URL, timeout=5)
        if response.status_code == 200:
            print("✅ SearxNG 服务正常运行\n")
        else:
            print(f"⚠️  服务响应异常：{response.status_code}\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到 SearxNG: {e}")
        print("请确保服务已启动：cd /home/ubuntu/.openclaw/workspace/searxng && sudo docker-compose ps")
        exit(1)
    
    # 运行测试
    test_basic_search()
    test_multi_engine()
    test_category_search()
    test_json_output()
    ai_integration_example()
    
    print("\n✅ 所有测试完成！")
