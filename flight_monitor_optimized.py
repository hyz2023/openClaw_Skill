#!/usr/bin/env python3
"""
航班价格监控应用 - 优化版
优化策略：最大化在广州停留时间

要求：
- 去程：周五下午/晚上 或 周六上午（越早越好）
- 回程：周日下午/晚上（仅考虑 12:00 之后的航班，越晚越好）
- 目标：在广州停留时间最大化（至少 36 小时）
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

# 配置
SEARXNG_URL = "http://localhost:8080"
CONFIG_FILE = "/home/ubuntu/.openclaw/workspace/memory/flights-manila-guangzhou.json"
OUTPUT_FILE = "/home/ubuntu/.openclaw/workspace/memory/flights-manila-guangzhou.json"


class OptimizedFlightMonitor:
    """优化版航班监控器 - 最大化停留时间"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "OptimizedFlightMonitor/2.0"
        })
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._default_config()
    
    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "route": "Manila (MNL) ↔ Guangzhou (CAN)",
            "requirements": {
                "outbound": "Friday afternoon/evening or Saturday morning",
                "return": "Sunday AFTERNOON/EVENING only (after 12:00 PM)",
                "maxPriceCNY": 2500,
                "optimization": "MAXIMIZE_GUANGZHOU_STAY_TIME"
            },
            "filterRules": {
                "minStayHours": 36,
                "returnTimeMin": "12:00",
                "preferredOutbound": "Friday 14:00-23:59 or Saturday 06:00-12:00",
                "preferredReturn": "Sunday 17:00-23:59"
            },
            "notifiedDeals": [],
            "lastCheck": None
        }
    
    def search_google_flights(self) -> List[Dict]:
        """
        搜索 Google Flights 航班信息
        使用优化的查询语句
        """
        # 优化的搜索查询 - 强调周日下午/晚上回程
        queries = [
            "Manila to Guangzhou flights Friday evening Sunday afternoon return 2026",
            "MNL to CAN weekend flights stay 2 days Sunday night return",
            "Cebu Pacific China Southern Manila Guangzhou Sunday evening departure",
            "广州 马尼拉 周末航班 周日晚 回程 2026",
        ]
        
        all_results = []
        
        for query in queries:
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "engines": "google,bing"
                }
                
                response = self.session.get(
                    f"{SEARXNG_URL}/search",
                    params=params,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("results", [])[:5]:
                        result['search_query'] = query
                        all_results.append(result)
                
                time.sleep(1)  # 避免请求过快
                
            except Exception as e:
                print(f"搜索失败 [{query[:50]}...]: {e}")
        
        return all_results
    
    def parse_flight_time(self, time_str: str) -> Optional[datetime]:
        """解析航班时间字符串"""
        time_formats = [
            "%H:%M",
            "%I:%M %p",
            "%I:%M%p",
        ]
        
        for fmt in time_formats:
            try:
                return datetime.strptime(time_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def calculate_stay_duration(self, outbound_time: str, return_time: str) -> float:
        """
        计算在广州停留时间（小时）
        
        Args:
            outbound_time: 去程到达时间 (如 "Friday 11:25 PM")
            return_time: 回程出发时间 (如 "Sunday 1:40 AM")
        
        Returns:
            停留小时数
        """
        # 简化计算：假设周五晚出发，周日回程
        # 将时间字符串转换为小时数
        
        def time_to_hours(time_str: str) -> float:
            """将时间字符串转换为小时数（从周五 0 点开始）"""
            time_str = time_str.lower()
            
            # 提取小时和分钟
            match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str)
            if not match:
                return 0
            
            hour = int(match.group(1))
            minute = int(match.group(2))
            am_pm = match.group(3)
            
            # 转换为 24 小时制
            if am_pm == 'pm' and hour != 12:
                hour += 12
            elif am_pm == 'am' and hour == 12:
                hour = 0
            
            # 计算从周五 0 点开始的小时数
            if 'friday' in time_str or 'fri' in time_str:
                day_offset = 0
            elif 'saturday' in time_str or 'sat' in time_str:
                day_offset = 24
            elif 'sunday' in time_str or 'sun' in time_str:
                day_offset = 48
            else:
                day_offset = 0
            
            return day_offset + hour + minute / 60
        
        outbound_hours = time_to_hours(outbound_time)
        return_hours = time_to_hours(return_time)
        
        # 停留时间 = 回程时间 - 去程时间
        stay_hours = return_hours - outbound_hours
        
        return max(0, stay_hours)
    
    def filter_optimized_flights(self, results: List[Dict]) -> List[Dict]:
        """
        筛选优化的航班组合
        
        筛选规则：
        1. 回程必须在周日 12:00 之后
        2. 停留时间至少 36 小时
        3. 优先选择周日晚上的回程航班
        4. 价格低于目标值
        """
        optimized = []
        
        max_price = self.config["requirements"].get("maxPriceCNY", 2500)
        min_return_hour = 12  # 周日最低回程时间
        
        for result in results:
            title = result.get("title", "") + " " + result.get("content", "")
            url = result.get("url", "")
            
            # 检查是否包含价格信息
            price_match = re.search(r'[\$¥₱]\s*([\d,]+)|(\d+)\s*(CNY|USD|PHP)', title, re.IGNORECASE)
            if not price_match:
                continue
            
            # 提取价格
            price_cny = self._extract_price_cny(title)
            if not price_cny or price_cny > max_price:
                continue
            
            # 检查回程时间
            # 查找周日下午/晚上的时间
            sunday_match = re.search(r'sunday.*?(\d{1,2}:\d{2}\s*(?:am|pm)?)', title, re.IGNORECASE)
            if sunday_match:
                return_time_str = sunday_match.group(1)
                return_time = self.parse_flight_time(return_time_str)
                
                if return_time:
                    # 检查是否在 12:00 之后
                    if return_time.hour < 12:
                        continue  # 跳过中午之前的航班
            
            # 计算停留时间（如果能提取到时间信息）
            outbound_match = re.search(r'friday.*?(\d{1,2}:\d{2}\s*(?:am|pm)?)', title, re.IGNORECASE)
            if outbound_match and sunday_match:
                stay_hours = self._estimate_stay_hours(title)
                if stay_hours and stay_hours < 36:
                    continue  # 停留时间不足 36 小时
            else:
                stay_hours = None
            
            # 符合条件的航班
            flight_info = {
                "title": result.get("title", ""),
                "url": url,
                "price_cny": price_cny,
                "stay_hours": stay_hours,
                "snippet": result.get("content", "")[:200],
                "source": result.get("engine", "unknown"),
                "optimized": True
            }
            
            optimized.append(flight_info)
        
        # 按停留时间排序（优先停留时间长的）
        optimized.sort(key=lambda x: (x.get("stay_hours") or 0, -x.get("price_cny", 9999)), reverse=True)
        
        return optimized
    
    def _extract_price_cny(self, text: str) -> Optional[float]:
        """从文本中提取价格并转换为 CNY"""
        # 匹配各种货币符号
        patterns = [
            (r'[\$¥]\s*([\d,]+)', 1.0),  # USD/CNY 直接转换
            (r'₱\s*([\d,]+)', 0.14),  # PHP 转 CNY (近似)
            (r'(\d+)\s*CNY', 1.0),
            (r'(\d+)\s*USD', 7.2),  # USD 转 CNY
            (r'A\$\s*([\d,]+)', 4.6),  # AUD 转 CNY
        ]
        
        for pattern, rate in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = float(match.group(1).replace(',', ''))
                return price * rate
        
        return None
    
    def _estimate_stay_hours(self, text: str) -> Optional[float]:
        """从文本中估算停留时间"""
        # 尝试提取去程和回程时间
        friday_match = re.search(r'friday.*?(\d{1,2}:\d{2})\s*(am|pm)?', text, re.IGNORECASE)
        sunday_match = re.search(r'sunday.*?(\d{1,2}:\d{2})\s*(am|pm)?', text, re.IGNORECASE)
        
        if friday_match and sunday_match:
            # 简化估算
            fri_hour = int(friday_match.group(1))
            sun_hour = int(sunday_match.group(1))
            
            # 计算小时差
            if 'pm' in (friday_match.group(2) or '').lower() and fri_hour != 12:
                fri_hour += 12
            
            if 'am' in (sunday_match.group(2) or '').lower() and sun_hour != 12:
                sun_hour += 0
            elif 'pm' in (sunday_match.group(2) or '').lower() and sun_hour != 12:
                sun_hour += 12
            
            # 估算停留时间（周五到周日）
            stay = (48 + sun_hour) - (fri_hour)
            return max(0, stay)
        
        return None
    
    def generate_report(self, flights: List[Dict]) -> Dict:
        """生成优化报告"""
        report = {
            "check_time": datetime.now().isoformat(),
            "optimization": "MAXIMIZE_GUANGZHOU_STAY_TIME",
            "requirements": {
                "return_after": "12:00 PM Sunday",
                "min_stay_hours": 36,
                "max_price_cny": self.config["requirements"].get("maxPriceCNY", 2500)
            },
            "total_results": len(flights),
            "flights": flights,
            "best_deal": flights[0] if flights else None,
            "recommendations": []
        }
        
        # 生成推荐
        if flights:
            best = flights[0]
            report["recommendations"].append(
                f"✈️ 最佳选择：停留约 {best.get('stay_hours', 'N/A')} 小时，"
                f"价格 ¥{best.get('price_cny', 'N/A')} CNY"
            )
            
            # 检查是否有周日晚上的航班
            evening_flights = [f for f in flights if f.get('stay_hours', 0) and f.get('stay_hours', 0) > 40]
            if evening_flights:
                report["recommendations"].append(
                    f"🌙 发现 {len(evening_flights)} 个周日晚回程航班，停留时间更长"
                )
        
        return report
    
    def save_results(self, report: Dict):
        """保存结果到配置文件"""
        # 更新配置文件
        self.config["lastCheck"] = datetime.now().isoformat()
        
        # 添加新发现到 notifiedDeals（避免重复）
        existing_ids = {d.get("id") for d in self.config.get("notifiedDeals", [])}
        
        for flight in report.get("flights", []):
            deal_id = f"optimized-{datetime.now().strftime('%Y%m%d')}-{hash(flight.get('url', '')) % 10000}"
            
            if deal_id not in existing_ids:
                self.config.setdefault("notifiedDeals", []).append({
                    "id": deal_id,
                    "airline": "Multiple",
                    "route": "MNL ↔ CAN",
                    "price": f"¥{flight.get('price_cny', 'N/A')} CNY",
                    "priceCNY": flight.get("price_cny"),
                    "stay_hours": flight.get("stay_hours"),
                    "type": "Optimized (Sunday PM return)",
                    "url": flight.get("url"),
                    "foundDate": datetime.now().strftime("%Y-%m-%d"),
                    "optimization": "MAXIMIZE_GUANGZHOU_STAY_TIME"
                })
                existing_ids.add(deal_id)
        
        # 保存
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存：{OUTPUT_FILE}")
    
    def run(self):
        """运行监控"""
        print("="*70)
        print("✈️  航班监控 - 优化版（最大化广州停留时间）")
        print("="*70)
        print("\n📋 优化策略:")
        print("  - 去程：周五下午/晚上 或 周六上午")
        print("  - 回程：周日 12:00 之后（下午/晚上优先）")
        print("  - 目标：最大化在广州停留时间（≥36 小时）")
        print("="*70)
        
        # 搜索航班
        print("\n🔍 正在搜索优化的航班组合...")
        results = self.search_google_flights()
        print(f"找到 {len(results)} 个搜索结果")
        
        # 筛选优化航班
        print("\n🎯 筛选优化的航班（周日 12:00 后回程）...")
        optimized = self.filter_optimized_flights(results)
        print(f"找到 {len(optimized)} 个符合条件的航班")
        
        # 生成报告
        print("\n📊 生成报告...")
        report = self.generate_report(optimized)
        
        # 显示结果
        print("\n" + "="*70)
        print("📋 优化航班报告")
        print("="*70)
        
        if optimized:
            print(f"\n✅ 找到 {len(optimized)} 个优化的航班选择\n")
            
            for i, flight in enumerate(optimized[:5], 1):
                print(f"{i}. {flight.get('title', 'N/A')[:80]}")
                print(f"   价格：¥{flight.get('price_cny', 'N/A')} CNY")
                print(f"   预估停留：{flight.get('stay_hours', 'N/A')} 小时")
                print(f"   链接：{flight.get('url', 'N/A')[:60]}")
                print()
        else:
            print("\n⚠️  未找到完全符合优化条件的航班")
            print("   建议：放宽回程时间限制或调整出行日期")
        
        # 推荐
        if report.get("recommendations"):
            print("\n💡 推荐:")
            for rec in report["recommendations"]:
                print(f"  {rec}")
        
        # 保存结果
        self.save_results(report)
        
        print("\n✅ 监控完成!")
        
        return report


def main():
    """主函数"""
    monitor = OptimizedFlightMonitor()
    report = monitor.run()
    
    # 返回状态码
    if report.get("flights"):
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
