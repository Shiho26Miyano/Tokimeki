# Market Pulse 文档

Market Pulse 实时市场监控和分析系统。

## 📚 核心文档

### 🚀 快速开始
- **[快速启动](./market-pulse-quickstart.md)** - 5分钟快速上手

### 🏗️ 架构设计
- **[分层架构设计 v3](./architecture-layered-v3.md)** - 极简设计（推荐，基于第一性原理）⭐
- **[设计原则](./design-principles.md)** - 第一性原理设计方法
- **[实施总结](./IMPLEMENTATION-SUMMARY.md)** - v3 简化实施总结

### ☁️ AWS 部署
- **[AWS 资源清单](./aws-storage-what-to-create.md)** - 需要创建的 AWS 资源
- **[Lambda 部署指南](./lambda-deployment-guide.md)** - 部署 Lambda Agent 到 AWS
- **[Lambda Agents 说明](./LAMBDA-AGENTS-README.md)** - Compute & Learning Agent 文件说明 ⭐
- **[AWS 双 Agent 部署](./AWS-SETUP-DUAL-AGENT.md)** - 完整部署步骤
- **[Lambda Compute Agent 代码](./aws-lambda-compute-agent.py)** - Compute Agent 代码
- **[Lambda Learning Agent 代码](./aws-lambda-learning-agent.py)** - Learning Agent 代码

## 🎯 核心概念

### 极简架构（v3）

```
Layer 3: API + Frontend - 读取 processed-data/ → 展示
    ↓
Layer 2: Processing (Lambda) - 读取 raw-data/ → 计算指标 → 写入 processed-data/
    ↓
Layer 1: Data Collection - WebSocket → S3 (raw-data/)
```

**v3 版本关键简化**：
- ✅ **代码减少 38%**：删除所有不必要的功能
- ✅ **只保留核心**：2 个 API 端点，3 个核心组件
- ✅ **S3-only**：零数据库成本，零 DynamoDB 复杂度
- ✅ **极简 Lambda**：只计算指标，不学习不总结

### 各层职责（v3 简化）

**Layer 1: Data Collection**
- ✅ 采集原始数据 (WebSocket → S3)
- Tech: `websocket-client`, Polygon.io

**Layer 2: Processing (Lambda)**
- ✅ 计算 pulse 指标（5个）
- ❌ 删除：学习模式、每日总结
- Tech: AWS Lambda, EventBridge

**Layer 3: API + Frontend**
- ✅ 提供 REST API（2个端点）
- ✅ 读取 Agent 处理结果
- ✅ 数据可视化
- Tech: FastAPI, HTML/JS, Chart.js

### 为什么分层？

- 🎯 **职责清晰**: 每层职责单一，易于理解
- 🚀 **独立扩展**: 每层可以独立升级和扩展
- 💰 **成本优化**: Lambda 按需执行，不占用后端资源
- 🔧 **技术灵活**: 每层可以使用最适合的技术
- 🧠 **易于维护**: 问题定位到具体层

## 📖 阅读顺序

1. [快速启动](./market-pulse-quickstart.md) - 快速上手
2. [设计原则](./design-principles.md) - 理解第一性原理设计方法
3. [分层架构设计 v3](./architecture-layered-v3.md) - 极简架构（推荐）
4. [AWS 资源清单](./aws-storage-what-to-create.md) - 创建 AWS 资源
5. [Lambda 部署指南](./lambda-deployment-guide.md) - 部署处理层

## 🔗 相关资源

- API: `/api/v1/market-pulse/`
- 代码: `app/services/marketpulse/`
- 测试: `scripts/test_websocket_connection.py`

## 📁 文档结构

```
docs/features/marketpulse/
├── README.md                      # 文档索引（本文件）
├── design-principles.md            # 第一性原理设计原则
├── architecture-layered-v3.md     # 极简架构设计（推荐）
├── market-pulse-quickstart.md    # 快速启动指南
├── aws-storage-what-to-create.md # AWS 资源清单
├── lambda-deployment-guide.md     # Lambda 部署指南
├── LAMBDA-AGENTS-README.md        # Lambda Agents 文件说明
├── AWS-SETUP-DUAL-AGENT.md        # 双 Agent 完整部署步骤
├── aws-lambda-compute-agent.py     # Lambda Compute Agent 代码
└── aws-lambda-learning-agent.py   # Lambda Learning Agent 代码
```
