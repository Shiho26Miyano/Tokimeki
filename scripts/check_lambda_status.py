#!/usr/bin/env python3
"""
检查 Lambda 函数状态和触发它们

用法:
    python scripts/check_lambda_status.py                    # 检查状态
    python scripts/check_lambda_status.py --trigger         # 检查并触发
    python scripts/check_lambda_status.py --trigger --compute # 只触发 Compute Agent
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

def check_lambda_function(function_name: str, region: str = "us-east-2") -> dict:
    """检查 Lambda 函数是否存在和状态"""
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        response = lambda_client.get_function(FunctionName=function_name)
        
        config = response['Configuration']
        return {
            'exists': True,
            'function_name': config['FunctionName'],
            'runtime': config.get('Runtime', 'Unknown'),
            'last_modified': config.get('LastModified', 'Unknown'),
            'state': config.get('State', 'Unknown'),
            'state_reason': config.get('StateReason', ''),
            'timeout': config.get('Timeout', 0),
            'memory_size': config.get('MemorySize', 0),
        }
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            return {'exists': False, 'error': 'Function not found'}
        else:
            return {'exists': False, 'error': str(e)}
    except Exception as e:
        return {'exists': False, 'error': str(e)}

def trigger_lambda(function_name: str, payload: dict, region: str = "us-east-2") -> dict:
    """触发 Lambda 函数"""
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        
        print(f"⚡ 触发 {function_name}...")
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response['Payload'].read())
        
        if response['StatusCode'] == 200:
            if 'FunctionError' in response:
                error_type = response.get('FunctionError', 'Unknown')
                if isinstance(response_payload, dict):
                    error_message = response_payload.get('errorMessage', 'Unknown error')
                    return {'success': False, 'error': f"{error_type}: {error_message}"}
                return {'success': False, 'error': str(response_payload)}
            else:
                return {'success': True, 'response': response_payload}
        else:
            return {'success': False, 'error': f"Status code: {response['StatusCode']}"}
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'ResourceNotFoundException':
            return {'success': False, 'error': 'Function not found'}
        elif error_code == 'AccessDeniedException':
            return {'success': False, 'error': 'Permission denied (need lambda:InvokeFunction)'}
        else:
            return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='检查 Lambda 函数状态')
    parser.add_argument('--trigger', action='store_true', help='触发 Lambda 函数')
    parser.add_argument('--compute', action='store_true', help='只检查/触发 Compute Agent')
    parser.add_argument('--learning', action='store_true', help='只检查/触发 Learning Agent')
    parser.add_argument('--date', type=str, help='日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--region', type=str, default='us-east-2', help='AWS 区域')
    
    args = parser.parse_args()
    
    # 默认日期（今天）
    date = args.date or datetime.now(timezone.utc).date().isoformat()
    
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
    
    print("🔍 Lambda 函数状态检查")
    print("=" * 60)
    print(f"区域: {args.region}")
    print(f"日期: {date}")
    print()
    
    # 确定要检查的函数
    check_compute = args.compute or (not args.compute and not args.learning)
    check_learning = args.learning or (not args.compute and not args.learning)
    
    results = {}
    
    # 检查 Compute Agent
    if check_compute:
        print(f"\n{'='*60}")
        print(f"📊 Compute Agent: {COMPUTE_FUNCTION_NAME}")
        print('='*60)
        
        status = check_lambda_function(COMPUTE_FUNCTION_NAME, args.region)
        if status.get('exists'):
            print("✅ 函数存在")
            print(f"   Runtime: {status.get('runtime', 'Unknown')}")
            print(f"   State: {status.get('state', 'Unknown')}")
            print(f"   Last Modified: {status.get('last_modified', 'Unknown')}")
            print(f"   Timeout: {status.get('timeout', 0)}s")
            print(f"   Memory: {status.get('memory_size', 0)}MB")
            
            if status.get('state') != 'Active':
                print(f"   ⚠️  警告: 函数状态不是 Active: {status.get('state_reason', '')}")
            
            results['compute'] = status
            
            # 如果需要触发
            if args.trigger:
                print("\n触发 Compute Agent...")
                payload = {"date": date}
                result = trigger_lambda(COMPUTE_FUNCTION_NAME, payload, args.region)
                if result.get('success'):
                    print("✅ Compute Agent 执行成功")
                    if 'response' in result:
                        print("响应:")
                        print(json.dumps(result['response'], indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Compute Agent 执行失败: {result.get('error', 'Unknown error')}")
        else:
            print("❌ 函数不存在")
            print(f"   错误: {status.get('error', 'Unknown')}")
            print("\n💡 解决方案:")
            print("   1. 部署 Lambda 函数: ./scripts/deploy-lambda-functions.sh")
            print("   2. 或查看部署指南: docs/features/marketpulse/lambda-deployment-guide.md")
            results['compute'] = status
    
    # 检查 Learning Agent
    if check_learning:
        print(f"\n{'='*60}")
        print(f"🧠 Learning Agent: {LEARNING_FUNCTION_NAME}")
        print('='*60)
        
        status = check_lambda_function(LEARNING_FUNCTION_NAME, args.region)
        if status.get('exists'):
            print("✅ 函数存在")
            print(f"   Runtime: {status.get('runtime', 'Unknown')}")
            print(f"   State: {status.get('state', 'Unknown')}")
            print(f"   Last Modified: {status.get('last_modified', 'Unknown')}")
            print(f"   Timeout: {status.get('timeout', 0)}s")
            print(f"   Memory: {status.get('memory_size', 0)}MB")
            
            if status.get('state') != 'Active':
                print(f"   ⚠️  警告: 函数状态不是 Active: {status.get('state_reason', '')}")
            
            results['learning'] = status
            
            # 如果需要触发
            if args.trigger:
                print("\n触发 Learning Agent...")
                payload = {"date": date}
                result = trigger_lambda(LEARNING_FUNCTION_NAME, payload, args.region)
                if result.get('success'):
                    print("✅ Learning Agent 执行成功")
                    if 'response' in result:
                        print("响应:")
                        print(json.dumps(result['response'], indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Learning Agent 执行失败: {result.get('error', 'Unknown error')}")
        else:
            print("❌ 函数不存在")
            print(f"   错误: {status.get('error', 'Unknown')}")
            print("\n💡 解决方案:")
            print("   1. 部署 Lambda 函数: ./scripts/deploy-lambda-functions.sh")
            print("   2. 或查看部署指南: docs/features/marketpulse/lambda-deployment-guide.md")
            results['learning'] = status
    
    # 总结
    print(f"\n{'='*60}")
    print("📋 总结")
    print('='*60)
    
    if check_compute:
        compute_status = results.get('compute', {})
        if compute_status.get('exists'):
            print("✅ Compute Agent: 已部署")
        else:
            print("❌ Compute Agent: 未部署")
    
    if check_learning:
        learning_status = results.get('learning', {})
        if learning_status.get('exists'):
            print("✅ Learning Agent: 已部署")
        else:
            print("❌ Learning Agent: 未部署")
    
    print()
    print("💡 下一步:")
    if args.trigger:
        print("   - 等待几秒钟，然后刷新 Dashboard")
        print("   - 检查 S3 数据: python3 scripts/view_s3_data.py --check-dashboard --date " + date)
    else:
        print("   - 触发 Lambda 函数: python3 scripts/check_lambda_status.py --trigger")
        print("   - 或使用: python3 scripts/trigger_lambda_agents.py")
    
    print(f"   - 查看日志: aws logs tail /aws/lambda/{COMPUTE_FUNCTION_NAME} --follow --region {args.region}")

if __name__ == "__main__":
    main()
