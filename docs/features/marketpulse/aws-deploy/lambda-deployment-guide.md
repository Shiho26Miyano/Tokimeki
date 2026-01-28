# AWS Lambda Agent 部署指南

## 📦 部署文件

**文件位置**: `docs/features/marketpulse/aws-lambda-compute-agent.py`

这个文件可以直接部署到 AWS Lambda！

## 🚀 快速部署步骤

### 步骤 1: 准备文件

```bash
# 进入项目目录
cd /Volumes/D/2026_Project/Tokimeki

# 复制 Lambda Agent 文件
cp docs/features/marketpulse/aws-lambda-compute-agent.py lambda_function.py

# 创建部署包
zip lambda-deployment.zip lambda_function.py
```

### 步骤 2: 创建 Lambda Function

#### 方法 A: 使用 AWS Console（推荐新手）

1. **登录 AWS Console**
   - 访问 https://console.aws.amazon.com/lambda
   - 选择你的区域（如 `us-east-2`）

2. **创建函数**
   - 点击 "Create function"
   - 选择 "Author from scratch"
   - 函数名: `market-pulse-agent`
   - Runtime: `Python 3.11` 或 `Python 3.12`
   - Architecture: `x86_64`

3. **上传代码**
   - 在 "Code" 标签页
   - 点击 "Upload from" → ".zip file"
   - 选择 `lambda-deployment.zip`
   - 点击 "Save"

4. **设置环境变量**
   - 在 "Configuration" → "Environment variables"
   - 添加: `S3_BUCKET_NAME` = `your-bucket-name`
   - 点击 "Save"

5. **设置超时**
   - "Configuration" → "General configuration" → "Edit"
   - Timeout: `15 minutes` (900 seconds)
   - Memory: `512 MB`
   - 点击 "Save"

#### 方法 B: 使用 AWS CLI（推荐开发者）

```bash
# 1. 创建 Lambda Function
aws lambda create-function \
    --function-name market-pulse-agent \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-deployment.zip \
    --timeout 900 \
    --memory-size 512 \
    --environment Variables="{S3_BUCKET_NAME=your-bucket-name}"

# 2. 更新代码（如果已存在）
aws lambda update-function-code \
    --function-name market-pulse-agent \
    --zip-file fileb://lambda-deployment.zip
```

### 步骤 3: 设置 IAM 权限

Lambda execution role 需要以下权限：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }
    ]
}
```

### 步骤 4: 设置 EventBridge 触发（可选）

每天 21:00 ET（收盘后）自动触发：

```bash
# 创建 EventBridge Rule
aws events put-rule \
    --name market-pulse-daily-processor \
    --schedule-expression "cron(0 21 * * ? *)" \
    --description "Process Market Pulse data daily at 21:00 ET"

# 添加 Lambda 作为 target
aws events put-targets \
    --rule market-pulse-daily-processor \
    --targets "Id=1,Arn=arn:aws:lambda:REGION:ACCOUNT:function:market-pulse-agent"
```

## 🧪 测试 Lambda

### 手动测试

#### 使用 AWS Console

1. 进入 Lambda Function 页面
2. 点击 "Test" 标签
3. 创建测试事件：
   ```json
   {
     "date": "2024-01-15"
   }
   ```
4. 点击 "Test"
5. 查看执行结果和日志

#### 使用 AWS CLI

```bash
aws lambda invoke \
    --function-name market-pulse-agent \
    --payload '{"date": "2024-01-15"}' \
    response.json

cat response.json
```

### 查看日志

```bash
aws logs tail /aws/lambda/market-pulse-agent --follow
```

## 📋 部署检查清单

- [ ] Lambda Function 已创建
- [ ] 代码已上传（`lambda_function.py`）
- [ ] 环境变量已设置（`S3_BUCKET_NAME`）
- [ ] 超时设置为 15 分钟（900 秒）
- [ ] IAM 权限已配置（S3 读写权限）
- [ ] EventBridge 规则已创建（可选）
- [ ] 手动测试成功
- [ ] 日志正常输出

## 🔧 常见问题

### 问题 1: "ModuleNotFoundError"

**原因**: Lambda 环境缺少依赖

**解决**: 
- Lambda 内置了 `boto3`，不需要额外安装
- 如果使用其他库，需要打包到 zip 文件中

### 问题 2: "Access Denied" 错误

**原因**: IAM 权限不足

**解决**: 检查 Lambda execution role 是否有 S3 权限

### 问题 3: 超时错误

**原因**: 处理时间超过 15 分钟

**解决**: 
- 增加超时时间（最多 15 分钟）
- 或优化代码，减少处理时间

### 问题 4: 找不到 S3 文件

**原因**: Bucket 名称或路径错误

**解决**: 
- 检查环境变量 `S3_BUCKET_NAME`
- 确认 S3 中有 `raw-data/YYYY-MM-DD/` 的数据

## 📝 文件结构

部署后的 Lambda 结构：

```
lambda_function.py          # 主文件（从 aws-lambda-compute-agent.py 重命名）
├── read_raw_data_from_s3()
├── calculate_price_velocity()
├── calculate_volume_surge()
├── calculate_volatility()
├── calculate_stress_index()
├── compute_pulse_from_bars()
├── learn_patterns()
├── generate_daily_summary()
├── process_daily_data()
└── lambda_handler()        # 入口点
```

## 🎯 下一步

部署成功后：

1. ✅ 手动测试一次
2. ✅ 检查 S3 中是否生成了 `processed-data/` 文件
3. ✅ 设置 EventBridge 自动触发
4. ✅ 监控 CloudWatch 日志

## 🔗 相关文档

- [Lambda Compute Agent 代码](./aws-lambda-compute-agent.py)
- [文档索引](./README.md)
- [架构设计 v2](./architecture-layered-v2.md)
