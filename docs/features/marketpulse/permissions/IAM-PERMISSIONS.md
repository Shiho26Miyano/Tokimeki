# IAM 权限配置指南

## 问题

如果遇到以下错误：
```
AccessDeniedException: User is not authorized to perform: lambda:InvokeFunction
```

说明 IAM 用户/角色缺少必要的 Lambda 权限。

## 解决方案

### 方法 1: 使用 AWS Console 添加权限

1. 登录 AWS Console
2. 进入 **IAM** → **Users** → 选择 `tokimeki-pulse-writer`
3. 点击 **Add permissions** → **Attach policies directly**
4. 搜索并添加以下策略之一：
   - **AWSLambdaFullAccess** (完整权限，推荐用于开发)
   - 或创建自定义策略（见下方）

### 方法 2: 创建自定义 IAM 策略（推荐用于生产）

创建最小权限策略，只允许调用特定的 Lambda 函数：

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-compute-agent",
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-learning-agent"
            ]
        }
    ]
}
```

**步骤：**
1. 进入 **IAM** → **Policies** → **Create policy**
2. 选择 **JSON** 标签
3. 粘贴上面的 JSON（替换 Account ID 和函数名）
4. 命名策略（如：`MarketPulseLambdaInvokePolicy`）
5. 创建策略
6. 将策略附加到用户 `tokimeki-pulse-writer`

### 方法 3: 使用 AWS CLI 添加权限

```bash
# 创建策略文件
cat > lambda-invoke-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-compute-agent",
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-learning-agent"
            ]
        }
    ]
}
EOF

# 创建策略
aws iam create-policy \
    --policy-name MarketPulseLambdaInvokePolicy \
    --policy-document file://lambda-invoke-policy.json \
    --region us-east-2

# 附加策略到用户（需要管理员权限）
aws iam attach-user-policy \
    --user-name tokimeki-pulse-writer \
    --policy-arn arn:aws:iam::989513605244:policy/MarketPulseLambdaInvokePolicy \
    --region us-east-2
```

## 所需权限总结

### 手动触发 Lambda 函数需要：

| 权限 | 说明 | 必需 |
|------|------|------|
| `lambda:InvokeFunction` | 调用 Lambda 函数 | ✅ 必需 |
| `lambda:GetFunction` | 检查函数是否存在（可选） | ❌ 可选 |

### 完整功能所需权限：

| 服务 | 权限 | 说明 |
|------|------|------|
| **S3** | `s3:GetObject`<br>`s3:PutObject`<br>`s3:ListBucket` | 读取/写入 S3 数据 |
| **Lambda** | `lambda:InvokeFunction` | 手动触发 Lambda 函数 |
| **CloudWatch Logs** | `logs:DescribeLogGroups`<br>`logs:DescribeLogStreams`<br>`logs:GetLogEvents` | 查看 Lambda 日志（可选） |

## 验证权限

添加权限后，验证是否生效：

```bash
# 测试调用 Compute Agent
aws lambda invoke \
    --function-name market-pulse-compute-agent \
    --payload '{"date": "2026-01-27"}' \
    --region us-east-2 \
    response.json

# 查看响应
cat response.json
```

## 注意事项

1. **最小权限原则**: 生产环境建议使用自定义策略，只授予必要的权限
2. **资源限制**: 可以限制只能调用特定的 Lambda 函数（使用 Resource ARN）
3. **权限生效时间**: IAM 权限更改可能需要几分钟才能生效

## 修改现有策略

如果你已经创建了策略，需要修改它：

### 方法 1: 使用 AWS Console

1. 进入 **IAM** → **Policies**
2. 搜索你的策略名称（如 `MarketPulseLambdaInvokePolicy`）
3. 点击策略名称进入详情页
4. 点击 **Edit policy** 按钮
5. 选择 **JSON** 标签
6. 修改 JSON 内容（见下方示例）
7. 点击 **Next** → **Save changes**

### 方法 2: 使用 AWS CLI 创建新版本

IAM 策略使用版本控制，需要创建新版本：

```bash
# 1. 创建新的策略文档文件
cat > lambda-invoke-policy-updated.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-compute-agent",
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-learning-agent"
            ]
        }
    ]
}
EOF

# 2. 获取策略 ARN（替换为你的策略名称）
POLICY_NAME="MarketPulseLambdaInvokePolicy"
ACCOUNT_ID="989513605244"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# 3. 创建新版本
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document file://lambda-invoke-policy-updated.json \
    --set-as-default

# 4. （可选）删除旧版本（保留最新5个版本）
# 先列出所有版本
aws iam list-policy-versions --policy-arn "$POLICY_ARN"

# 删除旧版本（替换 VERSION_ID）
# aws iam delete-policy-version \
#     --policy-arn "$POLICY_ARN" \
#     --version-id "v1"
```

### 方法 3: 查看当前策略内容

在修改前，先查看当前策略内容：

```bash
# 获取策略 ARN
POLICY_NAME="MarketPulseLambdaInvokePolicy"
ACCOUNT_ID="989513605244"
POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

# 获取默认版本 ID
DEFAULT_VERSION=$(aws iam get-policy \
    --policy-arn "$POLICY_ARN" \
    --query 'Policy.DefaultVersionId' \
    --output text)

# 查看策略内容
aws iam get-policy-version \
    --policy-arn "$POLICY_ARN" \
    --version-id "$DEFAULT_VERSION" \
    --query 'PolicyVersion.Document' \
    --output json | python3 -m json.tool
```

### 策略示例（包含 Lambda 调用权限）

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-compute-agent",
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-learning-agent"
            ]
        }
    ]
}
```

### 如果需要同时包含 S3 权限

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-compute-agent",
                "arn:aws:lambda:us-east-2:989513605244:function:market-pulse-learning-agent"
            ]
        },
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
        }
    ]
}
```

## 故障排查

如果添加权限后仍然失败：

1. **检查策略是否正确附加**:
   ```bash
   aws iam list-attached-user-policies --user-name tokimeki-pulse-writer
   ```

2. **检查策略内容**:
   ```bash
   POLICY_ARN="arn:aws:iam::989513605244:policy/你的策略名称"
   DEFAULT_VERSION=$(aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId' --output text)
   aws iam get-policy-version --policy-arn "$POLICY_ARN" --version-id "$DEFAULT_VERSION"
   ```

3. **等待权限生效**: IAM 权限更改可能需要 1-5 分钟才能生效

4. **检查 Lambda 函数名称和区域**: 确保函数名和区域正确

5. **验证策略版本**: 确保新版本已设置为默认版本
   ```bash
   aws iam get-policy --policy-arn "$POLICY_ARN" --query 'Policy.DefaultVersionId'
   ```
