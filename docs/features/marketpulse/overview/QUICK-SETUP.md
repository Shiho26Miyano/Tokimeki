# Market Pulse 快速设置指南

## 问题诊断

如果看到错误："⚠️ Check AWS credentials and S3 permissions"，请按以下步骤检查：

## 步骤 1: 设置环境变量

### 方法 A: 在终端中设置（临时）

```bash
export AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod
export AWS_ACCESS_KEY_ID=your-access-key-id
export AWS_SECRET_ACCESS_KEY=your-secret-access-key
export AWS_REGION=us-east-2
```

### 方法 B: 创建 .env 文件（推荐）

在项目根目录创建 `.env` 文件：

```bash
# .env
AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-2
POLYGON_API_KEY=your-polygon-api-key
```

然后在启动应用前加载：

```bash
# 如果使用 python-dotenv
source .env  # 或使用 export $(cat .env | xargs)
python main.py
```

### 方法 C: 在 Railway/部署环境中设置

在 Railway Dashboard 或部署平台的环境变量设置中添加：
- `AWS_S3_PULSE_BUCKET`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## 步骤 2: 验证配置

运行诊断脚本：

```bash
python3 scripts/diagnose_data_collection.py
```

或快速测试：

```bash
python3 -c "
import os
print('Bucket:', os.getenv('AWS_S3_PULSE_BUCKET'))
print('Access Key:', '✅ Set' if os.getenv('AWS_ACCESS_KEY_ID') else '❌ Not set')
print('Secret Key:', '✅ Set' if os.getenv('AWS_SECRET_ACCESS_KEY') else '❌ Not set')
"
```

## 步骤 3: 验证 S3 权限

如果环境变量已设置但仍然报错，检查 S3 权限：

```bash
# 测试 S3 访问
aws s3 ls s3://tokimeki-market-pulse-prod/
```

如果返回 403 Forbidden，需要添加 S3 权限。参考：
- `docs/features/marketpulse/FIX-S3-PERMISSIONS-MANUAL.md`

## 步骤 4: 启动应用

设置环境变量后，重新启动应用：

```bash
python main.py
```

## 常见问题

### Q: 如何获取 AWS 凭证？

A: 
1. 登录 AWS Console
2. 进入 IAM → Users → 选择你的用户
3. 点击 "Security credentials" 标签
4. 创建新的 Access Key

### Q: 如何找到 S3 bucket 名称？

A: 
1. 登录 AWS Console
2. 进入 S3 服务
3. 查看 bucket 列表
4. 默认名称：`tokimeki-market-pulse-prod`

### Q: 环境变量设置后仍然报错？

A: 
1. 确认应用已重启（环境变量只在启动时读取）
2. 检查凭证是否正确
3. 检查 S3 权限是否已添加
4. 运行诊断脚本查看详细错误

## 快速检查清单

- [ ] `AWS_S3_PULSE_BUCKET` 已设置
- [ ] `AWS_ACCESS_KEY_ID` 已设置
- [ ] `AWS_SECRET_ACCESS_KEY` 已设置
- [ ] `AWS_REGION` 已设置（默认: us-east-2）
- [ ] S3 权限已配置（参考 FIX-S3-PERMISSIONS-MANUAL.md）
- [ ] 应用已重启
