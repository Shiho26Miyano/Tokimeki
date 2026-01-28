# 403 Forbidden 故障排查指南

## 当前状态

从日志可以看到：
```
INFO: Found credentials in environment variables.
WARNING: S3 bucket access forbidden (403) - IAM permissions issue
```

这说明：
- ✅ AWS 凭证已正确设置
- ✅ 能够连接到 AWS S3
- ❌ **仍然缺少 `s3:ListBucket` 权限**

## 最可能的原因

### ⚠️ 策略未附加到用户（90% 的情况）⭐ **你当前的情况！**

**如果 "Entities attached" 标签中找不到任何实体，这就是问题所在！**

策略已经创建并保存，但**还没有附加到任何用户**。

**解决方案：** 参考 `ATTACH-POLICY-TO-USER.md` 将策略附加到用户。

## 详细检查步骤

### 步骤 1: 确认策略已创建

1. 进入 **IAM** → **Policies**
2. 搜索 `MarketPulseS3AccessPolicy`
3. 确认策略存在
4. 点击策略名称，检查策略内容是否正确

### 步骤 2: 找到使用这些凭证的用户

1. 在 AWS Console 中，找到你的 Access Key 对应的用户：
   - 方法 A: IAM → Users → 逐个检查用户的 Access Keys
   - 方法 B: 如果你知道用户名，直接进入该用户

2. **重要：** 确认 `.env` 文件中的 `AWS_ACCESS_KEY_ID` 对应的用户

### 步骤 3: 检查策略是否已附加

1. 进入 **IAM** → **Users** → 选择你的用户
2. 点击 **Permissions** 标签
3. 在 **"Attached policies"** 部分查找 `MarketPulseS3AccessPolicy`

**如果策略不在列表中：**

1. 点击 **"Add permissions"** → **"Attach policies directly"**
2. 在搜索框中输入 `MarketPulseS3AccessPolicy`
3. 勾选策略
4. 点击 **"Add permissions"**

### 步骤 4: 等待权限生效

1. **等待 2-3 分钟**（IAM 权限需要时间生效）
2. **重启应用**：
   ```bash
   # 停止当前应用（Ctrl+C）
   python main.py
   ```

3. 检查日志，应该看到：
   ```
   INFO: AWS S3 client initialized for bucket: tokimeki-market-pulse-prod
   ```

## 如果仍然 403

### 检查清单

- [ ] 策略已创建并保存
- [ ] 策略已附加到**正确的用户**（使用这些凭证的用户）
- [ ] 等待了 2-3 分钟
- [ ] 重启了应用
- [ ] 检查了是否有 Deny 策略
- [ ] 检查了 Bucket Policy

### 尝试简化版本

如果以上都正确，尝试使用简化版本（移除 Condition）：

1. 编辑策略 `MarketPulseS3AccessPolicy`
2. 使用 `MarketPulseS3AccessPolicy-SIMPLE.json` 的内容
3. 保存并等待
4. 重启应用

### 验证凭证对应的用户

运行以下命令查看当前使用的用户：

```bash
aws sts get-caller-identity
```

然后确认这个用户已附加策略。

## 常见错误

### ❌ 错误 1: 策略附加到了错误的用户

**症状：** 策略已附加，但仍然 403

**原因：** 策略附加到了用户 A，但应用使用的是用户 B 的凭证

**解决：** 确认策略附加到**使用这些凭证的用户**

### ❌ 错误 2: 没有等待权限生效

**症状：** 附加策略后立即测试，仍然 403

**原因：** IAM 权限需要时间生效

**解决：** 等待 2-3 分钟后重启应用

### ❌ 错误 3: 策略版本不是默认版本

**症状：** 更新了策略但权限没有生效

**原因：** 新版本没有设置为默认版本

**解决：** 在保存策略时，确保勾选 "Set this new version as the default"

## 快速验证

运行检查脚本：

```bash
./scripts/check_policy_attachment.sh
```

## 需要帮助？

如果以上步骤都完成了但仍然 403，请提供：
1. 策略是否已附加到用户（截图）
2. 使用的 Access Key 对应的用户 ARN
3. 是否有其他 Deny 策略
