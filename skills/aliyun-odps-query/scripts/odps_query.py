#!/usr/bin/env python3
"""
阿里云 ODPS/MaxCompute 查询工具

功能:
- 列出项目中的所有表
- 查看表结构和元数据
- 执行 SQL 查询
- 导出查询结果

使用示例:
    python scripts/odps_query.py --action list --project my_project
    python scripts/odps_query.py --action describe --project my_project --table user_info
    python scripts/odps_query.py --action query --project my_project --sql "SELECT * FROM table LIMIT 10"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from odps import ODPS
    from odps.models import Table
except ImportError:
    print("请安装 ODPS 库：pip install odps")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("请安装 pandas: pip install pandas")
    pandas = None


class ODPSQuery:
    """ODPS 查询工具类"""
    
    def __init__(
        self,
        access_id: Optional[str] = None,
        access_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        project: Optional[str] = None
    ):
        """
        初始化 ODPS 连接
        
        Args:
            access_id: 阿里云 AccessKey ID
            access_key: 阿里云 AccessKey Secret
            endpoint: ODPS 服务端点
            project: ODPS 项目名称
        """
        # 从参数或环境变量获取配置
        self.access_id = access_id or os.getenv('ALIBABA_ACCESSKEY_ID')
        self.access_key = access_key or os.getenv('ALIBABA_ACCESSKEY_SECRET')
        self.endpoint = endpoint or os.getenv('ALIBABA_ODPS_ENDPOINT', 'http://service.odps.aliyun.com/api')
        self.project = project or os.getenv('ALIBABA_ODPS_PROJECT')
        
        # 验证必需参数
        if not self.access_id:
            raise ValueError("缺少 AccessKey ID，请设置 ALIBABA_ACCESSKEY_ID 环境变量或使用 --access-id 参数")
        if not self.access_key:
            raise ValueError("缺少 AccessKey Secret，请设置 ALIBABA_ACCESSKEY_SECRET 环境变量或使用 --access-key 参数")
        if not self.project:
            raise ValueError("缺少项目名称，请使用 --project 参数或设置 ALIBABA_ODPS_PROJECT 环境变量")
        
        # 初始化 ODPS 客户端
        self.client = ODPS(
            access_id=self.access_id,
            secret_access_key=self.access_key,
            endpoint=self.endpoint,
            project=self.project
        )
        
    def list_tables(self, pattern: Optional[str] = None) -> List[Dict]:
        """
        列出项目中的所有表
        
        Args:
            pattern: 表名匹配模式 (支持通配符)
            
        Returns:
            表信息列表
        """
        tables = []
        
        try:
            for table in self.client.list_tables():
                table_info = {
                    'name': table.name,
                    'project': table.project,
                    'created_time': str(table.creation_time) if hasattr(table, 'creation_time') else 'N/A',
                    'is_virtual_view': getattr(table, 'is_virtual_view', False),
                }
                
                # 尝试获取表大小
                try:
                    table.reload()
                    table_info['size'] = getattr(table, 'size', 0)
                except:
                    table_info['size'] = 0
                
                # 过滤
                if pattern and pattern.lower() not in table.name.lower():
                    continue
                
                tables.append(table_info)
            
        except Exception as e:
            print(f"❌ 获取表列表失败：{e}")
            return []
        
        # 按表名排序
        tables.sort(key=lambda x: x['name'])
        return tables
    
    def describe_table(self, table_name: str) -> Dict:
        """
        查看表结构
        
        Args:
            table_name: 表名
            
        Returns:
            表结构信息
        """
        try:
            table = self.client.get_table(table_name)
            table.reload()
            
            # 获取字段信息
            schema = table.schema
            columns = []
            
            for col in schema.columns:
                col_info = {
                    'name': col.name,
                    'type': str(col.type),
                    'comment': getattr(col, 'comment', ''),
                    'label': getattr(col, 'label', ''),
                }
                columns.append(col_info)
            
            # 获取分区信息
            partitions = []
            if schema.partitions:
                for pt in schema.partitions:
                    partitions.append({
                        'name': pt.name,
                        'type': str(pt.type),
                        'comment': getattr(pt, 'comment', ''),
                    })
            
            # 表基本信息
            table_info = {
                'name': table.name,
                'project': table.project,
                'comment': getattr(table, 'comment', ''),
                'created_time': str(table.creation_time) if hasattr(table, 'creation_time') else 'N/A',
                'last_modified_time': str(table.last_data_modified_time) if hasattr(table, 'last_data_modified_time') else 'N/A',
                'size': getattr(table, 'size', 0),
                'lifecycle': getattr(table, 'lifecycle', 0),
                'is_virtual_view': getattr(table, 'is_virtual_view', False),
                'columns': columns,
                'partitions': partitions,
            }
            
            return table_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def execute_query(
        self,
        sql: str,
        limit: int = 100,
        project: Optional[str] = None
    ) -> Dict:
        """
        执行 SQL 查询
        
        Args:
            sql: SQL 语句
            limit: 结果行数限制
            project: 项目名称 (可选，覆盖默认项目)
            
        Returns:
            查询结果
        """
        # 验证 SQL (仅允许 SELECT)
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith('SELECT'):
            return {'error': '仅支持 SELECT 查询语句'}
        
        try:
            # 执行查询
            query_project = project or self.project
            instance = self.client.execute_sql(sql, project=query_project)
            
            # 等待查询完成
            instance.wait_for_success()
            
            # 获取结果
            with self.client.open_reader(instance.id) as reader:
                # 获取列名
                columns = [col.name for col in reader.schema.columns]
                
                # 获取数据
                rows = []
                count = 0
                for record in reader:
                    if limit and count >= limit:
                        break
                    row = {columns[i]: record[i] for i in range(len(columns))}
                    rows.append(row)
                    count += 1
                
                return {
                    'success': True,
                    'columns': columns,
                    'data': rows,
                    'count': len(rows),
                    'sql': sql,
                }
                
        except Exception as e:
            return {'error': str(e), 'sql': sql}
    
    def export_results(
        self,
        data: List[Dict],
        output_format: str = 'csv',
        output_file: Optional[str] = None
    ) -> Optional[str]:
        """
        导出查询结果
        
        Args:
            data: 数据列表
            output_format: 输出格式 (csv/json/excel)
            output_file: 输出文件路径
            
        Returns:
            输出文件路径或内容
        """
        if not data:
            return None
        
        if output_format == 'json':
            content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                return output_file
            return content
        
        elif output_format == 'csv' and pandas is not None:
            df = pd.DataFrame(data)
            if output_file:
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                return output_file
            return df.to_csv(index=False, encoding='utf-8-sig')
        
        elif output_format == 'excel' and pandas is not None:
            df = pd.DataFrame(data)
            if not output_file:
                output_file = f"odps_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')
            return output_file
        
        else:
            return str(data)


def format_table_list(tables: List[Dict]) -> str:
    """格式化表列表输出"""
    if not tables:
        return "未找到任何表"
    
    lines = []
    lines.append(f"📊 项目：{tables[0].get('project', 'N/A')}")
    lines.append(f"找到 {len(tables)} 张表\n")
    lines.append(f"{'表名':<40} {'创建时间':<20} {'大小 (MB)':<12}")
    lines.append("-" * 72)
    
    for table in tables:
        name = table.get('name', 'N/A')[:38]
        created = table.get('created_time', 'N/A')[:19] if table.get('created_time') else 'N/A'
        size_mb = table.get('size', 0) / (1024 * 1024)
        size_str = f"{size_mb:.2f}" if size_mb > 0 else "N/A"
        
        lines.append(f"{name:<40} {created:<20} {size_str:<12}")
    
    return "\n".join(lines)


def format_table_schema(schema: Dict) -> str:
    """格式化表结构输出"""
    if 'error' in schema:
        return f"❌ 错误：{schema['error']}"
    
    lines = []
    lines.append(f"📋 表结构：{schema.get('project', 'N/A')}.{schema.get('name', 'N/A')}")
    
    if schema.get('comment'):
        lines.append(f"注释：{schema['comment']}")
    
    lines.append(f"\n基本信息:")
    lines.append(f"  创建时间：{schema.get('created_time', 'N/A')}")
    lines.append(f"  最后修改：{schema.get('last_modified_time', 'N/A')}")
    size_mb = schema.get('size', 0) / (1024 * 1024)
    lines.append(f"  表大小：{size_mb:.2f} MB" if size_mb > 0 else "  表大小：N/A")
    lines.append(f"  生命周期：{schema.get('lifecycle', 0)} 天" if schema.get('lifecycle') else "  生命周期：永久")
    
    # 字段信息
    columns = schema.get('columns', [])
    if columns:
        lines.append(f"\n字段 ({len(columns)}列):")
        lines.append(f"{'字段名':<30} {'类型':<20} {'注释':<30}")
        lines.append("-" * 80)
        
        for col in columns:
            name = col.get('name', 'N/A')[:28]
            col_type = col.get('type', 'N/A')[:18]
            comment = col.get('comment', '')[:28]
            lines.append(f"{name:<30} {col_type:<20} {comment:<30}")
    
    # 分区信息
    partitions = schema.get('partitions', [])
    if partitions:
        lines.append(f"\n分区 ({len(partitions)}列):")
        lines.append(f"{'分区名':<30} {'类型':<20} {'注释':<30}")
        lines.append("-" * 80)
        
        for pt in partitions:
            name = pt.get('name', 'N/A')[:28]
            pt_type = pt.get('type', 'N/A')[:18]
            comment = pt.get('comment', '')[:28]
            lines.append(f"{name:<30} {pt_type:<20} {comment:<30}")
    
    return "\n".join(lines)


def format_query_result(result: Dict) -> str:
    """格式化查询结果输出"""
    if 'error' in result:
        return f"❌ 查询失败：{result['error']}\nSQL: {result.get('sql', 'N/A')}"
    
    if not result.get('success'):
        return "❌ 查询执行失败"
    
    lines = []
    lines.append(f"✅ 查询成功")
    lines.append(f"返回 {result.get('count', 0)} 行\n")
    
    # 表格形式显示
    data = result.get('data', [])
    if data:
        columns = result.get('columns', [])
        
        # 计算列宽
        col_widths = {}
        for col in columns:
            col_widths[col] = len(col)
            for row in data:
                val_len = len(str(row.get(col, '')))
                col_widths[col] = max(col_widths[col], val_len)
        
        # 表头
        header = " | ".join(col.ljust(col_widths[col]) for col in columns)
        lines.append(header)
        lines.append("-" * len(header))
        
        # 数据行
        for row in data:
            row_str = " | ".join(str(row.get(col, '')).ljust(col_widths[col]) for col in columns)
            lines.append(row_str)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='阿里云 ODPS 查询工具')
    parser.add_argument('--action', type=str, required=True,
                        choices=['list', 'describe', 'query'],
                        help='操作类型：list(列表)/describe(描述)/query(查询)')
    parser.add_argument('--project', type=str, required=True,
                        help='ODPS 项目名称')
    parser.add_argument('--table', type=str, default=None,
                        help='表名 (describe 操作需要)')
    parser.add_argument('--sql', type=str, default=None,
                        help='SQL 语句 (query 操作需要)')
    parser.add_argument('--limit', type=int, default=100,
                        help='结果行数限制 (默认 100)')
    parser.add_argument('--output', type=str, default='table',
                        choices=['table', 'csv', 'json', 'excel'],
                        help='输出格式')
    parser.add_argument('--output-file', type=str, default=None,
                        help='输出文件路径')
    parser.add_argument('--access-id', type=str, default=None,
                        help='AccessKey ID (覆盖环境变量)')
    parser.add_argument('--access-key', type=str, default=None,
                        help='AccessKey Secret (覆盖环境变量)')
    parser.add_argument('--endpoint', type=str, default=None,
                        help='ODPS Endpoint (覆盖环境变量)')
    parser.add_argument('--pattern', type=str, default=None,
                        help='表名匹配模式 (list 操作使用)')
    
    args = parser.parse_args()
    
    # 初始化 ODPS 连接
    try:
        odps = ODPSQuery(
            access_id=args.access_id,
            access_key=args.access_key,
            endpoint=args.endpoint,
            project=args.project
        )
        print(f"✅ 已连接到 ODPS 项目：{args.project}\n")
    except Exception as e:
        print(f"❌ 连接失败：{e}")
        sys.exit(1)
    
    # 执行操作
    if args.action == 'list':
        tables = odps.list_tables(pattern=args.pattern)
        output = format_table_list(tables)
        print(output)
        
    elif args.action == 'describe':
        if not args.table:
            print("❌ describe 操作需要指定 --table 参数")
            sys.exit(1)
        
        schema = odps.describe_table(args.table)
        output = format_table_schema(schema)
        print(output)
        
    elif args.action == 'query':
        if not args.sql:
            print("❌ query 操作需要指定 --sql 参数")
            sys.exit(1)
        
        result = odps.execute_query(args.sql, limit=args.limit, project=args.project)
        
        # 导出结果
        if args.output in ['csv', 'json', 'excel'] and result.get('success'):
            output_file = args.output_file or f"odps_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.output}"
            saved_file = odps.export_results(
                result.get('data', []),
                output_format=args.output,
                output_file=output_file
            )
            print(f"✅ 结果已导出到：{saved_file}")
        else:
            output = format_query_result(result)
            print(output)


if __name__ == "__main__":
    main()
