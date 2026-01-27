# S3 策略类型说明

## 两种策略类型

### 1. IAM Policy（IAM 用户策略）- 推荐 ✅

**文件**: `S3-IAM-POLICY.json`

**特点**:
- ❌ **不需要** Principal 字段
- 附加到 IAM 用户/角色
- 通过 IAM 服务管理
- 更灵活，可以附加到多个用户

**使用方法**:
```bash
# 创建 IAM 策略
aws iam create-policy \
    --policy-name MarketPulseS3AccessPolicy \
    --policy-document file://docs/features/marketpulse/S3-IAM-POLICY.json

# 附加到用户
aws iam attach-user-policy \
    --user-name tokimeki-pulse-writer \
    --policy-arn arn:aws:iam::989513605244:policy/MarketPulseS3AccessPolicy
```

**或使用脚本**:
```bash
./scripts/fix_s3_permissions.sh
```

---

### 2. Bucket Policy（存储桶策略）

**文件**: `S3-BUCKET-POLICY.json`

**特点**:
- ✅ **需要** Principal 字段（指定允许访问的用户/角色）
- 直接附加到 S3 bucket
- 在 S3 Console 中管理
- 适合跨账户访问或公开访问场景

**使用方法**:
```bash
# 直接附加到 bucket
aws s3api put-bucket-policy \
    --bucket tokimeki-market-pulse-prod \
    --policy file://docs/features/marketpulse/S3-BUCKET-POLICY.json
```

**或通过 AWS Console**:
1. S3 → 选择 bucket → Permissions → Bucket policy
2. 粘贴 `S3-BUCKET-POLICY.json` 的内容
3. 保存

---

## 选择哪个？

### 推荐：IAM Policy ✅

**原因**:
- 更符合 AWS 最佳实践
- 权限管理更集中（在 IAM 中）
- 可以轻松附加到多个用户/角色
- 不需要 Principal 字段

### 使用 Bucket Policy 的场景

- 需要跨账户访问
- 需要公开访问（不推荐）
- 需要基于 IP 地址限制
- 需要基于时间限制

---

## 如果 AWS Console 提示 "missing principal"

如果你在 AWS Console 中创建策略时看到 "missing principal" 错误：

1. **确认你在创建什么**:
   - IAM → Policies → Create policy → **IAM Policy**（不需要 Principal）✅
   - S3 → Bucket → Permissions → Bucket policy → **Bucket Policy**（需要 Principal）✅

2. **如果创建 IAM Policy 但提示需要 Principal**:
   - 检查是否误选了 "Bucket policy" 选项
   - 确保在 IAM 服务中创建，而不是 S3 服务

3. **如果确实需要 Bucket Policy**:
   - 使用 `S3-BUCKET-POLICY.json` 文件
   - 确保 Principal 中的 ARN 正确（替换账户 ID 和用户名）

---

## 验证策略

### 验证 IAM Policy
```bash
# 查看用户附加的策略
aws iam list-attached-user-policies --user-name tokimeki-pulse-writer

# 查看策略内容
aws iam get-policy --policy-arn arn:aws:iam::989513605244:policy/MarketPulseS3AccessPolicy
```

### 验证 Bucket Policy
```bash
# 查看 bucket 策略
aws s3api get-bucket-policy --bucket tokimeki-market-pulse-prod
```

---

## 同时使用两种策略？

**可以，但不推荐**。两种策略会合并生效，可能导致权限混乱。

**建议**: 只使用一种方式：
- 推荐：IAM Policy（附加到用户）
- 或：Bucket Policy（附加到 bucket）

不要同时使用两种！
