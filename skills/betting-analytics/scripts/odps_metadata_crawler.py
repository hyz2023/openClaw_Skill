#!/usr/bin/env python3
"""
ODPS 元数据采集工具 (增强版)
- 采集表结构、字段信息、分区信息
- 获取最新有数据的分区
- 支持增量更新
- 每 30 秒汇报进度

环境变量:
export ALIBABA_ACCESSKEY_ID="your_access_key_id"
export ALIBABA_ACCESSKEY_SECRET="your_access_key_secret"
export ALIBABA_ODPS_PROJECT="superengineproject"
export ALIBABA_ODPS_ENDPOINT="http://service.ap-southeast-1.maxcompute.aliyun.com/api"
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from odps import ODPS
import pandas as pd


class ProgressReporter:
    """进度汇报器 - 每 30 秒汇报一次"""
    
    def __init__(self, interval: int = 30):
        self.interval = interval
        self.current_table = ""
        self.processed = 0
        self.total = 0
        self.start_time = None
        self.running = False
        self.thread = None
    
    def start(self, total: int):
        """启动汇报线程"""
        self.total = total
        self.processed = 0
        self.start_time = datetime.now()
        self.running = True
        self.thread = threading.Thread(target=self._report_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止汇报"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def update(self, table_name: str):
        """更新当前处理的表"""
        self.current_table = table_name
        self.processed += 1
    
    def _report_loop(self):
        """汇报循环"""
        while self.running:
            time.sleep(self.interval)
            self._print_progress()
    
    def _print_progress(self):
        """打印进度"""
        if self.total == 0:
            return
        
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        pct = self.processed / self.total * 100
        
        # 估算剩余时间
        if self.processed > 0:
            avg_time = elapsed.total_seconds() / self.processed
            remaining = (self.total - self.processed) * avg_time
            remaining_str = f"{remaining/60:.1f}分钟"
        else:
            remaining_str = "未知"
        
        print(f"\n⏰ [{elapsed_str}] 进度：{self.processed}/{self.total} ({pct:.1f}%)")
        print(f"   当前：{self.current_table}")
        print(f"   预计剩余：{remaining_str}")
        print(f"   处理速度：{self.processed/elapsed.total_seconds()*60:.1f} 表/分钟")
        sys.stdout.flush()


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


def get_partition_data_status(o: ODPS, table_name: str) -> dict:
    """
    获取表的分区数据状态
    返回最新有数据的分区信息
    """
    try:
        table = o.get_table(table_name)
        
        if not table.table_schema.partitions:
            return {
                'is_partitioned': False,
                'latest_partition': None,
                'partition_count': 0,
                'has_data': None
            }
        
        # 获取所有分区
        partitions = list(table.partitions)
        
        if not partitions:
            return {
                'is_partitioned': True,
                'latest_partition': None,
                'partition_count': 0,
                'has_data': False
            }
        
        # 按分区值排序 (假设 pt 格式为 yyyymmdd)
        partition_info = []
        for pt in partitions:
            pt_name = pt.name
            # 提取分区值 (如 pt='20260226')
            if '=' in pt_name:
                pt_value = pt_name.split('=')[1].strip("'\"")
            else:
                pt_value = pt_name
            
            partition_info.append({
                'name': pt_name,
                'value': pt_value,
                'size': pt.size if hasattr(pt, 'size') else 0,
                'records': pt.records if hasattr(pt, 'records') else 0
            })
        
        # 按分区值排序
        partition_info.sort(key=lambda x: x['value'], reverse=True)
        
        # 找到最新有数据的分区
        latest_with_data = None
        for pt in partition_info:
            if pt['records'] > 0 or pt['size'] > 0:
                latest_with_data = pt
                break
        
        return {
            'is_partitioned': True,
            'latest_partition': latest_with_data,
            'all_partitions': partition_info[:10],  # 只保留前 10 个
            'partition_count': len(partitions),
            'has_data': latest_with_data is not None
        }
        
    except Exception as e:
        return {
            'is_partitioned': True,
            'latest_partition': None,
            'partition_count': 0,
            'has_data': None,
            'error': str(e)
        }


def get_table_metadata(o: ODPS, table_name: str, check_partitions: bool = True) -> dict:
    """获取单张表的详细元数据"""
    try:
        table = o.get_table(table_name)
        
        # 基本信息
        metadata = {
            'table_name': table.name,
            'comment': getattr(table, 'comment', ''),
            'create_time': str(table.creation_time) if hasattr(table, 'creation_time') else None,
            'last_modified_time': str(table.last_data_modified_time) if hasattr(table, 'last_data_modified_time') else None,
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
        
        # 分区信息 (可选，耗时)
        if check_partitions:
            partition_status = get_partition_data_status(o, table_name)
            metadata['partition_status'] = partition_status
        else:
            metadata['partition_status'] = {
                'is_partitioned': False,
                'latest_partition': None
            }
        
        return metadata
        
    except Exception as e:
        print(f"⚠️  获取表 {table_name} 元数据失败：{e}")
        return None


def load_existing_metadata(output_dir: str) -> dict:
    """加载已有的元数据 (用于增量更新)"""
    latest_json = Path(output_dir) / 'metadata_latest.json'
    
    if not latest_json.exists():
        return None
    
    try:
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ 加载已有元数据：{data.get('table_count', 0)} 张表")
            return data
    except:
        return None


def crawl_all_metadata(o: ODPS, output_dir: str = 'odps_metadata', incremental: bool = True):
    """
    采集所有表的元数据
    
    Args:
        o: ODPS 连接
        output_dir: 输出目录
        incremental: 是否增量更新
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取所有表
    table_names = list_all_tables(o)
    
    # 加载已有元数据 (增量模式)
    existing_data = None
    if incremental:
        existing_data = load_existing_metadata(output_dir)
    
    all_metadata = []
    failed_tables = []
    updated_tables = 0
    unchanged_tables = 0
    
    # 构建已有元数据的索引
    existing_index = {}
    if existing_data and 'tables' in existing_data:
        for table in existing_data['tables']:
            existing_index[table['table_name']] = table
    
    # 初始化进度汇报
    reporter = ProgressReporter(interval=30)
    reporter.start(len(table_names))
    
    start_time = datetime.now()
    
    # 逐表采集
    for i, table_name in enumerate(table_names, 1):
        reporter.update(table_name)
        
        # 增量检查
        if incremental and table_name in existing_index:
            existing_table = existing_index[table_name]
            
            # 检查是否需要更新 (表大小变化或最后修改时间变化)
            # 简单策略：每次都更新分区信息，其他信息如果表大小没变就跳过
            try:
                current_table = o.get_table(table_name)
                current_size = current_table.size if hasattr(current_table, 'size') else 0
                existing_size = existing_table.get('size', 0)
                
                # 如果表大小没变，且已有分区信息，跳过
                if current_size == existing_size and existing_table.get('partition_status', {}).get('latest_partition'):
                    all_metadata.append(existing_table)
                    unchanged_tables += 1
                    continue
                else:
                    # 需要更新
                    print(f"  📝 表有更新，重新采集：{table_name}")
            except:
                pass
        
        # 采集元数据 (检查分区)
        metadata = get_table_metadata(o, table_name, check_partitions=True)
        
        if metadata:
            all_metadata.append(metadata)
            updated_tables += 1
            
            # 每采集 50 张表保存一次进度
            if i % 50 == 0:
                save_incremental_progress(output_path, all_metadata, failed_tables, i, len(table_names))
        else:
            failed_tables.append(table_name)
    
    # 停止进度汇报
    reporter.stop()
    
    # 最终统计
    elapsed = datetime.now() - start_time
    elapsed_str = str(elapsed).split('.')[0]
    
    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. JSON 格式 (完整元数据)
    json_file = output_path / f'metadata_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'project': os.getenv('ALIBABA_ODPS_PROJECT'),
            'crawl_time': timestamp,
            'crawl_duration': elapsed_str,
            'table_count': len(all_metadata),
            'updated_tables': updated_tables,
            'unchanged_tables': unchanged_tables,
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
    
    # 3. 创建最新元数据的链接
    latest_json = output_path / 'metadata_latest.json'
    latest_csv = output_path / 'columns_latest.csv'
    
    if latest_json.exists():
        latest_json.unlink()
    if latest_csv.exists():
        latest_csv.unlink()
    
    import shutil
    shutil.copy(json_file, latest_json)
    shutil.copy(csv_file, latest_csv)
    
    print(f"✅ 最新元数据链接已创建")
    
    # 4. 统计摘要
    partitioned_tables = sum(1 for t in all_metadata if t.get('partition_status', {}).get('is_partitioned'))
    tables_with_data = sum(1 for t in all_metadata if t.get('partition_status', {}).get('has_data'))
    
    summary = {
        'project': os.getenv('ALIBABA_ODPS_PROJECT'),
        'crawl_time': timestamp,
        'crawl_duration': elapsed_str,
        'total_tables': len(all_metadata),
        'total_columns': sum(t['column_count'] for t in all_metadata),
        'partitioned_tables': partitioned_tables,
        'tables_with_data': tables_with_data,
        'updated_tables': updated_tables,
        'unchanged_tables': unchanged_tables,
        'failed_tables': failed_tables,
        'top_tables_by_columns': sorted(
            [(t['table_name'], t['column_count']) for t in all_metadata],
            key=lambda x: x[1],
            reverse=True
        )[:10],
        'tables_with_latest_partition': [
            {
                'table': t['table_name'],
                'latest_partition': t['partition_status'].get('latest_partition', {}).get('value'),
                'has_data': t['partition_status'].get('has_data')
            }
            for t in all_metadata[:20]  # 只显示前 20 个
        ]
    }
    
    summary_file = output_path / f'summary_{timestamp}.json'
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 统计摘要已保存：{summary_file}")
    
    # 打印摘要
    print("\n" + "="*70)
    print("📊 元数据采集完成")
    print("="*70)
    print(f"项目：{summary['project']}")
    print(f"采集时间：{timestamp}")
    print(f"耗时：{elapsed_str}")
    print(f"总表数：{summary['total_tables']}")
    print(f"总字段数：{summary['total_columns']}")
    print(f"分区表数：{partitioned_tables}")
    print(f"有数据的表：{tables_with_data}")
    print(f"更新表数：{updated_tables}")
    print(f"跳过表数：{unchanged_tables}")
    
    if failed_tables:
        print(f"\n⚠️  失败的表 ({len(failed_tables)}):")
        for t in failed_tables[:10]:
            print(f"  - {t}")
    
    print("\n📁 输出文件:")
    print(f"  - {json_file}")
    print(f"  - {csv_file}")
    print(f"  - {summary_file}")
    
    return all_metadata


def save_incremental_progress(output_path: Path, all_metadata: list, failed_tables: list, 
                              current: int, total: int):
    """保存增量进度"""
    temp_file = output_path / 'metadata_progress.json'
    
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump({
            'progress': f"{current}/{total}",
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'tables': all_metadata,
            'failed_tables': failed_tables
        }, f, ensure_ascii=False, indent=2)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ODPS 元数据采集工具')
    parser.add_argument('--output', default='odps_metadata', help='输出目录')
    parser.add_argument('--full', action='store_true', help='全量采集 (不增量)')
    parser.add_argument('--no-partition-check', action='store_true', help='跳过分区检查')
    
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
    crawl_all_metadata(
        o, 
        args.output, 
        incremental=not args.full
    )


if __name__ == '__main__':
    main()
