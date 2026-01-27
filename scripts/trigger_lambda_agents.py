#!/usr/bin/env python3
"""
手动触发 Compute Agent 和 Learning Agent Lambda 函数

用法:
    python scripts/trigger_lambda_agents.py                    # 触发两个agent（使用今天日期）
    python scripts/trigger_lambda_agents.py --compute           # 只触发 Compute Agent
    python scripts/trigger_lambda_agents.py --learning          # 只触发 Learning Agent
    python scripts/trigger_lambda_agents.py --date 2026-01-26   # 指定日期
"""
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

# Lambda 函数名称（可以从环境变量覆盖）
COMPUTE_FUNCTION_NAME = os.getenv("COMPUTE_FUNCTION_NAME", "market-pulse-compute-agent")
LEARNING_FUNCTION_NAME = os.getenv("LEARNING_FUNCTION_NAME", "market-pulse-learning-agent")

def trigger_lambda(function_name: str, payload: dict, region: str = "us-east-2") -> dict:
    """触发 Lambda 函数"""
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        
        # 直接触发 Lambda（不先检查函数是否存在，避免需要 lambda:GetFunction 权限）
        print(f"⚡ 触发 {function_name}...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',  # 同步调用
            Payload=json.dumps(payload)
        )
        
        # 读取响应
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            # 检查是否有函数错误
            if 'FunctionError' in response:
                print(f"❌ {function_name} 执行失败")
                error_type = response.get('FunctionError', 'Unknown')
                print(f"   错误类型: {error_type}")
                if isinstance(response_payload, dict):
                    error_message = response_payload.get('errorMessage', 'Unknown error')
                    error_type = response_payload.get('errorType', 'Unknown')
                    print(f"   错误: {error_type}: {error_message}")
                else:
                    print(f"   响应: {response_payload}")
                return response_payload
            else:
                print(f"✅ {function_name} 执行完成")
                return response_payload
        else:
            print(f"❌ {function_name} 执行失败")
            print(f"   状态码: {response['StatusCode']}")
            if 'FunctionError' in response:
                print(f"   错误: {response['FunctionError']}")
            return response_payload
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        
        if error_code == 'ResourceNotFoundException':
            print(f"❌ Lambda 函数不存在: {function_name}")
            print("   请先部署 Lambda 函数")
        elif error_code == 'AccessDeniedException':
            print(f"❌ 权限不足: 无法调用 Lambda 函数 {function_name}")
            print(f"   需要权限: lambda:InvokeFunction")
            print(f"   错误详情: {error_message}")
        else:
            print(f"❌ 调用 Lambda 函数失败: {error_code}")
            print(f"   错误: {error_message}")
        return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='手动触发 Lambda Agents')
    parser.add_argument('--compute', action='store_true', help='只触发 Compute Agent')
    parser.add_argument('--learning', action='store_true', help='只触发 Learning Agent')
    parser.add_argument('--date', type=str, help='日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--region', type=str, default='us-east-2', help='AWS 区域，默认 us-east-2')
    
    args = parser.parse_args()
    
    # 默认日期（今天）
    date = args.date or datetime.now(timezone.utc).date().isoformat()
    
    # 确定要触发的函数
    trigger_compute = args.compute
    trigger_learning = args.learning
    
    # 如果都没有指定，默认触发两个
    if not trigger_compute and not trigger_learning:
        trigger_compute = True
        trigger_learning = True
    
    print("🚀 手动触发 Lambda Agents")
    print("=" * 60)
    print(f"日期: {date}")
    print(f"区域: {args.region}")
    print()
    
    # 检查 AWS 凭证
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("❌ AWS 凭证未配置")
            print("   设置环境变量: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 检查 AWS 凭证失败: {e}")
        sys.exit(1)
    
    # Payload
    payload = {"date": date}
    
    results = {}
    
    # 触发 Compute Agent
    if trigger_compute:
        print(f"\n{'='*60}")
        result = trigger_lambda(COMPUTE_FUNCTION_NAME, payload, args.region)
        if result:
            results['compute'] = result
            print("\n响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 触发 Learning Agent
    if trigger_learning:
        print(f"\n{'='*60}")
        result = trigger_lambda(LEARNING_FUNCTION_NAME, payload, args.region)
        if result:
            results['learning'] = result
            print("\n响应:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 总结
    print(f"\n{'='*60}")
    if results:
        print("✅ 完成！")
        print()
        print("💡 提示:")
        print(f"   - 检查 S3 数据: python3 scripts/view_s3_data.py --check-dashboard --date {date}")
        print(f"   - 查看 Compute Agent 日志: aws logs tail /aws/lambda/{COMPUTE_FUNCTION_NAME} --follow --region {args.region}")
        print(f"   - 查看 Learning Agent 日志: aws logs tail /aws/lambda/{LEARNING_FUNCTION_NAME} --follow --region {args.region}")
    else:
        print("❌ 没有成功触发任何函数")
        sys.exit(1)

if __name__ == "__main__":
    main()
