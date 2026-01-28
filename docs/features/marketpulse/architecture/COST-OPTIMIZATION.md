# 成本优化指南 - 确保 < $20/月

## 💰 当前配置成本分析

### Lambda 成本（当前配置）

**计算 Agent**：
- 频率：每 5 分钟 = 每天 288 次
- 内存：512 MB
- 执行时间：假设平均 30 秒
- 成本计算：
  - 请求：288 次/天 × 30 天 = 8,640 次/月 × $0.0000002 = **$0.0017/月**
  - 计算：8,640 次 × 0.5 GB × 0.5 分钟 = 2,160 GB-秒/月 × $0.0000166667 = **$0.036/月**
  - **小计：$0.0377/月**

**学习 Agent**：
- 频率：每天 1 次 = 30 次/月
- 内存：1024 MB
- 执行时间：假设平均 5 分钟（300 秒）
- 成本计算：
  - 请求：30 次/月 × $0.0000002 = **$0.000006/月**
  - 计算：30 次 × 1 GB × 5 分钟 = 150 GB-分钟/月 × $0.0000166667 = **$0.0025/月**
  - **小计：$0.0025/月**

**Lambda 总计：~$0.04/月**

### S3 成本

**存储成本**：
- 假设数据量：10 GB（原始 + 处理后 + 学习结果）
- 成本：10 GB × $0.023/GB = **$0.23/月**

**请求成本**：
- PUT 请求：~10,000 次/月 × $0.000005 = **$0.05/月**
- GET 请求：~50,000 次/月 × $0.0000004 = **$0.02/月**
- **小计：$0.07/月**

**S3 总计：~$0.30/月**

### EventBridge 成本

- 规则：2 个规则 × $0 = **$0/月**（免费）
- 自定义事件：0 = **$0/月**

### CloudWatch Logs 成本

- 日志存储：假设 1 GB/月 × $0.50/GB = **$0.50/月**
- 日志摄取：免费（前 5 GB/月）

### **总成本估算：~$0.84/月** ✅ 远低于 $20！

---

## 🎯 成本优化策略

### 1. 优化 Lambda 内存配置

**当前配置**：
- 计算 Agent：512 MB
- 学习 Agent：1024 MB

**优化建议**：
- 计算 Agent：降低到 **256 MB**（如果执行时间 < 60 秒）
- 学习 Agent：保持 **1024 MB**（需要处理大量数据）

**节省**：约 50% Lambda 计算成本 = **节省 ~$0.02/月**

### 2. 优化 Lambda 执行时间

**优化代码**：
- 使用并行处理
- 减少 S3 读取次数
- 使用缓存

**节省**：减少执行时间 = **节省 ~$0.01/月**

### 3. S3 生命周期策略（重要！）

**设置自动删除旧数据**：

```json
{
  "Rules": [
    {
      "Id": "DeleteOldRawData",
      "Status": "Enabled",
      "Prefix": "raw-data/",
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "DeleteOldProcessedData",
      "Status": "Enabled",
      "Prefix": "processed-data/",
      "Expiration": {
        "Days": 90
      }
    },
    {
      "Id": "TransitionToGlacier",
      "Status": "Enabled",
      "Prefix": "processed-data/",
      "Transitions": [
        {
          "Days": 30,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

**节省**：减少存储成本 = **节省 ~$0.10/月**

### 4. 减少计算 Agent 频率（可选）

**如果不需要每 5 分钟更新**：
- 改为每 15 分钟 = 每天 96 次
- 或改为每 30 分钟 = 每天 48 次

**节省**：
- 每 15 分钟：节省 67% = **节省 ~$0.025/月**
- 每 30 分钟：节省 83% = **节省 ~$0.031/月**

### 5. CloudWatch Logs 保留策略

**设置日志保留期**：
- 默认：永久保留（贵！）
- 建议：保留 7 天

**节省**：减少日志存储 = **节省 ~$0.40/月**

---

## 📊 优化后的成本估算

### 优化配置

| 项目 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| Lambda 计算 | $0.04 | $0.02 | $0.02 |
| S3 存储 | $0.23 | $0.15 | $0.08 |
| S3 请求 | $0.07 | $0.05 | $0.02 |
| CloudWatch Logs | $0.50 | $0.10 | $0.40 |
| **总计** | **$0.84** | **$0.32** | **$0.52** |

### **优化后总成本：~$0.32/月** ✅ 远低于 $20！

---

## 🔧 实施优化步骤

### Step 1: 优化 Lambda 内存

在 AWS Console 中：
1. Lambda → `market-pulse-compute-agent` → Configuration → General configuration
2. 编辑 Memory：512 MB → **256 MB**
3. 保存并测试

### Step 2: 设置 S3 生命周期策略

```bash
# 创建生命周期策略文件
cat > s3-lifecycle.json << 'EOF'
{
  "Rules": [
    {
      "Id": "DeleteOldRawData",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "raw-data/"
      },
      "Expiration": {
        "Days": 30
      }
    },
    {
      "Id": "DeleteOldProcessedData",
      "Status": "Enabled",
      "Filter": {
        "Prefix": "processed-data/"
      },
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
EOF

# 应用生命周期策略
aws s3api put-bucket-lifecycle-configuration \
    --bucket tokimeki-market-pulse-prod \
    --lifecycle-configuration file://s3-lifecycle.json \
    --region us-east-2
```

### Step 3: 设置 CloudWatch Logs 保留期

```bash
# 设置计算 Agent 日志保留 7 天
aws logs put-retention-policy \
    --log-group-name /aws/lambda/market-pulse-compute-agent \
    --retention-in-days 7 \
    --region us-east-2

# 设置学习 Agent 日志保留 7 天
aws logs put-retention-policy \
    --log-group-name /aws/lambda/market-pulse-learning-agent \
    --retention-in-days 7 \
    --region us-east-2
```

### Step 4: 设置成本告警

在 AWS Console 中：
1. 进入 CloudWatch → Billing → Alarms
2. 创建告警：
   - Metric: `EstimatedCharges`
   - Threshold: `$15`（当接近 $20 时提醒）
   - 通知：发送到你的邮箱

---

## 📈 成本监控

### 查看当前成本

```bash
# 查看 Lambda 成本（需要 Cost Explorer 权限）
# 或在 AWS Console: Billing → Cost Explorer
```

### 设置预算告警

在 AWS Console：
1. Billing → Budgets → Create budget
2. 选择 "Cost budget"
3. 设置：
   - Budget amount: `$20`
   - Alert threshold: `80%` ($16)
   - Alert threshold: `100%` ($20)

---

## 🎯 最终优化配置

### Lambda 配置

**计算 Agent**：
- Memory: **256 MB**（优化后）
- Timeout: 900 秒
- 频率: 每 5 分钟（或根据需要调整）

**学习 Agent**：
- Memory: **1024 MB**（保持）
- Timeout: 900 秒
- 频率: 每天 1 次

### S3 配置

- 生命周期策略：自动删除 30 天前的 raw-data
- 生命周期策略：自动删除 90 天前的 processed-data

### CloudWatch Logs 配置

- 保留期：7 天（不是永久）

---

## ✅ 成本检查清单

- [ ] Lambda 内存已优化（计算 Agent 256 MB）
- [ ] S3 生命周期策略已设置
- [ ] CloudWatch Logs 保留期已设置（7 天）
- [ ] 成本告警已设置（$15 和 $20）
- [ ] 预算已设置（$20/月）

---

## 💡 额外节省建议

### 如果成本仍然过高

1. **减少计算 Agent 频率**：每 5 分钟 → 每 15 分钟
2. **减少数据保留期**：30 天 → 14 天
3. **使用 S3 Intelligent-Tiering**：自动优化存储成本
4. **压缩数据**：使用 gzip 压缩（已在代码中实现）

---

## 📊 预期成本（优化后）

| 项目 | 月成本 |
|------|--------|
| Lambda | $0.02 |
| S3 存储 | $0.15 |
| S3 请求 | $0.05 |
| CloudWatch Logs | $0.10 |
| EventBridge | $0.00 |
| **总计** | **~$0.32/月** |

**远低于 $20/月预算！** ✅
