#!/usr/bin/env python3
"""
ODPS AI 检索工具
根据用户需求，智能推荐可查询的表和字段

功能:
1. 加载本地元数据
2. 语义匹配表和字段
3. 生成查询建议
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
import re


class ODPSSemanticSearch:
    """ODPS 语义搜索引擎"""
    
    def __init__(self, metadata_dir: str = 'odps_metadata'):
        self.metadata_dir = Path(metadata_dir)
        self.tables = []
        self.columns = []
        self.column_index = {}  # 字段名 → 表列表
        self.keyword_index = {}  # 关键词 → 表/字段列表
        
        self._load_metadata()
        self._build_index()
    
    def _load_metadata(self):
        """加载元数据"""
        latest_json = self.metadata_dir / 'metadata_latest.json'
        latest_csv = self.metadata_dir / 'columns_latest.csv'
        
        if not latest_json.exists():
            raise FileNotFoundError(f"未找到元数据文件：{latest_json}")
        
        # 加载 JSON
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.tables = data['tables']
        
        # 加载 CSV
        import pandas as pd
        df = pd.read_csv(latest_csv)
        self.columns = df.to_dict('records')
        
        print(f"✅ 加载 {len(self.tables)} 张表，{len(self.columns)} 个字段")
    
    def _build_index(self):
        """构建索引"""
        # 字段名索引
        for col in self.columns:
            col_name = col['column_name'].lower()
            if col_name not in self.column_index:
                self.column_index[col_name] = []
            self.column_index[col_name].append(col)
        
        # 关键词索引 (从注释中提取)
        for table in self.tables:
            table_name = table['table_name']
            
            # 表注释分词
            if table.get('comment'):
                keywords = self._extract_keywords(table['comment'])
                for kw in keywords:
                    if kw not in self.keyword_index:
                        self.keyword_index[kw] = []
                    self.keyword_index[kw].append({
                        'type': 'table',
                        'name': table_name,
                        'match': 'comment'
                    })
            
            # 字段注释分词
            for col in table['columns']:
                if col.get('comment'):
                    keywords = self._extract_keywords(col['comment'])
                    for kw in keywords:
                        if kw not in self.keyword_index:
                            self.keyword_index[kw] = []
                        self.keyword_index[kw].append({
                            'type': 'column',
                            'table': table_name,
                            'column': col['name'],
                            'match': 'comment'
                        })
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        if not text:
            return []
        
        # 中文分词 (简单按字符)
        keywords = []
        
        # 英文单词
        english_words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text.lower())
        keywords.extend(english_words)
        
        # 中文关键词 (2-4 字)
        chinese_chars = re.findall(r'[\u4e00-\u9fa5]{2,4}', text)
        keywords.extend(chinese_chars)
        
        # 常见业务词汇
        business_terms = {
            '用户': ['user', 'login', 'customer'],
            '投注': ['bet', 'wager', 'order'],
            '金额': ['amount', 'money', 'sum'],
            '时间': ['time', 'date', 'bill'],
            '游戏': ['game', 'play'],
            '订单': ['order', 'bill'],
            '平台': ['platform', 'channel'],
            '设备': ['device', 'mobile', 'app'],
            '收入': ['revenue', 'income', 'ggr'],
            '输赢': ['win', 'loss', 'winloss']
        }
        
        for term, synonyms in business_terms.items():
            if term in text:
                keywords.extend(synonyms)
        
        return list(set(keywords))
    
    def search(self, query: str, top_k: int = 10) -> Dict:
        """
        搜索匹配的表和字段
        
        Args:
            query: 用户查询 (自然语言)
            top_k: 返回结果数量
        
        Returns:
            匹配的表和字段列表
        """
        print(f"\n🔍 分析查询：{query}")
        
        # 1. 提取查询关键词
        query_keywords = self._extract_keywords(query)
        print(f"📝 提取关键词：{', '.join(query_keywords[:10])}")
        
        # 2. 字段名匹配
        field_matches = []
        for kw in query_keywords:
            if kw in self.column_index:
                for col in self.column_index[kw]:
                    field_matches.append({
                        'table': col['table_name'],
                        'column': col['column_name'],
                        'type': col['column_type'],
                        'match_type': 'field_name',
                        'score': 1.0
                    })
        
        # 3. 注释关键词匹配
        comment_matches = []
        for kw in query_keywords:
            if kw in self.keyword_index:
                for item in self.keyword_index[kw]:
                    if item['type'] == 'table':
                        comment_matches.append({
                            'table': item['name'],
                            'column': '*',
                            'type': 'table',
                            'match_type': 'table_comment',
                            'score': 0.8
                        })
                    else:
                        comment_matches.append({
                            'table': item['table'],
                            'column': item['column'],
                            'type': 'column',
                            'match_type': 'column_comment',
                            'score': 0.9
                        })
        
        # 4. 合并结果并去重
        all_matches = field_matches + comment_matches
        
        # 按表分组
        table_scores = {}
        for match in all_matches:
            table = match['table']
            if table not in table_scores:
                table_scores[table] = {
                    'table': table,
                    'score': 0,
                    'columns': [],
                    'match_types': set()
                }
            
            table_scores[table]['score'] += match['score']
            table_scores[table]['match_types'].add(match['match_type'])
            
            if match['column'] != '*' and match['column'] not in [c['name'] for c in table_scores[table]['columns']]:
                table_scores[table]['columns'].append({
                    'name': match['column'],
                    'type': match.get('type', 'unknown'),
                    'match_type': match['match_type']
                })
        
        # 5. 排序
        results = sorted(
            table_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:top_k]
        
        # 转换集合为列表
        for r in results:
            r['match_types'] = list(r['match_types'])
        
        return {
            'query': query,
            'keywords': query_keywords[:10],
            'matched_tables': results,
            'total_matches': len(results)
        }
    
    def generate_query_suggestion(self, search_result: Dict, intent: str = 'query') -> str:
        """
        生成查询建议
        
        Args:
            search_result: 搜索结果
            intent: 查询意图 (query/count/sum/detail)
        """
        if not search_result['matched_tables']:
            return "❌ 未找到匹配的表和字段"
        
        tables = search_result['matched_tables']
        primary_table = tables[0]
        
        # 根据意图生成 SQL
        if intent == 'count':
            sql = f"""
-- 查询 {primary_table['table']} 的记录数
SELECT 
    pt,
    COUNT(*) AS cnt
FROM {primary_table['table']}
WHERE pt >= DATE_SUB(GETDATE(), 7)
GROUP BY pt
ORDER BY pt DESC;
"""
        elif intent == 'sum':
            # 找数值字段
            amount_cols = [c for c in primary_table['columns'] 
                          if 'amount' in c['name'].lower() or 'sum' in c['name'].lower()]
            if amount_cols:
                col = amount_cols[0]['name']
                sql = f"""
-- 统计 {primary_table['table']} 的 {col} 总和
SELECT 
    pt,
    SUM(CAST({col} AS DOUBLE)) AS total_{col.lower()}
FROM {primary_table['table']}
WHERE pt >= DATE_SUB(GETDATE(), 7)
GROUP BY pt
ORDER BY pt DESC;
"""
            else:
                sql = f"-- 表 {primary_table['table']} 未找到金额字段"
        
        elif intent == 'detail':
            cols = ', '.join([c['name'] for c in primary_table['columns'][:10]])
            sql = f"""
-- 查询 {primary_table['table']} 的详细数据
SELECT 
    {cols}
FROM {primary_table['table']}
WHERE pt = GETDATE()
LIMIT 100;
"""
        
        else:  # query
            cols = ', '.join([c['name'] for c in primary_table['columns'][:15]])
            sql = f"""
-- 查询 {primary_table['table']}
SELECT 
    {cols}
FROM {primary_table['table']}
WHERE pt >= DATE_SUB(GETDATE(), 7)
LIMIT 1000;
"""
        
        return sql
    
    def interactive_search(self):
        """交互式搜索"""
        print("\n" + "="*60)
        print("🤖 ODPS AI 检索助手")
        print("="*60)
        print("输入查询描述，我会推荐相关的表和字段")
        print("输入 'quit' 退出")
        print("="*60)
        
        while True:
            query = input("\n📝 请输入查询需求：").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 再见!")
                break
            
            if not query:
                continue
            
            # 搜索
            result = self.search(query)
            
            # 显示结果
            self._print_results(result)
            
            # 生成 SQL 建议
            print("\n💡 SQL 查询建议:")
            print("-" * 60)
            sql = self.generate_query_suggestion(result)
            print(sql)


def _print_results(self, result: Dict):
    """打印搜索结果"""
    print("\n" + "="*60)
    print(f"📊 找到 {result['total_matches']} 个匹配的表")
    print("="*60)
    
    for i, table in enumerate(result['matched_tables'], 1):
        print(f"\n{i}. 📁 {table['table']} (匹配度：{table['score']:.2f})")
        print(f"   匹配类型：{', '.join(table['match_types'])}")
        
        if table['columns']:
            print(f"   推荐字段:")
            for col in table['columns'][:5]:
                print(f"     - {col['name']} ({col['type']}) [{col['match_type']}]")


# 绑定方法
ODPSSemanticSearch._print_results = _print_results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS AI 检索工具')
    parser.add_argument('--query', '-q', type=str, help='查询语句')
    parser.add_argument('--metadata-dir', default='odps_metadata', help='元数据目录')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    # 初始化搜索引擎
    try:
        searcher = ODPSSemanticSearch(args.metadata_dir)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n请先运行元数据采集:")
        print("  python odps_metadata_crawler.py")
        return
    
    if args.interactive or not args.query:
        # 交互模式
        searcher.interactive_search()
    else:
        # 单次查询
        result = searcher.search(args.query)
        searcher._print_results(result)
        
        print("\n💡 SQL 查询建议:")
        print("-" * 60)
        sql = searcher.generate_query_suggestion(result)
        print(sql)


if __name__ == '__main__':
    main()
