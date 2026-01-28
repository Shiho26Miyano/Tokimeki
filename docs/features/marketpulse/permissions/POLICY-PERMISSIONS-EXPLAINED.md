# MarketPulseS3AccessPolicy 权限说明

## 策略包含的权限

`MarketPulseS3AccessPolicy` **确实包含**所有必需的权限：

### Statement 1: ListBucket 权限

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:ListBucket"  ← 这里！
  ],
  "Resource": "arn:aws:s3:::tokimeki-market-pulse-prod",
  "Condition": {
    "StringLike": {
      "s3:prefix": ["", "raw-data/*", "processed-data/*", "pulse-events/*", "learning-results/*"]
    }
  }
}
```

**权限：** `s3:ListBucket` ✅

### Statement 2: 对象操作权限

```json
{
  "Effect": "Allow",
  "Action": [
    "s3:GetObject",    ← 这里！
    "s3:PutObject",    ← 这里！
    "s3:DeleteObject"
  ],
  "Resource": [
    "arn:aws:s3:::tokimeki-market-pulse-prod/raw-data/*",
    "arn:aws:s3:::tokimeki-market-pulse-prod/processed-data/*",
    "arn:aws:s3:::tokimeki-market-pulse-prod/pulse-events/*",
    "arn:aws:s3:::tokimeki-market-pulse-prod/learning-results/*"
  ]
}
```

**权限：** 
- `s3:GetObject` ✅
- `s3:PutObject` ✅
- `s3:DeleteObject` ✅

## 为什么在 AWS Console 中可能看不到？

在 AWS Console 的 "Review and save" 页面，权限可能显示为：
- **Access level:** Limited: List, Read, Write
- **Service:** S3

这是**正确的**！AWS Console 使用简化的显示方式：
- "List" = `s3:ListBucket`
- "Read" = `s3:GetObject`
- "Write" = `s3:PutObject`, `s3:DeleteObject`

## 如何确认策略包含这些权限？

### 方法 1: 查看 JSON 标签

在 AWS Console 中：
1. IAM → Policies → `MarketPulseS3AccessPolicy`
2. 点击策略名称
3. 点击 **"JSON"** 标签
4. 你应该能看到完整的 JSON，包含：
   - `"s3:ListBucket"` 在第一个 Statement
   - `"s3:GetObject"` 和 `"s3:PutObject"` 在第二个 Statement

### 方法 2: 查看 Permissions 标签

在策略详情页：
1. 点击 **"Permissions"** 标签
2. 展开 **"S3"** 服务
3. 你应该能看到：
   - ListBucket
   - GetObject
   - PutObject
   - DeleteObject

## 如果 AWS Console 中确实没有这些权限

如果 AWS Console 中显示的策略**确实不包含**这些权限，可能的原因：

1. **策略版本问题**
   - 检查是否使用了正确的策略版本
   - 确保 "Set this new version as the default" 已勾选

2. **策略内容被修改**
   - 在 JSON 标签中检查实际内容
   - 如果内容不对，使用 `MarketPulseS3AccessPolicy.json` 文件的内容更新

3. **查看错误的策略**
   - 确认查看的是 `MarketPulseS3AccessPolicy`
   - 不是其他策略

## 验证步骤

1. **在 AWS Console 中：**
   - IAM → Policies → `MarketPulseS3AccessPolicy`
   - 点击策略名称
   - 点击 **"JSON"** 标签
   - 复制 JSON 内容

2. **与文件对比：**
   - 打开 `docs/features/marketpulse/MarketPulseS3AccessPolicy.json`
   - 对比内容是否一致

3. **如果不一致：**
   - 点击 **"Edit"** → **"JSON"** 标签
   - 粘贴 `MarketPulseS3AccessPolicy.json` 的内容
   - 保存并设置为默认版本

## 总结

策略文件 `MarketPulseS3AccessPolicy.json` **确实包含**所有必需的权限：
- ✅ `s3:ListBucket`
- ✅ `s3:GetObject`
- ✅ `s3:PutObject`
- ✅ `s3:DeleteObject`

如果 AWS Console 中显示不同，请检查策略的 JSON 内容，确保与文件一致。
