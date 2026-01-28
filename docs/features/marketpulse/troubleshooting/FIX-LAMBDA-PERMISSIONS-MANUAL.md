# 手动修复 Lambda 调用权限指南

## 问题

`tokimeki-pulse-writer` 用户没有 `lambda:InvokeFunction` 权限，无法手动触发 Lambda 函数。

## 解决方案

### 方法 1: 使用 AWS Console（推荐）

#### 步骤 1: 创建 Lambda 调用策略

1. 登录 AWS Console（使用管理员账户）
2. 进入 **IAM** → **Policies** → **Create policy**
3. 选择 **JSON** 标签
4. 复制以下内容：

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

5. 点击 **Next**
6. 策略名称：`MarketPulseLambdaInvokePolicy`
7. 描述：`Allow invoke Market Pulse Lambda functions`
8. 点击 **Create policy**

#### 步骤 2: 附加策略到用户

1. 进入 **IAM** → **Users** → `tokimeki-pulse-writer`
2. 点击 **Add permissions** → **Attach policies directly**
3. 搜索并选择 `MarketPulseLambdaInvokePolicy`
4. 点击 **Add permissions**

#### 步骤 3: 验证

等待 10-30 秒后测试：

```bash
python scripts/trigger_lambda_agents.py --compute
```

应该能成功触发 Lambda 函数。

---

### 方法 2: 使用 AWS CLI（如果有管理员权限）

```bash
# 1. 创建策略文件
cat > /tmp/lambda-policy.json <<EOF
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

# 2. 创建策略（如果不存在）
aws iam create-policy \
    --policy-name MarketPulseLambdaInvokePolicy \
    --policy-document file:///tmp/lambda-policy.json \
    --description "Allow invoke Market Pulse Lambda functions" \
    --region us-east-2

# 3. 附加到用户
aws iam attach-user-policy \
    --user-name tokimeki-pulse-writer \
    --policy-arn arn:aws:iam::989513605244:policy/MarketPulseLambdaInvokePolicy \
    --region us-east-2

# 清理
rm /tmp/lambda-policy.json
```

如果策略已存在，更新它：

```bash
POLICY_ARN="arn:aws:iam::989513605244:policy/MarketPulseLambdaInvokePolicy"
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document file:///tmp/lambda-policy.json \
    --set-as-default \
    --region us-east-2
```

---

### 方法 3: 使用管理员账户运行脚本

如果你有另一个有管理员权限的 AWS profile：

```bash
# 使用管理员 profile
./scripts/fix_lambda_permissions.sh --profile your-admin-profile
```

---

## 完整的权限需求

为了让 `tokimeki-pulse-writer` 用户完全工作，需要两个策略：

1. **S3 访问权限** (`MarketPulseS3AccessPolicy`)
   - `s3:ListBucket`
   - `s3:GetObject`
   - `s3:PutObject`
   - `s3:DeleteObject`

2. **Lambda 调用权限** (`MarketPulseLambdaInvokePolicy`)
   - `lambda:InvokeFunction`

---

## 一次性修复所有权限

如果你有管理员权限，可以一次性创建两个策略：

### 在 AWS Console 中：

1. **创建 S3 策略**（参考 `FIX-S3-PERMISSIONS-MANUAL.md`）
2. **创建 Lambda 策略**（使用上面的 JSON）
3. **附加两个策略到用户**

### 使用脚本（如果有管理员权限）：

```bash
# 修复 S3 权限
./scripts/fix_s3_permissions.sh --profile admin

# 修复 Lambda 权限
./scripts/fix_lambda_permissions.sh --profile admin
```

---

## 验证所有权限

修复后，验证所有权限：

```bash
# 1. 测试 S3 访问
aws s3 ls s3://tokimeki-market-pulse-prod/

# 2. 测试 Lambda 调用
python scripts/trigger_lambda_agents.py --compute

# 3. 如果都成功，触发两个 agents
python scripts/trigger_lambda_agents.py
```

---

## 常见问题

### Q: 为什么需要 Lambda 调用权限？

A: 虽然 Lambda 函数可以自动触发（通过 EventBridge），但手动触发需要 `lambda:InvokeFunction` 权限。

### Q: 策略更新后多久生效？

A: 通常 10-30 秒，但有时可能需要几分钟。

### Q: 如何检查策略是否正确附加？

A: 在 AWS Console 中：
- IAM → Users → `tokimeki-pulse-writer` → Permissions
- 应该能看到两个策略：
  - `MarketPulseS3AccessPolicy`
  - `MarketPulseLambdaInvokePolicy`

---

## 下一步

修复所有权限后：

1. ✅ 修复 S3 权限
2. ✅ 修复 Lambda 权限
3. 触发 Compute Agent: `python scripts/trigger_lambda_agents.py --compute`
4. 触发 Learning Agent: `python scripts/trigger_lambda_agents.py --learning`
5. 刷新 Dashboard 查看数据
