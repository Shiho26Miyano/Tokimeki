#!/usr/bin/env python3
"""
查看 S3 数据脚本
用于诊断 dashboard 为什么没有数据

用法:
    python scripts/view_s3_data.py                    # 列出所有文件
    python scripts/view_s3_data.py --date 2026-01-26  # 查看特定日期
    python scripts/view_s3_data.py --check-dashboard # 检查dashboard需要的数据
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def list_s3_objects(s3_client, bucket: str, prefix: str = "", max_keys: int = 1000) -> List[Dict]:
    """列出S3对象"""
    objects = []
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix, MaxKeys=max_keys)
        
        for page in pages:
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                objects.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified']
                })
    except Exception as e:
        print(f"❌ Error listing objects: {e}")
    
    return objects

def read_s3_object(s3_client, bucket: str, key: str) -> Any:
    """读取S3对象内容"""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            return None
        raise
    except json.JSONDecodeError:
        return content  # 返回原始内容如果不是JSON

def check_dashboard_data(s3_client, bucket: str, date: str):
    """检查dashboard需要的数据文件"""
    print("\n" + "=" * 80)
    print(f"🔍 检查 Dashboard 数据 (日期: {date})")
    print("=" * 80)
    
    # 需要检查的文件
    required_files = {
        'compute_signals': f"processed-data/{date}/compute-signals.json",
        'learning_signals': f"processed-data/{date}/learning-signals.json",
    }
    
    # 检查原始数据
    raw_data_prefix = f"raw-data/{date}/"
    raw_objects = list_s3_objects(s3_client, bucket, raw_data_prefix)
    
    print(f"\n📊 原始数据 (raw-data/{date}/):")
    if raw_objects:
        print(f"   ✅ 找到 {len(raw_objects)} 个文件")
        # 按ticker分组
        tickers = set()
        for obj in raw_objects:
            parts = obj['key'].split('/')
            if len(parts) >= 3:
                ticker = parts[2]
                tickers.add(ticker)
        print(f"   📈 Tickers: {', '.join(sorted(tickers))}")
        print(f"   📁 示例文件:")
        for obj in raw_objects[:5]:
            print(f"      - {obj['key']} ({format_size(obj['size'])})")
        if len(raw_objects) > 5:
            print(f"      ... 还有 {len(raw_objects) - 5} 个文件")
    else:
        print(f"   ❌ 没有找到原始数据")
        print(f"   💡 提示: 需要先运行数据采集器收集原始数据")
    
    # 检查处理后的数据
    print(f"\n📊 处理后的数据:")
    for file_type, key in required_files.items():
        print(f"\n   {file_type.replace('_', ' ').title()}:")
        print(f"   Key: {key}")
        
        try:
            data = read_s3_object(s3_client, bucket, key)
            if data is None:
                print(f"   ❌ 文件不存在")
            else:
                print(f"   ✅ 文件存在")
                
                if file_type == 'compute_signals':
                    signals = data.get('signals', [])
                    print(f"   📈 Signals数量: {len(signals)}")
                    if signals:
                        tickers = [s.get('ticker') for s in signals]
                        print(f"   📊 Tickers: {', '.join(tickers)}")
                        print(f"   📄 示例数据:")
                        print(f"      {json.dumps(signals[0], indent=6, ensure_ascii=False)}")
                
                elif file_type == 'learning_signals':
                    models = data.get('models', {})
                    print(f"   📈 Models数量: {len(models)}")
                    if models:
                        print(f"   📊 Tickers: {', '.join(models.keys())}")
                        print(f"   📄 示例数据 (第一个ticker):")
                        first_ticker = list(models.keys())[0]
                        print(f"      {json.dumps(models[first_ticker], indent=6, ensure_ascii=False)}")
                
                # 显示文件大小
                obj_info = next((o for o in list_s3_objects(s3_client, bucket, key) if o['key'] == key), None)
                if obj_info:
                    print(f"   💾 文件大小: {format_size(obj_info['size'])}")
                    print(f"   🕐 最后修改: {obj_info['last_modified']}")
        
        except Exception as e:
            print(f"   ❌ 读取错误: {e}")
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 诊断总结")
    print("=" * 80)
    
    compute_data = read_s3_object(s3_client, bucket, required_files['compute_signals'])
    learning_data = read_s3_object(s3_client, bucket, required_files['learning_signals'])
    
    if not raw_objects:
        print("❌ 问题: 没有原始数据")
        print("   💡 解决方案: 启动数据采集器收集原始数据")
    elif compute_data is None:
        print("❌ 问题: Compute Agent 还没有运行或失败")
        print("   💡 解决方案: 检查 Lambda 函数是否正常运行")
        print("   💡 手动触发: 在 AWS Console 中手动触发 Compute Agent Lambda")
    elif learning_data is None:
        print("⚠️  警告: Learning Agent 还没有运行")
        print("   💡 解决方案: Learning Agent 每小时运行一次，请等待")
    else:
        print("✅ 所有必需的数据文件都存在")
        print("   💡 如果 dashboard 仍然没有数据，检查:")
        print("      1. API 端点是否正常工作")
        print("      2. 浏览器控制台是否有错误")
        print("      3. 网络请求是否成功")

def list_all_data(s3_client, bucket: str, prefix: str = ""):
    """列出所有数据"""
    print("\n" + "=" * 80)
    print(f"📂 S3 Bucket: {bucket}")
    print(f"📁 Prefix: {prefix or '(全部)'}")
    print("=" * 80)
    
    objects = list_s3_objects(s3_client, bucket, prefix)
    
    if not objects:
        print("❌ 没有找到文件")
        return
    
    print(f"\n找到 {len(objects)} 个文件:\n")
    
    # 按前缀分组
    groups: Dict[str, List[Dict]] = {}
    for obj in objects:
        key = obj['key']
        # 获取第一级目录
        first_dir = key.split('/')[0] if '/' in key else ''
        if first_dir not in groups:
            groups[first_dir] = []
        groups[first_dir].append(obj)
    
    # 显示分组
    for group_name, group_objects in sorted(groups.items()):
        print(f"📁 {group_name}/ ({len(group_objects)} 个文件)")
        for obj in sorted(group_objects, key=lambda x: x['key'])[:10]:
            size_str = format_size(obj['size'])
            mod_time = obj['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
            print(f"   {obj['key']} ({size_str}, {mod_time})")
        if len(group_objects) > 10:
            print(f"   ... 还有 {len(group_objects) - 10} 个文件")
        print()

def main():
    parser = argparse.ArgumentParser(description='查看 S3 数据')
    parser.add_argument('--date', type=str, help='日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--prefix', type=str, default='', help='S3前缀过滤')
    parser.add_argument('--check-dashboard', action='store_true', help='检查dashboard需要的数据')
    parser.add_argument('--bucket', type=str, help='S3 bucket名称（覆盖环境变量）')
    
    args = parser.parse_args()
    
    # 检查AWS凭证
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("❌ AWS凭证未配置")
            print("   设置环境变量: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 检查AWS凭证失败: {e}")
        sys.exit(1)
    
    # 获取bucket名称
    bucket = args.bucket or os.getenv("AWS_S3_PULSE_BUCKET")
    if not bucket:
        print("❌ S3 bucket名称未设置")
        print("   设置环境变量: AWS_S3_PULSE_BUCKET")
        print("   或使用 --bucket 参数")
        sys.exit(1)
    
    # 初始化S3客户端
    try:
        region = os.getenv("AWS_REGION", "us-east-2")
        s3_client = boto3.client('s3', region_name=region)
        s3_client.head_bucket(Bucket=bucket)
        print(f"✅ 连接到 S3 bucket: {bucket}")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '404':
            print(f"❌ S3 bucket '{bucket}' 不存在")
        else:
            print(f"❌ 无法访问 S3 bucket: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 连接S3失败: {e}")
        sys.exit(1)
    
    # 执行操作
    if args.check_dashboard:
        date = args.date or datetime.now(timezone.utc).date().isoformat()
        check_dashboard_data(s3_client, bucket, date)
    else:
        list_all_data(s3_client, bucket, args.prefix)

if __name__ == "__main__":
    main()
