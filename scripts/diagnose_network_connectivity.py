#!/usr/bin/env python3
"""
诊断网络连接问题 - 检查 S3 端点连通性
"""
import os
import sys
import socket
import subprocess
from urllib.parse import urlparse

def test_dns_resolution(hostname):
    """测试 DNS 解析"""
    try:
        ip = socket.gethostbyname(hostname)
        return True, ip
    except socket.gaierror as e:
        return False, str(e)

def test_http_connectivity(url):
    """测试 HTTP 连接"""
    try:
        import urllib.request
        response = urllib.request.urlopen(url, timeout=5)
        return True, response.status
    except Exception as e:
        return False, str(e)

def main():
    print("🔍 网络连接诊断")
    print("=" * 60)
    print()
    
    # 检查基本网络连接
    print("1. 基本网络连接测试")
    print("-" * 60)
    
    test_hosts = [
        ("8.8.8.8", "Google DNS"),
        ("1.1.1.1", "Cloudflare DNS"),
        ("www.google.com", "Google"),
        ("s3.us-east-2.amazonaws.com", "S3 US East 2"),
        ("tokimeki-market-pulse-prod.s3.us-east-2.amazonaws.com", "S3 Bucket")
    ]
    
    for hostname, description in test_hosts:
        success, result = test_dns_resolution(hostname)
        if success:
            print(f"  ✅ {description:30} -> {result}")
        else:
            print(f"  ❌ {description:30} -> DNS 解析失败: {result}")
    
    print()
    
    # 检查 AWS 环境变量
    print("2. AWS 环境变量检查")
    print("-" * 60)
    
    aws_vars = {
        'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'AWS_S3_PULSE_BUCKET': os.getenv('AWS_S3_PULSE_BUCKET'),
        'AWS_REGION': os.getenv('AWS_REGION'),
    }
    
    for key, value in aws_vars.items():
        if value:
            if 'SECRET' in key or 'KEY' in key:
                print(f"  ✅ {key:30} -> 已设置 ({value[:10]}...)")
            else:
                print(f"  ✅ {key:30} -> {value}")
        else:
            print(f"  ❌ {key:30} -> 未设置")
    
    print()
    
    # 检查 .env 文件
    print("3. .env 文件检查")
    print("-" * 60)
    
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        print(f"  ✅ .env 文件存在: {env_file}")
        with open(env_file, 'r') as f:
            aws_lines = [line.strip() for line in f if 'AWS_' in line and not line.strip().startswith('#')]
            if aws_lines:
                print(f"  ✅ 找到 {len(aws_lines)} 个 AWS 相关配置")
            else:
                print(f"  ⚠️  未找到 AWS 相关配置")
    else:
        print(f"  ❌ .env 文件不存在: {env_file}")
    
    print()
    
    # 测试 S3 端点
    print("4. S3 端点连接测试")
    print("-" * 60)
    
    s3_endpoints = [
        "https://s3.us-east-2.amazonaws.com",
        "https://tokimeki-market-pulse-prod.s3.us-east-2.amazonaws.com/",
    ]
    
    for url in s3_endpoints:
        success, result = test_http_connectivity(url)
        if success:
            print(f"  ✅ {url:50} -> HTTP {result}")
        else:
            print(f"  ❌ {url:50} -> 连接失败: {result}")
    
    print()
    
    # 建议
    print("5. 建议")
    print("-" * 60)
    
    # 检查 DNS 解析
    success, _ = test_dns_resolution("s3.us-east-2.amazonaws.com")
    if not success:
        print("  ❌ DNS 解析失败")
        print("     解决方案:")
        print("     1. 检查网络连接")
        print("     2. 检查 DNS 设置: scutil --dns")
        print("     3. 尝试使用 VPN 或代理")
        print("     4. 检查防火墙设置")
        print("     5. 尝试使用其他 DNS 服务器 (8.8.8.8, 1.1.1.1)")
    
    # 检查环境变量
    if not aws_vars['AWS_ACCESS_KEY_ID'] or not aws_vars['AWS_SECRET_ACCESS_KEY']:
        print("  ⚠️  AWS 凭证未设置")
        print("     解决方案:")
        print("     1. 运行: ./scripts/add_aws_to_env.sh")
        print("     2. 或手动设置环境变量")
    
    print()

if __name__ == "__main__":
    main()
