#!/usr/bin/env python3
"""
监控数据收集器状态
实时显示数据收集进度和 S3 写入情况
"""
import os
import sys
import time
import boto3
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from app.services.marketpulse.pulse_service import MarketPulseService
except ImportError:
    print("❌ 无法导入 MarketPulseService")
    sys.exit(1)

def count_s3_files(bucket: str, prefix: str) -> int:
    """统计 S3 中指定前缀的文件数量"""
    try:
        s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "us-east-2"))
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
        
        count = 0
        for page in pages:
            if 'Contents' in page:
                count += len(page['Contents'])
        return count
    except Exception as e:
        return -1  # 错误时返回 -1

def monitor_collection(duration: int = 60, interval: int = 5):
    """监控数据收集"""
    print("=" * 80)
    print("📊 Market Pulse 数据收集监控")
    print("=" * 80)
    print()
    
    # 检查环境变量
    s3_bucket = os.getenv("AWS_S3_PULSE_BUCKET")
    if not s3_bucket:
        print("❌ AWS_S3_PULSE_BUCKET 未设置")
        return
    
    # 获取服务实例（如果正在运行）
    try:
        service = MarketPulseService()
        stats = service.data_collector.get_collection_stats()
        
        print(f"✅ 数据收集器状态:")
        print(f"   运行中: {'是' if service.started else '否'}")
        print(f"   WebSocket 连接: {'✅' if stats.get('websocket_connected') else '❌'}")
        print(f"   已收集数据条数: {stats.get('bars_collected', 0)}")
        print()
    except Exception as e:
        print(f"⚠️  无法获取服务状态: {e}")
        print("   数据收集器可能未运行")
        print()
    
    # 获取今天的日期
    today = datetime.now(timezone.utc).date().isoformat()
    prefix = f"raw-data/{today}/"
    
    print(f"📁 检查 S3 数据: s3://{s3_bucket}/{prefix}")
    print()
    
    # 初始计数
    initial_count = count_s3_files(s3_bucket, prefix)
    if initial_count >= 0:
        print(f"📊 当前 S3 文件数: {initial_count}")
    else:
        print("⚠️  无法访问 S3（可能是权限问题）")
    
    print()
    print(f"⏱️  监控 {duration} 秒，每 {interval} 秒更新一次...")
    print("   按 Ctrl+C 停止")
    print()
    print("-" * 80)
    
    start_time = time.time()
    last_count = initial_count
    last_bars = stats.get('bars_collected', 0) if 'stats' in locals() else 0
    
    try:
        while time.time() - start_time < duration:
            time.sleep(interval)
            
            # 获取当前统计
            try:
                current_stats = service.data_collector.get_collection_stats()
                current_bars = current_stats.get('bars_collected', 0)
            except:
                current_bars = last_bars
            
            # 统计 S3 文件
            current_count = count_s3_files(s3_bucket, prefix)
            
            # 计算增量
            bars_delta = current_bars - last_bars
            files_delta = current_count - last_count if current_count >= 0 else 0
            
            # 显示状态
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ", end="")
            
            if current_count >= 0:
                print(f"S3: {current_count} 文件 (+{files_delta}) | ", end="")
            else:
                print(f"S3: 无法访问 | ", end="")
            
            print(f"内存: {current_bars} 条 (+{bars_delta}) | ", end="")
            
            if bars_delta > 0:
                print("✅ 正在收集数据")
            elif current_bars > 0:
                print("⏸️  数据收集暂停")
            else:
                print("⏳ 等待数据...")
            
            last_count = current_count
            last_bars = current_bars
            
    except KeyboardInterrupt:
        print()
        print()
        print("-" * 80)
    
    # 最终统计
    print()
    print("=" * 80)
    print("📊 最终统计")
    print("=" * 80)
    
    try:
        final_stats = service.data_collector.get_collection_stats()
        print(f"内存中的数据条数: {final_stats.get('bars_collected', 0)}")
        if final_stats.get('last_bar_time'):
            print(f"最后数据时间: {final_stats.get('last_bar_time')}")
    except:
        pass
    
    final_count = count_s3_files(s3_bucket, prefix)
    if final_count >= 0:
        print(f"S3 中的文件数: {final_count}")
        if initial_count >= 0:
            total_added = final_count - initial_count
            print(f"本次监控新增: {total_added} 个文件")
    
    print()
    print("💡 提示:")
    print(f"   - 查看 S3 数据: aws s3 ls s3://{s3_bucket}/{prefix} --recursive")
    print(f"   - 运行诊断: python scripts/diagnose_data_collection.py --date {today}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='监控数据收集器')
    parser.add_argument('--duration', type=int, default=60, help='监控时长（秒）')
    parser.add_argument('--interval', type=int, default=5, help='更新间隔（秒）')
    
    args = parser.parse_args()
    
    monitor_collection(duration=args.duration, interval=args.interval)
