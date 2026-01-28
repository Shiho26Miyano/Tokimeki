#!/usr/bin/env python3
"""
诊断 403 Forbidden 错误
检查 IAM 策略是否正确配置
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

print("🔍 诊断 403 Forbidden 错误...")
print("=" * 60)

bucket = os.getenv('AWS_S3_PULSE_BUCKET', 'tokimeki-market-pulse-prod')
print(f"\nBucket: {bucket}")

# 检查凭证
if not os.getenv('AWS_ACCESS_KEY_ID') or not os.getenv('AWS_SECRET_ACCESS_KEY'):
    print("❌ AWS 凭证未设置")
    sys.exit(1)

print("✅ AWS 凭证已设置")

try:
    # 获取当前用户信息
    sts = boto3.client('sts',
                       aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                       aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    identity = sts.get_caller_identity()
    user_arn = identity.get('Arn')
    account_id = identity.get('Account')
    
    print(f"\n当前 AWS 用户:")
    print(f"  ARN: {user_arn}")
    print(f"  账户 ID: {account_id}")
    
    # 测试 S3 访问
    print(f"\n🧪 测试 S3 访问...")
    s3 = boto3.client('s3',
                     region_name=os.getenv('AWS_REGION', 'us-east-2'),
                     aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                     aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
    
    # 测试 head_bucket
    print(f"\n1. 测试 head_bucket (需要 s3:ListBucket)...")
    try:
        s3.head_bucket(Bucket=bucket)
        print("   ✅ head_bucket 成功！")
        print("   ✅ 权限配置正确")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        error_msg = e.response.get('Error', {}).get('Message', '')
        
        if error_code == '403':
            print(f"   ❌ 403 Forbidden")
            print(f"   错误消息: {error_msg}")
            print(f"\n💡 可能的原因:")
            print(f"   1. 策略未正确附加到用户: {user_arn}")
            print(f"   2. 策略中的 Condition 条件阻止了 head_bucket")
            print(f"   3. 策略需要时间生效（等待 1-5 分钟）")
            print(f"   4. 可能有其他策略在拒绝访问")
            print(f"\n🔧 检查步骤:")
            print(f"   1. 在 AWS Console 中确认策略已附加到用户")
            print(f"   2. 检查策略中的 s3:prefix 条件是否包含空字符串 \"\"")
            print(f"   3. 等待几分钟后重试")
        else:
            print(f"   ❌ 错误: {error_code}")
            print(f"   消息: {error_msg}")
    
    # 如果 head_bucket 失败，尝试其他操作
    print(f"\n2. 测试 list_objects_v2 (也需要 s3:ListBucket)...")
    try:
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        print("   ✅ list_objects_v2 成功")
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == '403':
            print("   ❌ 403 Forbidden - 确认缺少 s3:ListBucket 权限")
        else:
            print(f"   ❌ 错误: {error_code}")
    
    # 如果用户是 IAM 用户，尝试检查策略
    if ':user/' in user_arn:
        username = user_arn.split(':user/')[-1]
        print(f"\n3. 检查 IAM 策略（需要 iam:ListAttachedUserPolicies 权限）...")
        try:
            iam = boto3.client('iam',
                             aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                             aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
            
            attached_policies = iam.list_attached_user_policies(UserName=username)
            
            print(f"   用户名: {username}")
            print(f"   附加的策略数量: {len(attached_policies.get('AttachedPolicies', []))}")
            
            market_pulse_policy = None
            for policy in attached_policies.get('AttachedPolicies', []):
                print(f"   - {policy['PolicyName']} ({policy['PolicyArn']})")
                if 'MarketPulse' in policy['PolicyName'] or 'S3' in policy['PolicyName']:
                    market_pulse_policy = policy
            
            if market_pulse_policy:
                print(f"\n   ✅ 找到 Market Pulse 策略: {market_pulse_policy['PolicyName']}")
                
                # 获取策略内容
                try:
                    policy_version = iam.get_policy(PolicyArn=market_pulse_policy['PolicyArn'])
                    default_version = policy_version['Policy']['DefaultVersionId']
                    
                    policy_doc = iam.get_policy_version(
                        PolicyArn=market_pulse_policy['PolicyArn'],
                        VersionId=default_version
                    )
                    
                    policy_json = policy_doc['PolicyVersion']['Document']
                    
                    # 检查策略内容
                    statements = policy_json.get('Statement', [])
                    has_list_bucket = False
                    has_correct_resource = False
                    has_empty_prefix = False
                    
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
                                
                                # 检查 Resource
                                for resource in resources:
                                    if resource == f"arn:aws:s3:::{bucket}":
                                        has_correct_resource = True
                                
                                # 检查 Condition
                                condition = stmt.get('Condition', {})
                                if condition:
                                    string_like = condition.get('StringLike', {})
                                    prefixes = string_like.get('s3:prefix', [])
                                    if "" in prefixes or '' in prefixes:
                                        has_empty_prefix = True
                    
                    print(f"\n   📋 策略检查:")
                    print(f"      s3:ListBucket 权限: {'✅' if has_list_bucket else '❌'}")
                    print(f"      Resource ARN 正确: {'✅' if has_correct_resource else '❌'}")
                    print(f"      s3:prefix 包含空字符串: {'✅' if has_empty_prefix else '❌'}")
                    
                    if not has_list_bucket:
                        print(f"\n   ❌ 策略中缺少 s3:ListBucket 权限")
                    elif not has_correct_resource:
                        print(f"\n   ❌ 策略中的 Resource ARN 不正确")
                        print(f"      应该是: arn:aws:s3:::{bucket}")
                    elif not has_empty_prefix:
                        print(f"\n   ⚠️  策略中的 s3:prefix 条件可能缺少空字符串")
                        print(f"      这可能导致 head_bucket 失败")
                    else:
                        print(f"\n   ✅ 策略配置看起来正确")
                        print(f"      💡 如果仍然 403，可能原因:")
                        print(f"         1. 策略需要时间生效（等待 1-5 分钟）")
                        print(f"         2. 可能有其他策略在拒绝访问")
                        print(f"         3. Bucket policy 可能阻止了访问")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDenied':
                        print(f"   ⚠️  无法读取策略内容（需要 iam:GetPolicy 权限）")
                    else:
                        print(f"   ❌ 错误读取策略: {e}")
            else:
                print(f"\n   ❌ 未找到 Market Pulse 相关策略")
                print(f"      请检查策略是否已附加到用户")
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDenied':
                print(f"   ⚠️  无法检查 IAM 策略（需要 iam:ListAttachedUserPolicies 权限）")
            else:
                print(f"   ❌ 错误: {e}")
    
    print(f"\n" + "=" * 60)
    print(f"📖 详细修复指南: docs/features/marketpulse/FIX-403-FORBIDDEN.md")
    
except ClientError as e:
    error_code = e.response.get('Error', {}).get('Code', '')
    print(f"❌ AWS API 错误: {error_code}")
    print(f"   消息: {e.response.get('Error', {}).get('Message', '')}")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
