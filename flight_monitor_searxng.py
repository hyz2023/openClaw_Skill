#!/usr/bin/env python3
"""
航班价格监控应用 - 使用本地 SearxNG 搜索引擎
监控马尼拉 ↔ 广州的航班价格
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# 配置
SEARXNG_URL = "http://localhost:8080"
CONFIG_FILE = "/home/ubuntu/.openclaw/workspace/memory/flights-manila-guangzhou.json"

class FlightPriceMonitor:
    """航班价格监控器"""
    
    def __init__(self, searxng_url: str = SEARXNG_URL):
        self.searxng_url = searxng_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "FlightPriceMonitor/1.0"
        })
        
    def search_flights(self, route: str, date: str = None) -> Dict[str, Any]:
        """
        使用 SearxNG 搜索航班信息
        
        Args:
            route: 航线描述 (如 "Manila to Guangzhou flights")
            date: 日期 (可选)
        
        Returns:
            搜索结果字典
        """
        # 构建搜索查询
        query = f"{route} flights price"
        if date:
            query += f" {date}"
        
        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo"
        }
        
        try:
            print(f"🔍 正在搜索: {query}")
            response = self.session.get(
                f"{self.searxng_url}/search",
                params=params,
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "query": query,
                "results": data.get("results", []),
                "suggestions": data.get("suggestions", []),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
                "timestamp": datetime.now().isoformat()
            }
    
    def extract_price_info(self, results: List[Dict]) -> List[Dict]:
        """
        从搜索结果中提取航班价格信息
        
        Args:
            results: SearxNG 搜索结果列表
        
        Returns:
            提取的价格信息列表
        """
        price_info = []
        
        for result in results[:10]:  # 只处理前10个结果
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            # 提取可能包含价格的条目
            info = {
                "title": title,
                "url": url,
                "snippet": content[:200] if content else "",
                "source": result.get("engine", "unknown"),
                "has_price": False
            }
            
            # 简单判断内容是否包含价格信息
            price_keywords = ["price", "fare", "cost", "$", "USD", "CNY", "¥", "₱", "from", "cheap"]
            if any(keyword.lower() in (title + content).lower() for keyword in price_keywords):
                info["has_price"] = True
            
            price_info.append(info)
        
        return price_info
    
    def check_route(self, origin: str, destination: str, max_price: float = None) -> Dict[str, Any]:
        """
        检查特定航线的价格
        
        Args:
            origin: 出发地
            destination: 目的地
            max_price: 最高可接受价格
        
        Returns:
            检查结果报告
        """
        route = f"{origin} to {destination}"
        search_result = self.search_flights(route)
        
        if not search_result["success"]:
            return {
                "route": route,
                "status": "error",
                "error": search_result.get("error", "搜索失败"),
                "timestamp": search_result["timestamp"]
            }
        
        # 提取价格信息
        price_info = self.extract_price_info(search_result["results"])
        
        # 分析结果
        report = {
            "route": route,
            "status": "success",
            "total_results": len(search_result["results"]),
            "price_related_results": len([p for p in price_info if p["has_price"]]),
            "results": price_info,
            "timestamp": search_result["timestamp"]
        }
        
        return report
    
    def monitor_round_trip(self, 
                          origin: str, 
                          destination: str,
                          max_price_cny: float = 2500) -> Dict[str, Any]:
        """
        监控往返航班
        
        Args:
            origin: 出发地
            destination: 目的地
            max_price_cny: 最高可接受价格 (CNY)
        
        Returns:
            往返检查结果
        """
        print(f"\n✈️  开始监控往返航班: {origin} ↔ {destination}")
        print(f"💰 目标价格: ≤ ¥{max_price_cny} CNY")
        print("-" * 60)
        
        # 检查 outbound
        outbound = self.check_route(origin, destination)
        print(f"\n📤 去程 ({origin} → {destination}):")
        if outbound["status"] == "success":
            print(f"   找到 {outbound['total_results']} 个结果")
            print(f"   其中 {outbound['price_related_results']} 个包含价格信息")
        else:
            print(f"   ❌ 错误: {outbound.get('error', '未知错误')}")
        
        # 检查 return
        return_flight = self.check_route(destination, origin)
        print(f"\n📥 返程 ({destination} → {origin}):")
        if return_flight["status"] == "success":
            print(f"   找到 {return_flight['total_results']} 个结果")
            print(f"   其中 {return_flight['price_related_results']} 个包含价格信息")
        else:
            print(f"   ❌ 错误: {return_flight.get('error', '未知错误')}")
        
        return {
            "origin": origin,
            "destination": destination,
            "max_price_cny": max_price_cny,
            "outbound": outbound,
            "return": return_flight,
            "check_time": datetime.now().isoformat()
        }
    
    def test_searxng_connection(self) -> bool:
        """测试 SearxNG 连接是否正常"""
        try:
            response = self.session.get(self.searxng_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ SearxNG 连接正常: {self.searxng_url}")
                return True
            else:
                print(f"⚠️  SearxNG 返回状态码: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 无法连接到 SearxNG: {e}")
            return False


def run_flight_monitor_test():
    """运行航班监控测试"""
    print("=" * 70)
    print("✈️  航班价格监控应用 - SearxNG 版本")
    print("=" * 70)
    
    monitor = FlightPriceMonitor()
    
    # 第一步：测试 SearxNG 连接
    print("\n🔌 步骤 1: 检测 SearxNG 服务")
    print("-" * 70)
    if not monitor.test_searxng_connection():
        print("\n❌ 服务连接失败，请检查 SearxNG 是否运行")
        print("   启动命令: cd /home/ubuntu/.openclaw/workspace/searxng && sudo docker-compose up -d")
        return
    
    # 第二步：测试基本搜索
    print("\n🔍 步骤 2: 测试基本搜索功能")
    print("-" * 70)
    test_search = monitor.search_flights("Cebu Pacific Manila Guangzhou")
    if test_search["success"]:
        print(f"✅ 搜索成功！找到 {len(test_search['results'])} 个结果")
        print(f"   查询: {test_search['query']}")
    else:
        print(f"❌ 搜索失败: {test_search.get('error', '未知错误')}")
        return
    
    # 第三步：监控往返航班
    print("\n📊 步骤 3: 监控往返航班价格")
    print("-" * 70)
    report = monitor.monitor_round_trip(
        origin="Manila",
        destination="Guangzhou",
        max_price_cny=2500
    )
    
    # 第四步：显示详细结果示例
    print("\n📋 步骤 4: 搜索结果示例")
    print("-" * 70)
    if test_search["results"]:
        print("\n前 5 个搜索结果:")
        for i, result in enumerate(test_search["results"][:5], 1):
            title = result.get("title", "无标题")
            engine = result.get("engine", "unknown")
            print(f"\n{i}. {title}")
            print(f"   来源: {engine}")
            if result.get("content"):
                snippet = result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"]
                print(f"   摘要: {snippet}")
    
    # 保存报告
    report_file = "/home/ubuntu/.openclaw/workspace/memory/flight_monitor_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 监控完成！报告已保存至: {report_file}")
    print("=" * 70)


if __name__ == "__main__":
    run_flight_monitor_test()
