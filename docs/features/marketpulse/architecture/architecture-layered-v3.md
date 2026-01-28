# Market Pulse 分层架构设计 v3（最新版）

> 基于第一性原理：保持三层架构不变，但在 **Layer 2/3 中加入 Dual Agent / Dual Signal 能力**，同时继续避免不必要的复杂度（无 DynamoDB、无多数据源依赖）。

**设计原则**：参考同目录下的 `design-principles.md`。

---

## 核心价值（当前版本）

Market Pulse 现在聚焦四件事：

1. **采集**：实时市场数据 → S3 `raw-data/`
2. **计算**：Compute Agent 生成 10 只股票的基础信号 → `compute-signals.json`
3. **学习**：Learning Agent 基于 Compute 信号训练模型 → `learning-signals.json`
4. **展示**：前端展示当前 Pulse、事件列表，以及 **10 股 Dual Signal 对比表格**

---

## 三层架构总览

```text
┌──────────────────────────────────────┐
│ Layer 1: Data Collection             │
│ WebSocket → S3 (raw-data/)          │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│ Layer 2: Processing (Lambdas)        │
│ Compute Agent + Learning Agent       │
│ → 写入 processed-data/{date}/...     │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│ Layer 3: API + Frontend              │
│ FastAPI /api/v1/market-pulse/*      │
│ + HTML/JS Dual Signal Dashboard      │
└──────────────────────────────────────┘
```

---

## Layer 1: Data Collection（数据采集层）

### 职责

- 连接 Polygon WebSocket
- 接收原始 tick / 细粒度数据
- **按 5 分钟窗口聚合为 5m bars**（减少噪音 & S3 小文件数量）
- 将 5m bars 写入 S3 `raw-data/` 前缀

### 组件

- `MarketPulsePolygonService` – WebSocket 连接
- `MarketPulseDataCollector` – 数据收集和聚合
- `AWSStorageService` – 统一的 S3 读写工具

### 典型输出路径

```text
s3://tokimeki-market-pulse-prod/
  raw-data/...
```

具体文件组织由收集器实现控制（详见 `WEBSOCKET-DATA-FORMAT.md`），Layer 2 只依赖「按日期 / ticker 可读」这一抽象。

---

## Layer 2: Processing（处理层：Compute + Learning Agents）

### 总体职责

1. 读取 `raw-data/`，生成 **基础 Pulse 指标**  
2. 将当日 10 只核心股票的信号写入 S3  
3. 基于这些信号训练/更新 Learning 模型，输出预测 & 评估指标  
4. 所有结果都落在 **`processed-data/{YYYY-MM-DD}/`** 目录下

### 2.1 Compute Agent（计算 Agent）

- **触发方式**：Lambda（推荐 **每 5 分钟** 由 EventBridge 定时触发；也可按需/更慢频率触发）  
- **输入**：`raw-data/` under `tokimeki-market-pulse-prod`  
- **职责**：
  - 计算当前 Pulse 指标（stress / velocity / volume_surge / volatility / breadth）
  - 对 10 只核心股票生成「最新一条」因子信号
  - **将当次计算结果「追加」到当日信号时间序列中**，让一天内可以有多次学习样本
- **输出文件**（关键）：

```text
processed-data/{YYYY-MM-DD}/compute-signals.json
```

结构示意（**时间序列**，同一只股票会出现多条不同时间戳的记录）：

```json
{
  "date": "2026-01-28",
  "signals": [
    { "timestamp": "2026-01-28T12:00:00Z", "ticker": "AAPL", "signal": 0.12, "return": 0.0012, "vol": 0.01 },
    { "timestamp": "2026-01-28T12:05:00Z", "ticker": "AAPL", "signal": 0.15, "return": 0.0015, "vol": 0.01 },
    { "timestamp": "2026-01-28T12:10:00Z", "ticker": "MSFT", "signal": -0.05, "return": -0.0005, "vol": 0.009 },
    ...
  ],
  "tickers_processed": 10,
  "total_tickers": 10
}
```

实现要点（对应 `aws-lambda-compute-agent.py`）：

- 每次运行：
  - 从 S3 读取现有 `compute-signals.json`（如果存在），拿到已有 `signals[]`
  - 计算当前最新一条信号 `new_signals`（每只股票 0 或 1 条）
  - 按 `(ticker, timestamp)` 去重后 **append** 到 `signals[]`
  - 按 `(ticker, timestamp)` 排序并回写到同一个文件  
- 这样在一天之内，多次触发 Compute Agent 就会逐渐积累出 **长的 intra‑day 序列**，Learning Agent 可以在同一天内多次学习。

同时仍可以写入更细粒度的 `pulse-events` 数据，用于 `/current` 与 `/events/today` 等端点。

### 2.2 Learning Agent（学习 Agent）

- **触发方式**：Lambda，频率低于 Compute（推荐 **每 60 分钟** 触发一次）  
- **输入**：
  - `processed-data/{date}/compute-signals.json`
  - 历史学习结果（如需要）
- **职责**：
  - 针对 10 只股票训练或更新模型
  - 输出预测信号、R²、MAE、训练迭代次数、是否收敛
- **输出文件**（关键）：

```text
processed-data/{YYYY-MM-DD}/learning-signals.json
```

结构示意：

```json
{
  "models": {
    "AAPL": {
      "signal_predicted": 0.23,
      "r2_score": 0.91,
      "mae": 0.012,
      "training_iterations": 50,
      "converged": true
    },
    "MSFT": { "...": "..." }
  }
}
```

### 2.3 仍然遵守的“极简”原则

- 只依赖 **S3**（无 DynamoDB、无 RDS）
- 只处理有限的 10 只股票（列在 `DUAL-AGENT-SIGNAL-ARCHITECTURE.md` 中）
- Lambda 只负责「计算 + 写文件」，不直接对外暴露 HTTP

---

## Layer 3: API + Frontend（接口与展示层）

### 3.1 FastAPI 端点（当前实际存在）

端点定义在 `app/api/v1/endpoints/market_pulse.py` 中，主要包括：

- **基础 Pulse / 事件**
  - `GET /api/v1/market-pulse/current` – 当前 Pulse 指标（Compute Agent 即时计算）
  - `GET /api/v1/market-pulse/events/today` – 读取 S3 中当日事件列表
  - `GET /api/v1/market-pulse/available-tickers` – 返回今日有数据的股票列表

- **单 Agent 对比 & 性能**
  - `GET /api/v1/market-pulse/compare` – 单股票层面的 Compute vs Learning 对比
  - `GET /api/v1/market-pulse/compute-agent` – 只看 Compute Agent
  - `GET /api/v1/market-pulse/learning-agent` – 只看 Learning Agent
  - `GET /api/v1/market-pulse/performance` – 两个 Agent 的性能对比

- **Dual Signal Dashboard 专用**
  - `GET /api/v1/market-pulse/dual-signal`
    - 读取：
      - `processed-data/{today}/compute-signals.json`
      - `processed-data/{today}/learning-signals.json`
    - 聚合为 10 只股票的对比数组 `stocks[]`
    - 为前端 Dual Signal 表格提供数据

- **数据采集控制**
  - `POST /api/v1/market-pulse/collector/start`
  - `POST /api/v1/market-pulse/collector/stop`
  - `GET  /api/v1/market-pulse/collector/status`

> 旧版文档中「只保留 2 个端点」已经不符合现状——现在我们在 **不引入新存储层的前提下** 增加了必要的 API，以支持双 Agent Dashboard 和运维。

### 3.2 前端组件（Dual Signal Dashboard）

- 主要实现文件：
  - `static/index.html` – 包含 `Market Pulse - Dual Signal Comparison` 表格区域
  - `static/js/components/market-pulse.js` – `MarketPulseDashboard` 类
- 行为概要：
  - 初始化时调用 `GET /dual-signal`
  - 把 `stocks[]` 渲染到 Excel 风格表格中
  - 根据 `data_status` 显示 Learning Agent 尚未就绪的提示（不再阻塞显示）
  - 使用 `setInterval` 每 30 秒自动刷新一次

更详细的前端 + API 交互说明见 `../DUAL-AGENT-DASHBOARD.md`。

---

## S3 结构（当前版本）

```text
s3://tokimeki-market-pulse-prod/
├── raw-data/...
└── processed-data/
    └── {YYYY-MM-DD}/
        ├── compute-signals.json
        ├── learning-signals.json
        └── (可选) pulse-events-*.jsonl / metadata
```

- 不再依赖 `learning-results/` 等早期目录命名
- 仍然避免 `daily-summaries/`、`insights/` 等非核心目录

---

## 代码结构（当前核心模块）

```text
app/services/marketpulse/
├── polygon_service.py       # WebSocket 连接
├── data_collector.py        # 数据采集与聚合
├── aws_storage.py           # S3 访问封装（无 DynamoDB）
├── pulse_service.py         # Compute Agent 相关业务逻辑
└── learning_agent_service.py# Learning Agent 结果读取与增强

app/api/v1/endpoints/
└── market_pulse.py          # 所有 Market Pulse 相关 API 端点

docs/features/marketpulse/
├── aws-lambda-compute-agent.py   # Compute Lambda 实现（保持独立文档）
└── aws-lambda-learning-agent.py  # Learning Lambda 实现（保持独立文档）
```

> 与 v2 相比，最大的变化是：**删除 DynamoDB / Fallback / 历史查询等复杂度，但重新引入了“学习 + 双 Agent 对比”这一条主路径**，全部仍托管在 S3 之上。

---

## 环境变量（当前最小集合）

```bash
POLYGON_API_KEY=xxx
AWS_S3_PULSE_BUCKET=tokimeki-market-pulse-prod
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-2
```

- 仍然 **不需要**：
  - `AWS_DYNAMODB_PULSE_TABLE`
  - 其它数据库类环境变量

---

## 验证 Checklist（系统是否按最新架构工作）

- **Layer 1**
  - [ ] Data Collector 能稳定写入 `raw-data/`
- **Layer 2 – Compute Agent**
  - [ ] 当日存在 `processed-data/{today}/compute-signals.json`
  - [ ] 文件内包含 10 只股票的信号
- **Layer 2 – Learning Agent**
  - [ ] 当日存在 `processed-data/{today}/learning-signals.json`
  - [ ] 至少部分股票有 `signal_predicted` / `r2_score` / `mae`
- **Layer 3 – API**
  - [ ] `GET /api/v1/market-pulse/current` 正常返回
  - [ ] `GET /api/v1/market-pulse/events/today` 正常返回
  - [ ] `GET /api/v1/market-pulse/dual-signal` 返回 `success: true` 且 `stocks.length == 10`
- **Layer 3 – 前端**
  - [ ] Dual Signal 表格能显示 10 行股票数据
  - [ ] 在 Learning Agent 暂不可用时，仅出现黄色提示，而不是整表报错

---

## 相关文档

- `design-principles.md` – 第一性原理设计方法
- `../overview/market-pulse-quickstart.md` – 快速上手
- `../DUAL-AGENT-DASHBOARD.md` – Dual Signal Dashboard 前后端 + AWS 设计
- `../DUAL-AGENT-SIGNAL-ARCHITECTURE.md` – 计算公式 & 特征设计
