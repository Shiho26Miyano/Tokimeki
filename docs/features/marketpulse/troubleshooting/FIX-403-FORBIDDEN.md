# 修复 403 Forbidden 错误

## 问题诊断

从日志可以看到：
```
WARNING: S3 bucket access forbidden (403) - IAM permissions issue
INFO: Found credentials in environment variables.
```

这说明：
- ✅ AWS 凭证已正确设置
- ✅ 能够连接到 AWS S3
- ❌ **缺少 `s3:ListBucket` 权限或权限配置有问题**

## 快速诊断

运行诊断脚本：
```bash
python3 scripts/diagnose_403_error.py
```

这个脚本会：
- 检查当前 AWS 用户
- 测试 S3 访问权限
- 验证 IAM 策略配置
- 提供具体的修复建议

## 解决方案

### 步骤 1: 检查 IAM 策略

1. 登录 AWS Console
2. 进入 **IAM** → **Users** → 选择你的用户（例如 `tokimeki-pulse-writer`）
3. 点击 **Permissions** 标签
4. 检查是否有 `MarketPulseS3AccessPolicy` 或类似的策略

### 步骤 2: 验证策略内容

策略文件位置：
- **完整版本（带 Condition）**: `docs/features/marketpulse/MarketPulseS3AccessPolicy.json`
- **简化版本（无 Condition）**: `docs/features/marketpulse/MarketPulseS3AccessPolicy-SIMPLE.json`

**推荐使用完整版本（带 Condition，更安全）：**

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

**如果 403 错误持续，可以尝试简化版本（无 Condition）：**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::tokimeki-market-pulse-prod"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::tokimeki-market-pulse-prod/*"
      ]
    }
  ]
}
```

**重要：**
- `s3:ListBucket` 的 Resource 必须是 bucket ARN（**没有** `/*`）
- `s3:GetObject` 等的 Resource 必须是对象 ARN（**有** `/*`）

### 步骤 3: 检查 Condition 条件

如果你的策略有 `Condition` 条件，确保它不会阻止 `head_bucket` 操作：

```json
{
  "Effect": "Allow",
  "Action": ["s3:ListBucket"],
  "Resource": "arn:aws:s3:::tokimeki-market-pulse-prod",
  "Condition": {
    "StringLike": {
      "s3:prefix": [
        "",           // 空字符串很重要！允许列出根目录
        "raw-data/*",
        "processed-data/*",
        "pulse-events/*",
        "learning-results/*"
      ]
    }
  }
}
```

**注意：** `head_bucket` 操作需要能够访问根目录，所以 `s3:prefix` 中必须包含空字符串 `""`。

### 步骤 4: 如果策略不存在或错误

1. 进入 **IAM** → **Policies** → **Create policy**
2. 选择 **JSON** 标签
3. 复制上面的策略内容
4. 策略名称：`MarketPulseS3AccessPolicy`
5. 点击 **Create policy**

### 步骤 5: 附加策略到用户

1. 进入 **IAM** → **Users** → 选择你的用户
2. 点击 **Add permissions** → **Attach policies directly**
3. 搜索并选择 `MarketPulseS3AccessPolicy`
4. 点击 **Add permissions**

### 步骤 6: 等待权限生效

IAM 权限更改通常需要 **10-30 秒**，但有时可能需要 **1-5 分钟**。

### 步骤 7: 验证修复

重启应用后，检查日志应该看到：
```
INFO: AWS S3 client initialized for bucket: tokimeki-market-pulse-prod
```

而不是：
```
WARNING: S3 bucket access forbidden (403)
```

## 常见问题

### Q: 我已经添加了策略（策略内容看起来正确），为什么还是 403？

**A: 即使策略内容正确，也可能因为以下原因失败：**

1. **策略未正确附加到用户**
   - 检查 IAM → Users → 你的用户 → Permissions
   - 确认 `MarketPulseS3AccessPolicy` 在列表中
   - **重要：** 确保你检查的是**实际使用凭证的用户**，不是其他用户

2. **策略需要时间生效**
   - IAM 权限更改通常需要 **10-30 秒**
   - 但有时可能需要 **1-5 分钟**
   - **解决方案：** 等待几分钟后重启应用

3. **可能有其他策略在拒绝访问**
   - 检查是否有其他策略（如 `Deny` 策略）在阻止访问
   - IAM 策略评估顺序：显式 Deny > 显式 Allow > 默认 Deny

4. **Bucket Policy 可能阻止了访问**
   - 检查 S3 → Bucket → Permissions → Bucket policy
   - 如果有 Bucket Policy，确保它允许你的用户访问

5. **使用了错误的凭证**
   - 确认 `.env` 文件中的凭证对应的是策略附加的用户
   - 运行 `python3 scripts/diagnose_403_error.py` 查看实际使用的用户

6. **Condition 条件评估问题**
   - 即使 `s3:prefix` 包含空字符串，某些情况下 `head_bucket` 可能仍然失败
   - **临时解决方案：** 暂时移除 Condition 条件测试

### Q: 如何确认策略内容？

**A: 在 AWS Console 中：**

1. IAM → Policies → `MarketPulseS3AccessPolicy`
2. 点击策略名称
3. 点击 **JSON** 标签
4. 检查策略内容是否包含 `s3:ListBucket`

### Q: 我可以移除 Condition 条件吗？

**A: 可以，但为了安全，建议保留。**

如果移除 Condition，策略会变成：

```json
{
  "Effect": "Allow",
  "Action": ["s3:ListBucket"],
  "Resource": "arn:aws:s3:::tokimeki-market-pulse-prod"
}
```

这样更简单，但权限范围更广。

## 快速修复脚本

### 诊断脚本（推荐先运行）

```bash
python3 scripts/diagnose_403_error.py
```

这个脚本会详细检查：
- 当前使用的 AWS 用户
- S3 访问权限测试
- IAM 策略配置验证
- 具体的修复建议

### 修复脚本（需要管理员权限）

如果你有管理员权限，可以使用：

```bash
./scripts/fix_s3_permissions.sh
```

或者参考：`docs/features/marketpulse/FIX-S3-PERMISSIONS-MANUAL.md`

## 如果策略内容正确但仍然 403

如果你的策略内容完全正确（如你提供的策略），但仍然收到 403，按以下顺序检查：

1. **运行诊断脚本**
   ```bash
   python3 scripts/diagnose_403_error.py
   ```

2. **确认策略已附加到正确的用户**
   - 在 AWS Console 中检查
   - 确认用户 ARN 匹配诊断脚本输出的用户

3. **等待权限生效**
   - 等待 1-5 分钟
   - 重启应用

4. **检查是否有 Deny 策略**
   - IAM → Users → 你的用户 → Permissions
   - 检查是否有任何 Deny 策略

5. **检查 Bucket Policy**
   - S3 → Bucket → Permissions → Bucket policy
   - 如果有，确保它允许你的用户访问

6. **临时移除 Condition 条件**
   - 如果以上都正确，尝试暂时移除 `Condition` 部分
   - 如果移除后可以工作，说明 Condition 条件有问题
