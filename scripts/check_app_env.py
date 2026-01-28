#!/usr/bin/env python3
"""
检查应用运行时的环境变量
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🔍 检查应用运行时的环境变量...")
print("=" * 60)
print()

# 检查 .env 文件
env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(env_file):
    print(f"✅ 找到 .env 文件: {env_file}")
    print()
    print(".env 文件内容（AWS 相关）:")
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and ('AWS_' in line or 'POLYGON_' in line):
                if '=' in line:
                    key, value = line.split('=', 1)
                    if 'SECRET' in key or 'KEY' in key:
                        print(f"  {key}=***")
                    else:
                        print(f"  {key}={value}")
    print()
else:
    print(f"❌ 未找到 .env 文件: {env_file}")
    print()

# 检查环境变量
print("当前 Python 进程的环境变量:")
aws_vars = {
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
    'AWS_S3_PULSE_BUCKET': os.getenv('AWS_S3_PULSE_BUCKET'),
    'AWS_REGION': os.getenv('AWS_REGION'),
    'POLYGON_API_KEY': os.getenv('POLYGON_API_KEY'),
}

all_set = True
for key, value in aws_vars.items():
    if value:
        if 'SECRET' in key or 'KEY' in key:
            print(f"  {key}: ✅ 已设置 (值: {value[:10]}...)")
        else:
            print(f"  {key}: ✅ 已设置 (值: {value})")
    else:
        print(f"  {key}: ❌ 未设置")
        all_set = False

print()

if not all_set:
    print("❌ 部分环境变量未设置")
    print()
    print("💡 解决方案:")
    print()
    print("方法 1: 在启动应用前设置环境变量")
    print("  export AWS_ACCESS_KEY_ID=your-key")
    print("  export AWS_SECRET_ACCESS_KEY=your-secret")
    print("  export AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod")
    print("  export AWS_REGION=us-east-2")
    print("  python main.py")
    print()
    print("方法 2: 使用 .env 文件（确保格式正确）")
    print("  # .env 文件格式应该是 KEY=value（不要用 export）")
    print("  AWS_ACCESS_KEY_ID=your-key")
    print("  AWS_SECRET_ACCESS_KEY=your-secret")
    print("  AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod")
    print("  AWS_REGION=us-east-2")
    print()
    print("  然后使用 python-dotenv 加载，或手动 source:")
    print("  source .env  # 如果 .env 文件使用 export 格式")
    print("  python main.py")
    print()
    print("方法 3: 使用启动脚本")
    print("  ./scripts/quick_fix_env.sh")
    print("  source .env && python main.py")
else:
    print("✅ 所有必需的环境变量都已设置！")
    print()
    print("如果应用仍然报错，可能原因:")
    print("  1. 应用在不同的进程中运行（没有继承环境变量）")
    print("  2. 应用启动时环境变量还未设置")
    print("  3. 需要重启应用以加载新的环境变量")
