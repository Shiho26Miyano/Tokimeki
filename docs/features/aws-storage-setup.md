# AWS Storage 配置指南

本文档说明如何配置 AWS Storage 服务用于 Market Pulse 功能。

## 概述

Market Pulse 使用 AWS 存储市场脉搏事件数据：
- **S3**: 存储原始事件数据（JSON 文件）
- **DynamoDB** (可选): 用于快速查询和检索

## 前置要求

1. AWS 账户
2. AWS CLI 已安装（可选，用于测试）
3. Python `boto3` 库（已在 requirements.txt 中）

## 步骤 1: 创建 S3 Bucket

### 使用 AWS Console

1. 登录 AWS Console
2. 进入 S3 服务
3. 点击 "Create bucket"
4. 配置：
   - **Bucket name**: `tokimeki-pulse-events` (或自定义名称)
   - **Region**: 选择你的区域（如 `us-east-1`）
   - **Block Public Access**: 保持默认（全部阻止）
   - **Versioning**: 可选启用
   - **Encryption**: 建议启用（SSE-S3 或 SSE-KMS）

### 使用 AWS CLI

```bash
aws s3 mb s3://tokimeki-pulse-events --region us-east-1
```

## 步骤 2: 创建 DynamoDB Table (可选)

### 使用 AWS Console

1. 进入 DynamoDB 服务
2. 点击 "Create table"
3. 配置：
   - **Table name**: `tokimeki-pulse-events`
   - **Partition key**: `timestamp` (String)
   - **Sort key**: `ticker` (String) - 可选
   - **Table settings**: 使用默认设置或按需配置
   - **Capacity**: 按需或预配置（建议按需）

### 使用 AWS CLI

```bash
aws dynamodb create-table \
    --table-name tokimeki-pulse-events \
    --attribute-definitions \
        AttributeName=timestamp,AttributeType=S \
        AttributeName=ticker,AttributeType=S \
    --key-schema \
        AttributeName=timestamp,KeyType=HASH \
        AttributeName=ticker,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

## 步骤 3: 创建 IAM 用户和策略

### 创建 IAM 用户

1. 进入 IAM 服务
2. 点击 "Users" → "Create user"
3. 用户名: `tokimeki-pulse-service`
4. 选择 "Programmatic access"

### 创建策略

创建最小权限策略：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::tokimeki-pulse-events",
                "arn:aws:s3:::tokimeki-pulse-events/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan"
            ],
            "Resource": "arn:aws:dynamodb:*:*:table/tokimeki-pulse-events"
        }
    ]
}
```

### 附加策略到用户

1. 选择创建的用户
2. 点击 "Add permissions" → "Attach policies directly"
3. 创建并附加上述策略

### 保存访问密钥

创建用户后，保存：
- **Access Key ID**
- **Secret Access Key**

⚠️ **重要**: Secret Access Key 只显示一次，请妥善保存！

## 步骤 4: 配置环境变量

### 本地开发 (.env 文件)

在项目根目录创建或更新 `.env` 文件：

```bash
# AWS 凭证
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_REGION=us-east-1

# S3 配置
AWS_S3_PULSE_BUCKET=tokimeki-pulse-events

# DynamoDB 配置 (可选)
AWS_DYNAMODB_PULSE_TABLE=tokimeki-pulse-events
```

### Railway 部署

在 Railway 项目设置中添加环境变量：

1. 进入 Railway 项目
2. 点击 "Variables" 标签
3. 添加以下变量：
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `AWS_S3_PULSE_BUCKET`
   - `AWS_DYNAMODB_PULSE_TABLE` (可选)

## 步骤 5: 验证配置

### 测试 S3 连接

```python
import boto3
import os

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

bucket = os.getenv('AWS_S3_PULSE_BUCKET')
s3.head_bucket(Bucket=bucket)
print(f"✓ S3 bucket '{bucket}' is accessible")
```

### 测试 DynamoDB 连接

```python
import boto3
import os

dynamodb = boto3.resource('dynamodb',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

table_name = os.getenv('AWS_DYNAMODB_PULSE_TABLE')
table = dynamodb.Table(table_name)
table.meta.client.describe_table(TableName=table_name)
print(f"✓ DynamoDB table '{table_name}' is accessible")
```

## 数据结构

### S3 存储结构

```
s3://tokimeki-pulse-events/
├── pulse-events/
│   ├── 2024-01-15/
│   │   ├── 2024-01-15T10-00-00-000000.json
│   │   ├── 2024-01-15T10-05-00-000000.json
│   │   └── ...
│   ├── 2024-01-16/
│   │   └── ...
│   └── ...
└── daily-summaries/
    ├── 2024-01-15.json
    ├── 2024-01-16.json
    └── ...
```

### DynamoDB 表结构

| 字段 | 类型 | 说明 |
|------|------|------|
| timestamp | String (PK) | ISO 格式时间戳 |
| ticker | String (SK) | 股票代码 |
| stress | Number | 压力指数 (0-1) |
| regime | String | 市场状态 |
| velocity | Number | 价格速度 |
| data | String | 完整事件 JSON |

## 使用示例

### 在代码中使用

```python
from app.services.marketpulse.aws_storage import AWSStorageService

# 初始化服务（会自动从环境变量读取配置）
storage = AWSStorageService()

# 存储单个事件
event = {
    'timestamp': '2024-01-15T10:00:00',
    'ticker': 'SPY',
    'stress': 0.5,
    'regime': 'moderate_stress',
    'velocity': 0.2,
    # ... 其他字段
}
success = storage.store_pulse_event(event)

# 批量存储
events = [event1, event2, event3]
count = storage.store_pulse_events_batch(events)

# 查询事件
from datetime import datetime, timedelta
start = datetime.now() - timedelta(days=7)
end = datetime.now()
events = storage.get_pulse_events(start, end, ticker='SPY')
```

## 故障排除

### 问题: "AWS credentials not found"

**解决方案**:
- 检查环境变量是否正确设置
- 确认 `.env` 文件在项目根目录
- Railway 部署时确认环境变量已添加

### 问题: "S3 bucket does not exist"

**解决方案**:
- 确认 bucket 名称正确
- 确认 bucket 在正确的区域
- 检查 IAM 权限是否包含 `s3:ListBucket`

### 问题: "DynamoDB table does not exist"

**解决方案**:
- 确认表名正确
- 确认表在正确的区域
- 如果不需要 DynamoDB，可以不设置 `AWS_DYNAMODB_PULSE_TABLE` 环境变量

### 问题: "Access Denied"

**解决方案**:
- 检查 IAM 用户权限
- 确认策略已正确附加
- 验证资源 ARN 是否正确

## 成本估算

### S3 成本（每月）

- 存储: ~$0.023/GB
- PUT 请求: ~$0.005/1000 次
- GET 请求: ~$0.0004/1000 次

**示例**: 如果每天生成 288 个事件（每 5 分钟），每个事件 1KB：
- 存储: ~8.6 MB/月 ≈ $0.0002
- PUT 请求: ~8,640/月 ≈ $0.04
- **总计**: ~$0.05/月

### DynamoDB 成本（按需模式）

- 写入: $1.25/百万次
- 读取: $0.25/百万次

**示例**: 每天 288 次写入，7 天查询：
- 写入: ~8,640/月 ≈ $0.01
- 读取: ~2,000/月 ≈ $0.0005
- **总计**: ~$0.01/月

## 安全最佳实践

1. **最小权限原则**: 只授予必要的权限
2. **使用 IAM 角色**: 在 EC2/Lambda 上使用 IAM 角色而非密钥
3. **加密**: 启用 S3 和 DynamoDB 加密
4. **定期轮换密钥**: 定期更换访问密钥
5. **监控**: 启用 CloudTrail 监控访问日志
6. **备份**: 考虑启用 S3 版本控制

## 下一步

配置完成后，Market Pulse 服务会自动：
1. 每 5 分钟计算并存储脉冲事件
2. 将数据写入 S3（和 DynamoDB，如果配置）
3. 通过 API 端点提供历史数据查询

查看 API 文档: `/api/v1/market-pulse/current`

