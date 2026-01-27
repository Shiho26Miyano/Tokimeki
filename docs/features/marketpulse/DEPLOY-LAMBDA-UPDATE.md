# 更新 Lambda 函数部署指南

## 🚀 快速部署

### 方法 1: 使用部署脚本（推荐）

```bash
cd /Volumes/D/2026_Project/Tokimeki

# 运行部署脚本
./scripts/deploy-lambda-functions.sh
```

脚本会自动：
1. ✅ 创建两个 Lambda 函数的 zip 部署包
2. ✅ 更新 Compute Agent Lambda 函数
3. ✅ 更新 Learning Agent Lambda 函数
4. ✅ 验证部署结果

---

## 📦 方法 2: 手动部署

### 步骤 1: 准备部署包

#### Compute Agent

```bash
cd /Volumes/D/2026_Project/Tokimeki

# 创建临时目录
mkdir -p /tmp/lambda-compute
cd /tmp/lambda-compute

# 复制并重命名文件
cp /Volumes/D/2026_Project/Tokimeki/docs/features/marketpulse/aws-lambda-compute-agent.py lambda_function.py

# 创建 zip 文件
zip lambda-compute-agent.zip lambda_function.py

# 移动到项目目录
mv lambda-compute-agent.zip /Volumes/D/2026_Project/Tokimeki/
```

#### Learning Agent

```bash
# 创建临时目录
mkdir -p /tmp/lambda-learning
cd /tmp/lambda-learning

# 复制并重命名文件
cp /Volumes/D/2026_Project/Tokimeki/docs/features/marketpulse/aws-lambda-learning-agent.py lambda_function.py

# 创建 zip 文件
zip lambda-learning-agent.zip lambda_function.py

# 移动到项目目录
mv lambda-learning-agent.zip /Volumes/D/2026_Project/Tokimeki/
```

### 步骤 2: 更新 Lambda 函数

#### 更新 Compute Agent

```bash
cd /Volumes/D/2026_Project/Tokimeki

aws lambda update-function-code \
    --function-name market-pulse-compute-agent \
    --zip-file fileb://lambda-compute-agent.zip \
    --region us-east-2
```

#### 更新 Learning Agent

```bash
aws lambda update-function-code \
    --function-name market-pulse-learning-agent \
    --zip-file fileb://lambda-learning-agent.zip \
    --region us-east-2
```

---

## ✅ 验证部署

### 检查函数版本

```bash
# Compute Agent
aws lambda get-function \
    --function-name market-pulse-compute-agent \
    --region us-east-2 \
    --query 'Configuration.Version' \
    --output text

# Learning Agent
aws lambda get-function \
    --function-name market-pulse-learning-agent \
    --region us-east-2 \
    --query 'Configuration.Version' \
    --output text
```

### 测试函数

```bash
# 测试 Compute Agent
aws lambda invoke \
    --function-name market-pulse-compute-agent \
    --payload '{"date": "2026-01-26"}' \
    --region us-east-2 \
    response-compute.json

cat response-compute.json

# 测试 Learning Agent
aws lambda invoke \
    --function-name market-pulse-learning-agent \
    --payload '{"date": "2026-01-26"}' \
    --region us-east-2 \
    response-learning.json

cat response-learning.json
```

### 查看日志

```bash
# Compute Agent 日志
aws logs tail /aws/lambda/market-pulse-compute-agent --follow --region us-east-2

# Learning Agent 日志
aws logs tail /aws/lambda/market-pulse-learning-agent --follow --region us-east-2
```

---

## 🔧 重要配置

### Lambda 函数配置

确保 Lambda 函数有以下配置：

**Compute Agent:**
- Runtime: Python 3.11
- Handler: `lambda_function.lambda_handler`
- Timeout: 900 秒 (15 分钟)
- Memory: 512 MB
- Environment Variable: `S3_BUCKET_NAME=your-bucket-name`

**Learning Agent:**
- Runtime: Python 3.11
- Handler: `lambda_function.lambda_handler`
- Timeout: 900 秒 (15 分钟)
- Memory: 1024 MB
- Environment Variable: `S3_BUCKET_NAME=your-bucket-name`

### 更新环境变量（如果需要）

```bash
# Compute Agent
aws lambda update-function-configuration \
    --function-name market-pulse-compute-agent \
    --environment Variables="{S3_BUCKET_NAME=your-bucket-name}" \
    --region us-east-2

# Learning Agent
aws lambda update-function-configuration \
    --function-name market-pulse-learning-agent \
    --environment Variables="{S3_BUCKET_NAME=your-bucket-name}" \
    --region us-east-2
```

---

## 📝 注意事项

1. **文件命名**: Lambda 函数需要 `lambda_function.py` 作为文件名，handler 为 `lambda_function.lambda_handler`
2. **依赖**: 如果代码需要额外依赖（如 scikit-learn），需要创建包含依赖的部署包
3. **区域**: 确保使用正确的 AWS 区域（默认 `us-east-2`）
4. **权限**: 确保 AWS CLI 有更新 Lambda 函数的权限

---

## 🐛 故障排查

### 问题 1: 函数不存在

如果函数不存在，需要先创建：

```bash
# 创建 Compute Agent
aws lambda create-function \
    --function-name market-pulse-compute-agent \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/market-pulse-lambda-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda-compute-agent.zip \
    --timeout 900 \
    --memory-size 512 \
    --region us-east-2 \
    --environment Variables="{S3_BUCKET_NAME=your-bucket-name}"
```

### 问题 2: 权限错误

确保 IAM 用户/角色有 `lambda:UpdateFunctionCode` 权限。

### 问题 3: 部署包太大

如果部署包超过 50MB，需要使用 S3 上传：

```bash
# 上传到 S3
aws s3 cp lambda-compute-agent.zip s3://your-deployment-bucket/

# 从 S3 更新
aws lambda update-function-code \
    --function-name market-pulse-compute-agent \
    --s3-bucket your-deployment-bucket \
    --s3-key lambda-compute-agent.zip \
    --region us-east-2
```

---

## ✅ 完成！

部署完成后，Lambda 函数会自动使用新代码。EventBridge 触发器会继续按计划运行：
- Compute Agent: 每 5 分钟
- Learning Agent: 每 1 小时
