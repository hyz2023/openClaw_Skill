#!/usr/bin/env python3
"""
Playtime Philippines 新闻监控 - 使用本地 SearxNG 搜索引擎
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 配置
SEARXNG_URL = "http://localhost:8080"
CONFIG_FILE = "/home/ubuntu/.openclaw/workspace/memory/playtime-tracker.json"

# 监控关键词
MONITORING_KEYWORDS = [
    "Playtime Philippines",
    "PlayTime Entertainment",
    "PT Gaming",
    "Playtime PH casino"
]

# 搜索相关扩展关键词
SEARCH_QUERIES = [
    "Playtime Philippines news",
    "PlayTime Entertainment news",
    "PT Gaming Philippines",
    "Playtime casino news",
    "PlayTime Miss Universe Philippines",
    "Playtime InsiderPH"
]


class PlaytimeNewsMonitor:
    """Playtime 新闻监控器"""
    
    def __init__(self, searxng_url: str = SEARXNG_URL):
        self.searxng_url = searxng_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "PlaytimeNewsMonitor/1.0"
        })
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "lastUpdate": datetime.now().isoformat(),
                "reportedNews": [],
                "monitoringKeywords": MONITORING_KEYWORDS
            }
    
    def _save_config(self):
        """保存配置文件"""
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_reported_urls(self) -> set:
        """获取已报道的新闻 URL 集合"""
        return {item.get("url", "") for item in self.config.get("reportedNews", [])}
    
    def test_searxng_connection(self) -> bool:
        """测试 SearxNG 连接"""
        try:
            response = self.session.get(self.searxng_url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ SearxNG 连接失败: {e}")
            return False
    
    def search_news(self, query: str, time_range: str = "day") -> List[Dict[str, Any]]:
        """
        使用 SearxNG 搜索新闻
        
        Args:
            query: 搜索关键词
            time_range: 时间范围 (day, week, month, year)
        
        Returns:
            搜索结果列表
        """
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo,news",
            "time_range": time_range,
            "safesearch": 0,
            "language": "en"
        }
        
        try:
            print(f"🔍 搜索: {query}")
            response = self.session.get(
                f"{self.searxng_url}/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except Exception as e:
            print(f"⚠️ 搜索失败 '{query}': {e}")
            return []
    
    def is_news_relevant(self, result: Dict[str, Any]) -> bool:
        """判断结果是否与 Playtime Philippines 公司相关"""
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        url = result.get("url", "").lower()
        
        text = title + " " + content + " " + url
        
        # 明确排除 Poppy Playtime 游戏相关内容
        if "poppy playtime" in text:
            return False
        
        # 必须包含 Playtime Philippines 相关关键词
        company_keywords = [
            "playtime philippines", "playtime.ph",
            "playtime entertainment", "pt gaming",
            "playtime casino", "playtime pagcor",
            "playtime gaming philippines"
        ]
        
        # 公司相关上下文词
        context_keywords = [
            "casino", "gaming", "gambling", "entertainment",
            "miss universe philippines", "pagcor",
            "philippines", "manila", "filipino"
        ]
        
        # 排除游戏/玩具相关词
        exclude_keywords = [
            "poppy playtime", "toy", "toys",
            "horror game", "video game", "steam",
            "chapter 1", "chapter 2", "chapter 3", "chapter 4", "chapter 5", "chapter 6",
            "mob entertainment", "epic games"
        ]
        
        # 如果包含排除词，直接返回 False
        if any(kw in text for kw in exclude_keywords):
            return False
        
        # 必须包含公司关键词
        has_company = any(kw in text for kw in company_keywords)
        
        # 或者包含 "playtime" + 上下文词
        has_playtime = "playtime" in text or "play time" in text
        has_context = any(kw in text for kw in context_keywords)
        
        return has_company or (has_playtime and has_context)
    
    def filter_recent_results(self, results: List[Dict[str, Any]], hours: int = 48) -> List[Dict[str, Any]]:
        """筛选近期结果（简化版，基于URL和标题去重）"""
        recent = []
        seen_urls = set()
        
        for result in results:
            url = result.get("url", "")
            title = result.get("title", "")
            
            # 去重
            if url in seen_urls or not url:
                continue
            seen_urls.add(url)
            
            # 检查是否已报道
            if url in self.get_reported_urls():
                continue
            
            # 检查相关性
            if self.is_news_relevant(result):
                recent.append(result)
        
        return recent
    
    def format_news_item(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化新闻条目"""
        title = result.get("title", "无标题")
        url = result.get("url", "")
        content = result.get("content", "")
        engine = result.get("engine", "unknown")
        
        # 生成简单摘要（前100字符）
        summary = content[:150] + "..." if len(content) > 150 else content
        
        return {
            "title": title,
            "url": url,
            "summary": summary,
            "source": engine,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reportedAt": datetime.now().isoformat()
        }
    
    def run_monitor(self) -> Dict[str, Any]:
        """运行完整监控任务"""
        print("=" * 70)
        print("📰 Playtime Philippines 新闻监控 - SearxNG 版本")
        print("=" * 70)
        
        # 测试 SearxNG 连接
        print("\n🔌 检测 SearxNG 服务连接...")
        if not self.test_searxng_connection():
            return {
                "success": False,
                "error": "SearxNG 连接失败",
                "newNews": []
            }
        print("✅ SearxNG 连接正常")
        
        # 搜索所有关键词
        print(f"\n🔍 开始搜索 {len(SEARCH_QUERIES)} 个查询...")
        all_results = []
        
        for query in SEARCH_QUERIES:
            results = self.search_news(query, time_range="week")
            all_results.extend(results)
            time.sleep(0.5)  # 避免请求过快
        
        print(f"\n📊 共获取 {len(all_results)} 个原始结果")
        
        # 筛选新且相关的结果
        new_results = self.filter_recent_results(all_results)
        print(f"✅ 筛选出 {len(new_results)} 条新且相关的新闻")
        
        # 格式化新闻
        new_news = [self.format_news_item(r) for r in new_results]
        
        # 报告
        report = {
            "success": True,
            "checkTime": datetime.now().isoformat(),
            "totalSearched": len(all_results),
            "newNewsCount": len(new_news),
            "newNews": new_news,
            "reportedUrls": list(self.get_reported_urls())
        }
        
        # 如果有新新闻，更新配置
        if new_news:
            print(f"\n🆕 发现 {len(new_news)} 条新新闻!")
            self.config["reportedNews"].extend(new_news)
            self.config["lastUpdate"] = datetime.now().isoformat()
            self._save_config()
            print("✅ 已保存到配置文件")
        else:
            print("\n📭 没有发现新新闻")
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印监控报告"""
        print("\n" + "=" * 70)
        print("📋 监控报告")
        print("=" * 70)
        print(f"搜索时间: {report.get('checkTime')}")
        print(f"搜索结果: {report.get('totalSearched')} 条")
        print(f"新新闻: {report.get('newNewsCount')} 条")
        
        if report.get('newNews'):
            print("\n🆕 新发现的新闻:")
            for i, news in enumerate(report['newNews'], 1):
                print(f"\n{i}. {news['title']}")
                print(f"   来源: {news['source']}")
                print(f"   URL: {news['url']}")
                if news.get('summary'):
                    print(f"   摘要: {news['summary']}")


def main():
    """主函数"""
    monitor = PlaytimeNewsMonitor()
    report = monitor.run_monitor()
    monitor.print_report(report)
    
    # 返回结果给调用者
    return report


if __name__ == "__main__":
    main()
