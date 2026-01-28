#!/usr/bin/env python3
"""
验证 S3 IAM 策略是否正确配置
"""
import os
import sys
import json

# 加载 .env
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                os.environ.setdefault(key.strip(), value)

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("❌ boto3 not installed")
    sys.exit(1)

print("🔍 验证 S3 IAM 策略配置...")
print("=" * 60)

bucket = os.getenv('AWS_S3_PULSE_BUCKET', 'tokimeki-market-pulse-prod')
print(f"\nBucket: {bucket}")

# 检查凭证
if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
    print("❌ AWS 凭证未设置")
    sys.exit(1)

try:
    # 获取当前用户信息
    sts = boto3.client('sts',
                       aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                       aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    identity = sts.get_caller_identity()
    user_arn = identity.get('Arn')
    account_id = identity.get('Account')
    
    print(f"\n当前用户: {user_arn}")
    print(f"账户 ID: {account_id}")
    
    # 获取用户名
    if ':user/' in user_arn:
        username = user_arn.split(':user/')[-1]
        print(f"用户名: {username}")
        
        # 列出附加的策略
        iam = boto3.client('iam',
                           aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        
        print(f"\n📋 检查附加的策略...")
        try:
            # 获取附加的策略
            attached_policies = iam.list_attached_user_policies(UserName=username)
            
            market_pulse_policy = None
            for policy in attached_policies.get('AttachedPolicies', []):
                if 'MarketPulse' in policy['PolicyName'] or 'S3' in policy['PolicyName']:
                    market_pulse_policy = policy
                    print(f"  ✅ 找到策略: {policy['PolicyName']}")
                    print(f"     ARN: {policy['PolicyArn']}")
            
            if market_pulse_policy:
                # 获取策略内容
                policy_version = iam.get_policy(PolicyArn=market_pulse_policy['PolicyArn'])
                default_version = policy_version['Policy']['DefaultVersionId']
                
                policy_doc = iam.get_policy_version(
                    PolicyArn=market_pulse_policy['PolicyArn'],
                    VersionId=default_version
                )
                
                policy_json = policy_doc['PolicyVersion']['Document']
                print(f"\n📄 策略内容:")
                print(json.dumps(policy_json, indent=2))
                
                # 检查是否包含必要的权限
                statements = policy_json.get('Statement', [])
                has_list_bucket = False
                has_get_object = False
                
                for stmt in statements:
                    actions = stmt.get('Action', [])
                    if not isinstance(actions, list):
                        actions = [actions]
                    
                    resources = stmt.get('Resource', [])
                    if not isinstance(resources, list):
                        resources = [resources]
                    
                    for action in actions:
                        if 's3:ListBucket' in action:
                            has_list_bucket = True
                        if 's3:GetObject' in action:
                            has_get_object = True
                
                print(f"\n✅ 权限检查:")
                print(f"  s3:ListBucket: {'✅' if has_list_bucket else '❌'}")
                print(f"  s3:GetObject: {'✅' if has_get_object else '❌'}")
                
                if not has_list_bucket:
                    print(f"\n❌ 缺少 s3:ListBucket 权限！")
                    print(f"   这是导致 403 错误的原因")
                    print(f"\n💡 修复方法:")
                    print(f"   1. 在 AWS Console 中编辑策略")
                    print(f"   2. 确保包含以下权限:")
                    print(f"      - s3:ListBucket (Resource: arn:aws:s3:::{bucket})")
                    print(f"      - s3:GetObject (Resource: arn:aws:s3:::{bucket}/*)")
            else:
                print(f"\n❌ 未找到 Market Pulse 相关策略")
                print(f"   请检查策略是否已附加到用户")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print(f"\n⚠️  无法检查 IAM 策略（需要 iam:ListAttachedUserPolicies 权限）")
                print(f"   但可以继续测试 S3 访问")
            else:
                raise
    
    # 测试 S3 访问
    print(f"\n🧪 测试 S3 访问...")
    s3 = boto3.client('s3',
                     region_name=os.getenv('AWS_REGION', 'us-east-2'),
                     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    
    try:
        s3.head_bucket(Bucket=bucket)
        print("✅ head_bucket 成功")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '403':
            print("❌ 403 Forbidden - 确认缺少权限")
        else:
            print(f"❌ 错误: {error_code}")
    
except ClientError as e:
    print(f"❌ AWS API 错误: {e}")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
