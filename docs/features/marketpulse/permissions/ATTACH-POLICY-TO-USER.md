# 如何将 MarketPulseS3AccessPolicy 附加到用户

## 问题

"Entities attached" 标签中找不到任何实体，说明策略**还没有附加到任何用户**。

这就是为什么仍然收到 403 错误的原因！

## 解决方案：附加策略到用户

### 方法 1: 从策略页面附加（推荐）

1. **在策略详情页面：**
   - 点击 **"Entities attached"** 标签
   - 点击 **"Add"** 按钮（或 "Attach" 按钮）

2. **选择附加类型：**
   - 选择 **"Users"**（如果附加到用户）
   - 或 **"Roles"**（如果附加到角色）

3. **选择用户：**
   - 在用户列表中，找到你的用户（例如 `tokimeki-pulse-writer`）
   - 勾选用户
   - 点击 **"Attach"** 或 **"Add permissions"**

### 方法 2: 从用户页面附加（更直观）

1. **进入 IAM → Users**
   - 在 AWS Console 中，进入 **IAM** → **Users**

2. **找到你的用户**
   - 如果你知道用户名，直接搜索
   - 如果不知道，需要找到使用你的 Access Key 的用户
   - 查看 `.env` 文件中的 `AWS_ACCESS_KEY_ID`，找到对应的用户

3. **附加策略：**
   - 点击用户名
   - 点击 **"Permissions"** 标签
   - 点击 **"Add permissions"** 按钮
   - 选择 **"Attach policies directly"**
   - 在搜索框中输入 `MarketPulseS3AccessPolicy`
   - 勾选策略
   - 点击 **"Add permissions"**

4. **验证：**
   - 在用户的 Permissions 页面，应该能看到 `MarketPulseS3AccessPolicy` 在 "Attached policies" 列表中

## 如何找到使用这些凭证的用户？

如果你不知道 Access Key 对应的用户：

### 方法 1: 查看所有用户

1. IAM → Users
2. 逐个检查用户的 Access Keys
3. 找到匹配 `AWS_ACCESS_KEY_ID` 的用户

### 方法 2: 使用 AWS CLI（如果有权限）

```bash
# 查看当前使用的用户
aws sts get-caller-identity

# 这会返回用户 ARN，例如：
# arn:aws:iam::989513605244:user/tokimeki-pulse-writer
```

### 方法 3: 检查常见用户名

常见的用户名可能是：
- `tokimeki-pulse-writer`
- `market-pulse-user`
- 或其他相关的名称

## 完整步骤总结

1. ✅ **策略已创建**（你已完成）
2. ❌ **策略未附加到用户**（需要完成）
3. ⏳ **等待权限生效**（附加后等待 2-3 分钟）
4. 🔄 **重启应用**（等待后重启）

## 附加后的验证

附加策略后：

1. **在策略页面验证：**
   - IAM → Policies → `MarketPulseS3AccessPolicy`
   - 点击 **"Entities attached"** 标签
   - 应该能看到你的用户

2. **在用户页面验证：**
   - IAM → Users → 你的用户
   - 点击 **"Permissions"** 标签
   - 应该能看到 `MarketPulseS3AccessPolicy` 在列表中

3. **等待并重启应用：**
   - 等待 2-3 分钟
   - 重启应用
   - 检查日志，应该看到：
     ```
     INFO: AWS S3 client initialized for bucket: tokimeki-market-pulse-prod
     ```

## 如果仍然找不到用户

如果你无法确定哪个用户应该附加策略：

1. **检查 `.env` 文件中的 Access Key**
2. **在 AWS Console 中：**
   - IAM → Users
   - 查看每个用户的 Access Keys
   - 找到匹配的用户

3. **或者创建新用户：**
   - 如果找不到，可以创建一个新用户
   - 附加策略
   - 创建新的 Access Key
   - 更新 `.env` 文件

## 重要提示

**策略必须附加到使用这些凭证的用户！**

如果策略附加到了用户 A，但应用使用的是用户 B 的凭证，仍然会收到 403 错误。
