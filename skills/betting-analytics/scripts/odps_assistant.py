#!/usr/bin/env python3
"""
ODPS 数据助手 - 统一入口
整合元数据采集和 AI 检索功能
"""

import sys
import os
from pathlib import Path

# 添加脚本目录到路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))


def cmd_crawl(args):
    """采集元数据"""
    from odps_metadata_crawler import main as crawl_main
    crawl_main()


def cmd_search(args):
    """AI 检索"""
    from odps_ai_search import main as search_main
    search_main()


def cmd_demo(args):
    """演示模式"""
    from odps_ai_search import ODPSSemanticSearch
    
    print("\n" + "="*70)
    print("🤖 ODPS 数据助手 - 演示")
    print("="*70)
    
    # 初始化
    searcher = ODPSSemanticSearch('odps_metadata')
    
    # 演示查询
    demo_queries = [
        "查询用户投注数据",
        "统计每天的投注金额",
        "用户登录名和平台信息",
        "游戏种类和输赢统计"
    ]
    
    for query in demo_queries:
        print(f"\n{'='*70}")
        print(f"📝 查询：{query}")
        print('='*70)
        
        result = searcher.search(query)
        searcher._print_results(result)
        
        print("\n💡 推荐 SQL:")
        print("-" * 70)
        sql = searcher.generate_query_suggestion(result)
        print(sql)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='ODPS 数据助手',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 采集元数据
  python odps_assistant.py crawl
  
  # AI 检索
  python odps_assistant.py search -q "查询用户投注数据"
  
  # 交互模式
  python odps_assistant.py search -i
  
  # 演示
  python odps_assistant.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # crawl 命令
    crawl_parser = subparsers.add_parser('crawl', help='采集 ODPS 元数据')
    crawl_parser.add_argument('--output', default='odps_metadata', help='输出目录')
    crawl_parser.set_defaults(func=cmd_crawl)
    
    # search 命令
    search_parser = subparsers.add_parser('search', help='AI 检索表和字段')
    search_parser.add_argument('-q', '--query', type=str, help='查询语句')
    search_parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    search_parser.add_argument('--metadata-dir', default='odps_metadata', help='元数据目录')
    search_parser.set_defaults(func=cmd_search)
    
    # demo 命令
    demo_parser = subparsers.add_parser('demo', help='演示模式')
    demo_parser.set_defaults(func=cmd_demo)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
