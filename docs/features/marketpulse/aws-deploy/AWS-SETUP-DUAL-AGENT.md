# AWS 部署指南 - 双 Agent 系统

## 🎯 部署概览

需要部署两个 Lambda 函数：
1. **计算 Agent** (`market-pulse-compute-agent`) - 每5分钟运行
2. **学习 Agent** (`market-pulse-learning-agent`) - 每天运行一次

---

## 📋 前置要求

1. AWS 账户
2. AWS CLI 已安装和配置
3. S3 Bucket 已创建
4. IAM 角色已创建（有 S3 读写权限）

---

## 🔧 Step 0: 安装和配置 AWS CLI

### 0.1 安装 AWS CLI（macOS）

如果你看到 `zsh: command not found: aws` 错误，说明 AWS CLI 还未安装。

**方法 1: 使用 Homebrew（推荐）**

```bash
# 如果遇到权限问题，先修复权限
sudo chown -R $(whoami) /opt/homebrew/Cellar

# 安装 AWS CLI
brew install awscli
```

**方法 2: 使用官方安装包**

```bash
# 下载安装包
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"

# 安装
sudo installer -pkg AWSCLIV2.pkg -target /
```

**方法 3: 使用 pip（如果已安装 Python）**

```bash
pip install awscli
```

### 0.2 验证安装

在**本地终端（Terminal）**中运行：

```bash
# 检查 AWS CLI 是否安装成功
aws --version
# 应该显示类似：aws-cli/2.x.x Python/3.x.x ...

# 检查 AWS CLI 是否配置
aws configure list
# 如果显示 "access_key" 和 "secret_key" 为 (not set)，需要配置
```

### 0.3 配置 AWS CLI

如果 `aws configure list` 显示未配置，运行：

```bash
aws configure
```

会提示你输入：
- **AWS Access Key ID**: 你的 AWS 访问密钥 ID
- **AWS Secret Access Key**: 你的 AWS 秘密访问密钥
- **Default region name**: 默认区域（例如：`us-east-2`）
- **Default output format**: 默认输出格式（推荐：`json`）

### 0.4 获取 AWS 账户 ID

```bash
# 获取你的 AWS 账户 ID（记下来，后面要用！）
aws sts get-caller-identity
# 会显示你的 Account ID，例如：123456789012
```

**重要**：将返回的 `Account` 值记录下来，后续步骤中需要替换文档中的 `YOUR_ACCOUNT_ID`。

---

## 🗂️ Step 1: 创建 S3 Bucket

```bash
# 创建 bucket
aws s3 mb s3://your-market-pulse-bucket --region us-east-2

# 设置 bucket 策略（如果需要）
aws s3api put-bucket-policy --bucket your-market-pulse-bucket --policy file://bucket-policy.json
```

**Bucket 结构**：
```
s3://your-market-pulse-bucket/
├── raw-data/                    # 原始数据（数据采集层写入）
├── processed-data/              # 处理后的数据（计算 Agent 写入）
└── learning-results/            # 学习结果（学习 Agent 写入）
    ├── baseline/
    ├── patterns/
    └── models/
```

---

## 🔐 Step 2: 创建 IAM 角色

### 创建 Lambda 执行角色

```bash
# 创建角色
aws iam create-role \
    --role-name market-pulse-lambda-role \
    --assume-role-policy-document file://trust-policy.json

# 附加策略（S3 读写权限）
aws iam attach-role-policy \
    --role-name market-pulse-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

**trust-policy.json**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

---

## ⚡ Step 3: 部署计算 Agent

### 3.1 准备部署包

```bash
cd /Volumes/D/2026_Project/Tokimeki

# 复制计算 Agent 代码
cp docs/features/marketpulse/aws-lambda-compute-agent.py lambda_compute_agent.py

# 创建部署包
zip lambda-compute-agent.zip lambda_compute_agent.py
```

### 3.2 创建 Lambda 函数

```bash
aws lambda create-function \
    --function-name market-pulse-compute-agent \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/market-pulse-lambda-role \
    --handler lambda_compute_agent.lambda_handler \
    --zip-file fileb://lambda-compute-agent.zip \
    --timeout 900 \
    --memory-size 512 \
    --environment Variables="{S3_BUCKET_NAME=your-market-pulse-bucket}"
```

### 3.3 创建 EventBridge 规则（每5分钟触发）

```bash
# 创建规则
aws events put-rule \
    --name market-pulse-compute-schedule \
    --schedule-expression "rate(5 minutes)" \
    --state ENABLED

# 添加 Lambda 目标
aws events put-targets \
    --rule market-pulse-compute-schedule \
    --targets "Id=1,Arn=arn:aws:lambda:us-east-2:YOUR_ACCOUNT_ID:function:market-pulse-compute-agent"
```

---

## 🧠 Step 4: 部署学习 Agent

### 4.1 准备部署包

```bash
# 复制学习 Agent 代码
cp docs/features/marketpulse/aws-lambda-learning-agent.py lambda_learning_agent.py

# 创建部署包
zip lambda-learning-agent.zip lambda_learning_agent.py
```

### 4.2 创建 Lambda 函数

```bash
aws lambda create-function \
    --function-name market-pulse-learning-agent \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/market-pulse-lambda-role \
    --handler lambda_learning_agent.lambda_handler \
    --zip-file fileb://lambda-learning-agent.zip \
    --timeout 900 \
    --memory-size 1024 \
    --environment Variables="{S3_BUCKET_NAME=your-market-pulse-bucket}"
```

### 4.3 创建 EventBridge 规则（每天 00:00 UTC）

```bash
# 创建规则
aws events put-rule \
    --name market-pulse-learning-schedule \
    --schedule-expression "cron(0 0 * * ? *)" \
    --state ENABLED

# 添加 Lambda 目标
aws events put-targets \
    --rule market-pulse-learning-schedule \
    --targets "Id=1,Arn=arn:aws:lambda:us-east-2:YOUR_ACCOUNT_ID:function:market-pulse-learning-agent"
```

---

## ✅ Step 5: 验证部署

### 测试计算 Agent

```bash
# 手动触发
aws lambda invoke \
    --function-name market-pulse-compute-agent \
    --payload '{"date": "2026-01-26"}' \
    response.json

# 查看结果
cat response.json
```

### 测试学习 Agent

```bash
# 手动触发
aws lambda invoke \
    --function-name market-pulse-learning-agent \
    --payload '{"date": "2026-01-26"}' \
    response.json

# 查看结果
cat response.json
```

### 检查 S3 数据

```bash
# 检查 processed-data
aws s3 ls s3://your-market-pulse-bucket/processed-data/ --recursive

# 检查 learning-results
aws s3 ls s3://your-market-pulse-bucket/learning-results/ --recursive
```

---

## 🔧 Step 6: 配置后端环境变量

在后端服务器上设置环境变量：

```bash
export AWS_S3_PULSE_BUCKET=your-market-pulse-bucket
export AWS_REGION=us-east-2
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
```

或者在 `.env` 文件中：
```
AWS_S3_PULSE_BUCKET=your-market-pulse-bucket
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

---

## 📊 Step 7: 监控和日志

### 查看 Lambda 日志

```bash
# 计算 Agent 日志
aws logs tail /aws/lambda/market-pulse-compute-agent --follow

# 学习 Agent 日志
aws logs tail /aws/lambda/market-pulse-learning-agent --follow
```

### CloudWatch 指标

- Lambda 调用次数
- Lambda 错误率
- Lambda 执行时间
- S3 存储使用量

---

## 💰 成本估算

### Lambda 成本
- **计算 Agent**: 每天 288 次 × $0.0000002 = $0.00006/天 ≈ $0.002/月
- **学习 Agent**: 每天 1 次 × $0.0000167 = $0.0000167/天 ≈ $0.0005/月
- **总计**: ~$0.003/月

### S3 成本
- **存储**: ~1 GB × $0.023 = $0.023/月
- **请求**: ~10,000 次 × $0.0004/1000 = $0.004/月
- **总计**: ~$0.03/月

### **总成本**: ~$0.033/月（几乎免费！）

---

## 🚨 故障排查

### 问题 1: Lambda 无法访问 S3

**解决**: 检查 IAM 角色权限

```bash
aws iam get-role-policy \
    --role-name market-pulse-lambda-role \
    --policy-name S3Access
```

### 问题 2: EventBridge 未触发

**解决**: 检查规则状态

```bash
aws events describe-rule --name market-pulse-compute-schedule
```

### 问题 3: 学习 Agent 没有数据

**解决**: 确保计算 Agent 已运行至少一天，生成 processed-data

---

## 📝 更新代码

### 更新计算 Agent

```bash
# 修改代码后
zip lambda-compute-agent.zip lambda_compute_agent.py

# 更新 Lambda
aws lambda update-function-code \
    --function-name market-pulse-compute-agent \
    --zip-file fileb://lambda-compute-agent.zip
```

### 更新学习 Agent

```bash
# 修改代码后
zip lambda-learning-agent.zip lambda_learning_agent.py

# 更新 Lambda
aws lambda update-function-code \
    --function-name market-pulse-learning-agent \
    --zip-file fileb://lambda-learning-agent.zip
```

---

## ✅ 完成！

现在你的双 Agent 系统已经部署完成：

1. ✅ 计算 Agent 每5分钟自动运行
2. ✅ 学习 Agent 每天自动运行
3. ✅ 数据存储在 S3
4. ✅ Dashboard 可以显示对比

访问 Dashboard: `http://your-server/market-pulse`
