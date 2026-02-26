#!/usr/bin/env python3
"""
ODPS 元数据采集工具
采集所有表结构、字段信息、分区信息，保存到本地

环境变量:
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"
"""

import os
import json
from datetime import datetime
from pathlib import Path
from odps import ODPS
import pandas as pd


def connect_odps():
    """连接 ODPS"""
    access_id = os.getenv('ALIBABA_ACCESSKEY_ID')
    access_key = os.getenv('ALIBABA_ACCESSKEY_SECRET')
    project = os.getenv('ALIBABA_ODPS_PROJECT', 'superengineproject')
    endpoint = os.getenv('ALIBABA_ODPS_ENDPOINT', 'http://service.ap-southeast-1.maxcompute.aliyun.com/api')
    
    print(f"连接 ODPS 项目：{project}")
    
    return ODPS(
        access_id=access_id,
        secret_access_key=access_key,
        project=project,
        endpoint=endpoint
    )


def list_all_tables(o: ODPS) -> list:
    """列出所有表"""
    print("\n📋 获取表列表...")
    tables = []
    
    for table in o.list_tables():
        tables.append(table.name)
    
    print(f"找到 {len(tables)} 张表")
    return tables


def get_table_metadata(o: ODPS, table_name: str) -> dict:
    """获取单张表的详细元数据"""
    try:
        table = o.get_table(table_name)
        
        # 基本信息
        metadata = {
            'table_name': table.name,
            'comment': getattr(table, 'comment', ''),
            'create_time': str(table.creation_time) if hasattr(table, 'creation_time') else None,
            'last_modified_time': str(table.last_modified_time) if hasattr(table, 'last_modified_time') else None,
            'size': table.size if hasattr(table, 'size') else None,
            'is_virtual_view': getattr(table, 'is_virtual_view', False),
            'lifecycle': getattr(table, 'lifecycle', None)
        }
        
        # 字段信息
        columns = []
        for col in table.table_schema.columns:
            col_info = {
                'name': col.name,
                'type': str(col.type),
                'comment': getattr(col, 'comment', ''),
                'is_nullable': getattr(col, 'is_nullable', True)
            }
            columns.append(col_info)
        
        metadata['columns'] = columns
        metadata['column_count'] = len(columns)
        
        # 分区信息
        partitions = []
        if table.table_schema.partitions:
            for pt in table.table_schema.partitions:
                pt_info = {
                    'name': pt.name,
                    'type': str(pt.type),
                    'comment': getattr(pt, 'comment', '')
                }
                partitions.append(pt_info)
        
        metadata['partitions'] = partitions
        metadata['is_partitioned'] = len(partitions) > 0
        
        return metadata
        
    except Exception as e:
        print(f"⚠️  获取表 {table_name} 元数据失败：{e}")
        return None


def crawl_all_metadata(o: ODPS, output_dir: str = 'odps_metadata'):
    """采集所有表的元数据"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取所有表
    table_names = list_all_tables(o)
    
    all_metadata = []
    failed_tables = []
    
    # 逐表采集
    for i, table_name in enumerate(table_names, 1):
        print(f"[{i}/{len(table_names)}] 采集 {table_name}...")
        
        metadata = get_table_metadata(o, table_name)
        
        if metadata:
            all_metadata.append(metadata)
        else:
            failed_tables.append(table_name)
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. JSON 格式 (完整元数据)
    json_file = output_path / f'metadata_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'project': os.getenv('ALIBABA_ODPS_PROJECT'),
            'crawl_time': timestamp,
            'table_count': len(all_metadata),
            'failed_tables': failed_tables,
            'tables': all_metadata
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完整元数据已保存：{json_file}")
    
    # 2. CSV 格式 (字段清单)
    all_columns = []
    for table in all_metadata:
        for col in table['columns']:
            all_columns.append({
                'table_name': table['table_name'],
                'column_name': col['name'],
                'column_type': col['type'],
                'comment': col['comment'],
                'is_nullable': col['is_nullable']
            })
    
    csv_file = output_path / f'columns_{timestamp}.csv'
    df = pd.DataFrame(all_columns)
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    print(f"✅ 字段清单已保存：{csv_file}")
    
    # 3. 创建最新元数据的符号链接
    latest_json = output_path / 'metadata_latest.json'
    latest_csv = output_path / 'columns_latest.csv'
    
    if latest_json.exists():
        latest_json.unlink()
    if latest_csv.exists():
        latest_csv.unlink()
    
    # 复制文件作为 latest
    import shutil
    shutil.copy(json_file, latest_json)
    shutil.copy(csv_file, latest_csv)
    
    print(f"✅ 最新元数据链接已创建")
    
    # 4. 统计摘要
    summary = {
        'project': os.getenv('ALIBABA_ODPS_PROJECT'),
        'crawl_time': timestamp,
        'total_tables': len(all_metadata),
        'total_columns': sum(t['column_count'] for t in all_metadata),
        'partitioned_tables': sum(1 for t in all_metadata if t['is_partitioned']),
        'failed_tables': failed_tables,
        'top_tables_by_columns': sorted(
            [(t['table_name'], t['column_count']) for t in all_metadata],
            key=lambda x: x[1],
            reverse=True
        )[:10]
    }
    
    summary_file = output_path / f'summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 统计摘要已保存：{summary_file}")
    
    # 打印摘要
    print("\n" + "="*60)
    print("📊 元数据采集摘要")
    print("="*60)
    print(f"项目：{summary['project']}")
    print(f"采集时间：{timestamp}")
    print(f"总表数：{summary['total_tables']}")
    print(f"总字段数：{summary['total_columns']}")
    print(f"分区表数：{summary['partitioned_tables']}")
    
    if failed_tables:
        print(f"\n⚠️  失败的表 ({len(failed_tables)}):")
        for t in failed_tables[:10]:
            print(f"  - {t}")
    
    print("\n📁 输出文件:")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    print(f"  - {summary_file}")
    
    return all_metadata


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS 元数据采集工具')
    parser.add_argument('--output', default='odps_metadata', help='输出目录')
    
    args = parser.parse_args()
    
    # 检查配置
    if not os.getenv('ALIBABA_ACCESSKEY_ID'):
        print("❌ 缺少 ODPS 配置环境变量")
        print("请设置:")
        print("  export ALIBABA_ACCESSKEY_ID='...'")
        print("  export ALIBABA_ACCESSKEY_SECRET='...'")
        print("  export ALIBABA_ODPS_PROJECT='...'")
        return
    
    # 连接并采集
    o = connect_odps()
    crawl_all_metadata(o, args.output)


if __name__ == '__main__':
    main()
