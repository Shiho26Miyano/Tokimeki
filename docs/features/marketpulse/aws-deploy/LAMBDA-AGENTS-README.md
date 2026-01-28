# Lambda Agents 文件说明

## 📁 文件位置

### Compute Agent (计算 Agent)
**位置**: `docs/features/marketpulse/aws-lambda-compute-agent.py`

**功能**:
- 每 5 分钟运行一次
- 读取原始市场数据 (raw-data/)
- 计算 5 个核心指标：Stress, Velocity, Volume Surge, Volatility, Regime
- 存储处理结果到 processed-data/

**部署到 AWS Lambda**:
- 函数名: `market-pulse-compute-agent`
- Handler: `lambda_handler`
- 触发: EventBridge 每 5 分钟

---

### Learning Agent (学习 Agent)
**位置**: `docs/features/marketpulse/aws-lambda-learning-agent.py`

**功能**:
- 每天运行一次（00:00 UTC）
- 读取过去 30 天的处理数据
- 学习基准 (baseline)、模式 (patterns)、训练预测模型
- 存储学习结果到 learning-results/

**部署到 AWS Lambda**:
- 函数名: `market-pulse-learning-agent`
- Handler: `lambda_handler`
- 触发: EventBridge 每天 00:00 UTC

---

## 🚀 部署步骤

### 1. Compute Agent 部署

```bash
# 复制文件
cp docs/features/marketpulse/aws-lambda-compute-agent.py lambda_compute_agent.py

# 创建部署包
zip lambda-compute-agent.zip lambda_compute_agent.py

# 部署到 AWS Lambda
aws lambda create-function \
    --function-name market-pulse-compute-agent \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/market-pulse-agent-role \
    --handler lambda_compute_agent.lambda_handler \
    --zip-file fileb://lambda-compute-agent.zip \
    --timeout 300 \
    --memory-size 256
```

### 2. Learning Agent 部署

```bash
# 复制文件
cp docs/features/marketpulse/aws-lambda-learning-agent.py lambda_learning_agent.py

# 创建部署包
zip lambda-learning-agent.zip lambda_learning_agent.py

# 部署到 AWS Lambda
aws lambda create-function \
    --function-name market-pulse-learning-agent \
    --runtime python3.11 \
    --role arn:aws:iam::ACCOUNT_ID:role/market-pulse-agent-role \
    --handler lambda_learning_agent.lambda_handler \
    --zip-file fileb://lambda-learning-agent.zip \
    --timeout 900 \
    --memory-size 1024
```

### 3. 配置 EventBridge 触发器

详细步骤请参考: [AWS-SETUP-DUAL-AGENT.md](./AWS-SETUP-DUAL-AGENT.md)

---

## 📝 文件命名说明

- **源代码文件**: `aws-lambda-compute-agent.py`, `aws-lambda-learning-agent.py`
  - 位置: `docs/features/marketpulse/`
  - 用途: 源代码，版本控制

- **部署文件**: `lambda_compute_agent.py`, `lambda_learning_agent.py`
  - 位置: 临时目录（部署时创建）
  - 用途: 部署到 AWS Lambda 时使用
  - 注意: 这些文件不应提交到 git

- **部署包**: `lambda-compute-agent.zip`, `lambda-learning-agent.zip`
  - 位置: 临时目录（部署时创建）
  - 用途: 上传到 AWS Lambda
  - 注意: 这些文件不应提交到 git

---

## 🔄 更新 Agent 代码

1. 修改源代码: `docs/features/marketpulse/aws-lambda-compute-agent.py`
2. 重新部署: 按照上面的部署步骤
3. 测试: 检查 CloudWatch Logs

---

## 📚 相关文档

- [AWS 部署指南](./AWS-SETUP-DUAL-AGENT.md) - 完整部署步骤
- [架构设计](./architecture-layered-v3.md) - 系统架构说明
- [成本优化](./COST-OPTIMIZATION.md) - Lambda 成本优化建议
