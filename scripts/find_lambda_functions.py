#!/usr/bin/env python3
"""
查找所有 Lambda 函数，特别是 Market Pulse 相关的函数

用法:
    python scripts/find_lambda_functions.py                    # 查找所有函数
    python scripts/find_lambda_functions.py --region us-east-2  # 指定区域
"""
import os
import sys
import json
import argparse

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    print("❌ boto3 not installed. Install with: pip install boto3")
    sys.exit(1)

def list_all_lambda_functions(region: str = "us-east-2"):
    """列出所有 Lambda 函数"""
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        
        print(f"🔍 在区域 {region} 中查找 Lambda 函数...")
        print("=" * 60)
        
        # 列出所有函数
        paginator = lambda_client.get_paginator('list_functions')
        all_functions = []
        
        for page in paginator.paginate():
            all_functions.extend(page.get('Functions', []))
        
        if not all_functions:
            print(f"❌ 在区域 {region} 中没有找到任何 Lambda 函数")
            return []
        
        print(f"✅ 找到 {len(all_functions)} 个 Lambda 函数:\n")
        
        # 查找 Market Pulse 相关的函数
        market_pulse_functions = []
        other_functions = []
        
        for func in all_functions:
            func_name = func['FunctionName']
            if 'market' in func_name.lower() or 'pulse' in func_name.lower() or 'compute' in func_name.lower() or 'learning' in func_name.lower():
                market_pulse_functions.append(func)
            else:
                other_functions.append(func)
        
        # 显示 Market Pulse 相关函数
        if market_pulse_functions:
            print("📊 Market Pulse 相关函数:")
            print("-" * 60)
            for func in market_pulse_functions:
                func_name = func['FunctionName']
                runtime = func.get('Runtime', 'Unknown')
                last_modified = func.get('LastModified', 'Unknown')
                state = func.get('State', 'Unknown')
                timeout = func.get('Timeout', 0)
                memory = func.get('MemorySize', 0)
                
                print(f"  ✅ {func_name}")
                print(f"     Runtime: {runtime}")
                print(f"     State: {state}")
                print(f"     Timeout: {timeout}s, Memory: {memory}MB")
                print(f"     Last Modified: {last_modified}")
                
                # 检查环境变量
                try:
                    config = lambda_client.get_function_configuration(FunctionName=func_name)
                    env_vars = config.get('Environment', {}).get('Variables', {})
                    if env_vars:
                        print(f"     Environment Variables:")
                        for key, value in env_vars.items():
                            print(f"       - {key}: {value}")
                except:
                    pass
                
                # 检查触发器
                try:
                    event_config = lambda_client.list_event_source_mappings(FunctionName=func_name)
                    if event_config.get('EventSourceMappings'):
                        print(f"     Event Sources: {len(event_config['EventSourceMappings'])}")
                except:
                    pass
                
                print()
        
        # 显示其他函数（可选）
        if other_functions:
            print(f"\n其他函数 ({len(other_functions)} 个):")
            print("-" * 60)
            for func in other_functions[:10]:  # 只显示前10个
                print(f"  - {func['FunctionName']}")
            if len(other_functions) > 10:
                print(f"  ... 还有 {len(other_functions) - 10} 个函数")
        
        return market_pulse_functions
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'AccessDeniedException':
            print(f"❌ 权限不足: 无法列出 Lambda 函数")
            print(f"   需要权限: lambda:ListFunctions")
            print(f"   错误: {e}")
        else:
            print(f"❌ 错误: {e}")
        return []
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return []

def check_specific_functions(region: str = "us-east-2"):
    """检查特定的函数名称"""
    expected_functions = [
        "market-pulse-compute-agent",
        "market-pulse-learning-agent",
        "market-pulse-compute",
        "market-pulse-learning",
        "compute-agent",
        "learning-agent",
    ]
    
    print(f"\n🔍 检查预期的函数名称...")
    print("=" * 60)
    
    try:
        lambda_client = boto3.client('lambda', region_name=region)
        
        for func_name in expected_functions:
            try:
                response = lambda_client.get_function(FunctionName=func_name)
                config = response['Configuration']
                print(f"✅ 找到: {func_name}")
                print(f"   Runtime: {config.get('Runtime', 'Unknown')}")
                print(f"   State: {config.get('State', 'Unknown')}")
                print(f"   Last Modified: {config.get('LastModified', 'Unknown')}")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                if error_code == 'ResourceNotFoundException':
                    print(f"❌ 未找到: {func_name}")
                else:
                    print(f"⚠️  {func_name}: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    parser = argparse.ArgumentParser(description='查找 Lambda 函数')
    parser.add_argument('--region', type=str, default='us-east-2', help='AWS 区域')
    parser.add_argument('--all-regions', action='store_true', help='检查所有区域')
    
    args = parser.parse_args()
    
    # 检查 AWS 凭证
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if not credentials:
            print("❌ AWS 凭证未配置")
            print("   设置环境变量: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            sys.exit(1)
        
        # 显示当前身份
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"当前 AWS 身份: {identity.get('Arn', 'Unknown')}")
        print(f"账户 ID: {identity.get('Account', 'Unknown')}")
        print()
    except Exception as e:
        print(f"❌ 检查 AWS 凭证失败: {e}")
        sys.exit(1)
    
    if args.all_regions:
        # 检查所有区域
        common_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1'
        ]
        
        for region in common_regions:
            print(f"\n{'='*60}")
            print(f"区域: {region}")
            print('='*60)
            list_all_lambda_functions(region)
    else:
        # 检查指定区域
        list_all_lambda_functions(args.region)
        check_specific_functions(args.region)
    
    print("\n" + "=" * 60)
    print("💡 提示:")
    print("   - 如果函数存在但名称不同，更新脚本中的函数名称")
    print("   - 如果函数在不同区域，使用 --region 参数")
    print("   - 如果函数在不同账户，检查 AWS 凭证")

if __name__ == "__main__":
    main()
