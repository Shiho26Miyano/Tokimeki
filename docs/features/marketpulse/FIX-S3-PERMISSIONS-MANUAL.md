# 手动修复 S3 权限指南

## 问题

`tokimeki-pulse-writer` 用户没有 IAM 管理权限，无法通过脚本自动创建/更新策略。

## 解决方案

### 方法 1: 使用 AWS Console（推荐，最简单）

#### 步骤 1: 登录 AWS Console

1. 登录 AWS Console（使用有管理员权限的账户）
2. 进入 **IAM** 服务

#### 步骤 2: 创建或更新策略

**如果策略不存在：**

1. 进入 **IAM** → **Policies** → **Create policy**
2. 选择 **JSON** 标签
3. 复制以下内容（已包含根目录权限）：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::tokimeki-market-pulse-prod",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "",
            "raw-data/*",
            "processed-data/*",
            "pulse-events/*",
            "learning-results/*"
          ]
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::tokimeki-market-pulse-prod/raw-data/*",
        "arn:aws:s3:::tokimeki-market-pulse-prod/processed-data/*",
        "arn:aws:s3:::tokimeki-market-pulse-prod/pulse-events/*",
        "arn:aws:s3:::tokimeki-market-pulse-prod/learning-results/*"
      ]
    }
  ]
}
```

4. 点击 **Next**
5. 策略名称：`MarketPulseS3AccessPolicy`
6. 描述：`Allow S3 access for Market Pulse bucket`
7. 点击 **Create policy**

**如果策略已存在：**

1. 进入 **IAM** → **Policies**
2. 搜索 `MarketPulseS3AccessPolicy`
3. 点击策略名称进入详情页
4. 点击 **Edit policy** → **JSON** 标签
5. 替换为上面的 JSON 内容
6. 点击 **Next** → **Save changes**

#### 步骤 3: 附加策略到用户

1. 进入 **IAM** → **Users** → `tokimeki-pulse-writer`
2. 点击 **Add permissions** → **Attach policies directly**
3. 搜索并选择 `MarketPulseS3AccessPolicy`
4. 点击 **Add permissions**

#### 步骤 4: 验证

等待 10-30 秒后，使用 `tokimeki-pulse-writer` 的凭证测试：

```bash
aws s3 ls s3://tokimeki-market-pulse-prod/
```

应该能看到 bucket 内容。

---

### 方法 2: 使用管理员账户运行脚本

如果你有另一个有管理员权限的 AWS 账户或 profile：

```bash
# 使用管理员 profile
./scripts/fix_s3_permissions.sh --profile admin

# 或使用管理员账户的环境变量
export AWS_ACCESS_KEY_ID=admin-access-key
export AWS_SECRET_ACCESS_KEY=admin-secret-key
./scripts/fix_s3_permissions.sh
```

---

### 方法 3: 使用 AWS CLI（如果有管理员权限）

```bash
# 1. 创建策略（如果不存在）
aws iam create-policy \
    --policy-name MarketPulseS3AccessPolicy \
    --policy-document file://docs/features/marketpulse/S3-IAM-POLICY.json \
    --description "Allow S3 access for Market Pulse bucket"

# 2. 附加到用户
aws iam attach-user-policy \
    --user-name tokimeki-pulse-writer \
    --policy-arn arn:aws:iam::989513605244:policy/MarketPulseS3AccessPolicy

# 3. 如果策略已存在，更新它
POLICY_ARN="arn:aws:iam::989513605244:policy/MarketPulseS3AccessPolicy"
aws iam create-policy-version \
    --policy-arn "$POLICY_ARN" \
    --policy-document file://docs/features/marketpulse/S3-IAM-POLICY.json \
    --set-as-default
```

---

## 策略文件位置

更新后的策略文件已保存在：
- `docs/features/marketpulse/S3-IAM-POLICY.json`

这个文件已经包含了根目录权限（空字符串 `""` 在前缀列表中）。

---

## 验证步骤

修复后，验证权限：

```bash
# 1. 列出 bucket 根目录
aws s3 ls s3://tokimeki-market-pulse-prod/

# 2. 列出子目录
aws s3 ls s3://tokimeki-market-pulse-prod/raw-data/

# 3. 测试写入（可选）
echo "test" | aws s3 cp - s3://tokimeki-market-pulse-prod/test.txt
aws s3 rm s3://tokimeki-market-pulse-prod/test.txt
```

---

## 常见问题

### Q: 为什么需要管理员权限？

A: IAM 策略的创建和修改是敏感操作，需要 IAM 管理权限。普通用户只能使用已附加的策略，不能创建新策略。

### Q: 策略更新后多久生效？

A: 通常 10-30 秒，但有时可能需要几分钟。

### Q: 如何检查策略是否正确附加？

A: 在 AWS Console 中：
- IAM → Users → `tokimeki-pulse-writer` → Permissions
- 应该能看到 `MarketPulseS3AccessPolicy` 在列表中

---

## 下一步

修复 S3 权限后：

1. 触发 Compute Agent: `python scripts/trigger_lambda_agents.py --compute`
2. 触发 Learning Agent: `python scripts/trigger_lambda_agents.py --learning`
3. 刷新 Dashboard 查看数据
